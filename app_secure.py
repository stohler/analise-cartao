#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação principal com autenticação integrada
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
import os
import json
from datetime import datetime, timedelta
import tempfile
import pandas as pd
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Importar componentes locais
from pdf_analyzer import PDFAnalyzer
from data_handler import DataHandler
from models import UserManager, User
from auth import auth_bp, get_user_manager

# Importar MongoDB de forma condicional
try:
    from mongodb_handler import MongoDBHandler
    from monthly_comparison import MonthlyComparison
    MONGODB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MongoDB não disponível: {e}")
    MONGODB_AVAILABLE = False
    MongoDBHandler = None
    MonthlyComparison = None

# Carregar variáveis de ambiente
load_dotenv()

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações de segurança
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Configurações de sessão para produção
    is_production = os.environ.get('FLASK_ENV') == 'production'
    # Usar HTTPS se configurado no .env, senão usar HTTP
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_DOMAIN'] = os.environ.get('SESSION_COOKIE_DOMAIN') or None
    
    # Configurações da aplicação
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['REGISTRATION_ENABLED'] = os.environ.get('REGISTRATION_ENABLED', 'true').lower() == 'true'
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicializar extensões
    csrf = CSRFProtect(app)
    
    # Configurações adicionais do CSRF para produção
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Configurar user loader
    user_manager = get_user_manager()
    
    # Conectar ao MongoDB para usuários
    if not user_manager.connect():
        print("❌ Falha na conexão com MongoDB para usuários")
    
    @login_manager.user_loader
    def load_user(user_id):
        return user_manager.get_user_by_id(user_id)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    
    # Inicializar componentes
    analyzer = PDFAnalyzer()
    data_handler = DataHandler()
    
    # Inicializar MongoDB se disponível
    mongo_handler = None
    comparator = None
    mongo_connected = False
    
    if MONGODB_AVAILABLE:
        try:
            mongo_uri = os.environ.get('MONGODB_URI', 
                "mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            mongo_handler = MongoDBHandler(mongo_uri)
            comparator = MonthlyComparison(data_handler=data_handler, mongo_handler=mongo_handler)
            
            # Conectar ao MongoDB
            mongo_connected = mongo_handler.connect()
            if mongo_connected:
                mongo_handler.create_indexes()
                mongo_handler.initialize_default_categories()
                print("✅ Conectado ao MongoDB com sucesso!")
            else:
                print("❌ Falha na conexão com MongoDB")
        except Exception as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            mongo_connected = False
    else:
        print("⚠️ MongoDB não disponível - funcionalidades limitadas")
    
    def allowed_file(filename):
        """Verifica se o arquivo é permitido"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}
    
    # Context processor para disponibilizar variáveis globalmente
    @app.context_processor
    def inject_global_vars():
        return {
            'mongo_connected': mongo_connected,
            'registration_enabled': app.config.get('REGISTRATION_ENABLED', True)
        }
    
    # Middleware de segurança
    @app.before_request
    def configure_session():
        """Configura a sessão antes de cada requisição"""
        # Tornar sessão permanente
        session.permanent = True
        
        # Garantir que a sessão seja inicializada corretamente
        if 'csrf_token' not in session:
            session['csrf_token'] = None
    
    @app.before_request
    def security_headers():
        """Adiciona headers de segurança"""
        # Permitir acesso aos arquivos estáticos sem autenticação
        if request.endpoint and (request.endpoint.startswith('static') or 
                                request.endpoint.startswith('auth.')):
            return
        
        # Verificar se o usuário está autenticado para outras rotas
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
    
    @app.after_request
    def after_request(response):
        """Adiciona headers de segurança na resposta"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Rotas principais
    @app.route('/')
    @login_required
    def index():
        """Página principal"""
        # Obter estatísticas básicas
        stats = data_handler.get_statistics()
        mongo_count = 0
        
        if mongo_connected:
            try:
                mongo_count = mongo_handler.get_transactions_count()
            except:
                pass
        
        return render_template('index.html', 
                             stats=stats, 
                             mongo_connected=mongo_connected,
                             mongo_count=mongo_count,
                             user=current_user)
    
    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_file():
        """Upload e análise de arquivo PDF"""
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('index'))
        
        # Capturar data de pagamento
        payment_date_str = request.form.get('payment_date')
        if not payment_date_str:
            flash('Data de pagamento é obrigatória', 'error')
            return redirect(url_for('index'))
        
        try:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Data de pagamento inválida', 'error')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Adicionar timestamp para evitar conflitos
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Analisar PDF
                result = analyzer.analyze_pdf(filepath)
                
                # Aplicar categorização automática se MongoDB estiver disponível
                if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                    auto_categorized_count = 0
                    for transacao in result.get('transacoes', []):
                        if transacao.get('categoria') == 'outros':
                            match_result = mongo_handler.find_matching_category(
                                descricao=transacao.get('descricao', ''),
                                banco=transacao.get('banco'),
                                origem_cartao=transacao.get('origem_cartao')
                            )
                            
                            if match_result['found'] and match_result['confidence'] > 0.7:
                                transacao['categoria'] = match_result['categoria']
                                transacao['auto_categorized'] = True
                                transacao['confidence_score'] = match_result['confidence']
                                auto_categorized_count += 1
                    
                    if auto_categorized_count > 0:
                        print(f"✅ {auto_categorized_count} transações categorizadas automaticamente")
                
                # Adicionar informações do usuário
                result['user_id'] = current_user.id
                result['user_username'] = current_user.username
                
                # Armazenar resultado na sessão
                session_data = {
                    'filename': file.filename,
                    'analysis_result': result,
                    'payment_date': payment_date.isoformat(),
                    'timestamp': datetime.now().isoformat(),
                    'user_id': current_user.id,
                    'user_username': current_user.username
                }
                
                # Salvar dados da sessão em arquivo temporário
                session_file = f"session_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                
                # Remover arquivo PDF após análise
                os.remove(filepath)
                
                flash(f'PDF analisado com sucesso! {result["total_transacoes"]} transações encontradas.', 'success')
                return redirect(url_for('analysis_result', session_file=session_file))
                
            except Exception as e:
                # Remover arquivo em caso de erro
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash(f'Erro ao analisar PDF: {str(e)}', 'error')
                return redirect(url_for('index'))
        
        else:
            flash('Tipo de arquivo não permitido. Apenas PDFs são aceitos.', 'error')
            return redirect(url_for('index'))
    
    @app.route('/analysis/<session_file>')
    @login_required
    def analysis_result(session_file):
        """Página de resultado da análise"""
        try:
            # Verificar se o arquivo pertence ao usuário atual
            if not session_file.startswith(f'session_{current_user.id}_'):
                flash('Acesso negado a esta sessão.', 'error')
                return redirect(url_for('index'))
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verificar se a sessão pertence ao usuário
            if session_data.get('user_id') != current_user.id:
                flash('Acesso negado a esta sessão.', 'error')
                return redirect(url_for('index'))
            
            # Extrair session_id do nome do arquivo
            session_id = session_file.replace(f'session_{current_user.id}_', '').replace('.json', '')
            
            # Obter categorias do MongoDB se disponível
            categories = []
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                try:
                    categories = mongo_handler.get_categories()
                except Exception as e:
                    print(f"Erro ao obter categorias: {e}")
                    # Usar categorias padrão se houver erro
                    categories = [
                        {'nome': 'alimentacao', 'nome_exibicao': 'Alimentação', 'ativo': True},
                        {'nome': 'transporte', 'nome_exibicao': 'Transporte', 'ativo': True},
                        {'nome': 'saude', 'nome_exibicao': 'Saúde', 'ativo': True},
                        {'nome': 'educacao', 'nome_exibicao': 'Educação', 'ativo': True},
                        {'nome': 'lazer', 'nome_exibicao': 'Lazer', 'ativo': True},
                        {'nome': 'compras', 'nome_exibicao': 'Compras', 'ativo': True},
                        {'nome': 'servicos', 'nome_exibicao': 'Serviços', 'ativo': True},
                        {'nome': 'outros', 'nome_exibicao': 'Outros', 'ativo': True}
                    ]
            else:
                # Usar categorias padrão se MongoDB não estiver disponível
                categories = [
                    {'nome': 'alimentacao', 'nome_exibicao': 'Alimentação', 'ativo': True},
                    {'nome': 'transporte', 'nome_exibicao': 'Transporte', 'ativo': True},
                    {'nome': 'saude', 'nome_exibicao': 'Saúde', 'ativo': True},
                    {'nome': 'educacao', 'nome_exibicao': 'Educação', 'ativo': True},
                    {'nome': 'lazer', 'nome_exibicao': 'Lazer', 'ativo': True},
                    {'nome': 'compras', 'nome_exibicao': 'Compras', 'ativo': True},
                    {'nome': 'servicos', 'nome_exibicao': 'Serviços', 'ativo': True},
                    {'nome': 'outros', 'nome_exibicao': 'Outros', 'ativo': True}
                ]
            
            return render_template('analysis.html', 
                                 session_data=session_data,
                                 session_file=session_file,
                                 session_id=session_id,
                                 mongo_connected=mongo_connected,
                                 categories=categories,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao carregar resultado: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/save_to_mongodb', methods=['POST'])
    @login_required
    @csrf.exempt
    def save_to_mongodb():
        """Salva transações no MongoDB"""
        if not MONGODB_AVAILABLE or not mongo_connected or not mongo_handler:
            return jsonify({
                'success': False,
                'message': 'MongoDB não disponível'
            })
        
        try:
            data = request.get_json()
            session_file = data.get('session_file')
            card_origin = data.get('card_origin', 'Cartão Principal')
            remove_duplicates = data.get('remove_duplicates', True)
            
            if not session_file:
                return jsonify({
                    'success': False,
                    'message': 'Arquivo de sessão não especificado'
                })
            
            # Verificar se o arquivo pertence ao usuário atual
            if not session_file.startswith(f'session_{current_user.id}_'):
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado a esta sessão'
                })
            
            # Verificar se o arquivo de sessão existe
            if not os.path.exists(session_file):
                return jsonify({
                    'success': False,
                    'message': f'Arquivo de sessão não encontrado: {session_file}'
                })
            
            # Carregar dados da sessão
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verificar se a sessão pertence ao usuário
            if session_data.get('user_id') != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado a esta sessão'
                })
            
            if 'analysis_result' not in session_data or 'transacoes' not in session_data['analysis_result']:
                return jsonify({
                    'success': False,
                    'message': 'Dados de sessão inválidos - transações não encontradas'
                })
            
            transactions = session_data['analysis_result']['transacoes']
            
            if not transactions:
                return jsonify({
                    'success': False,
                    'message': 'Nenhuma transação encontrada para salvar'
                })
            
            # Adicionar informações do usuário às transações
            payment_date = session_data.get('payment_date')
            for transaction in transactions:
                transaction['data_pagamento'] = payment_date
                transaction['user_id'] = current_user.id
                transaction['user_username'] = current_user.username
                transaction['created_at'] = datetime.now().isoformat()
            
            # Salvar no MongoDB
            result = mongo_handler.save_transactions(transactions, card_origin, remove_duplicates)
            
            return jsonify(result)
            
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'message': f'Erro ao ler arquivo de sessão: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Erro ao salvar no MongoDB: {str(e)}'
            })
    
    @app.route('/save_to_local', methods=['POST'])
    @login_required
    @csrf.exempt
    def save_to_local():
        """Salva transações localmente"""
        try:
            data = request.get_json()
            session_file = data.get('session_file')
            card_origin = data.get('card_origin', 'Cartão Principal')
            remove_duplicates = data.get('remove_duplicates', True)
            
            if not session_file:
                return jsonify({
                    'success': False,
                    'message': 'Arquivo de sessão não especificado'
                })
            
            # Verificar se o arquivo pertence ao usuário atual
            if not session_file.startswith(f'session_{current_user.id}_'):
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado a esta sessão'
                })
            
            # Verificar se o arquivo de sessão existe
            if not os.path.exists(session_file):
                return jsonify({
                    'success': False,
                    'message': f'Arquivo de sessão não encontrado: {session_file}'
                })
            
            # Carregar dados da sessão
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verificar se a sessão pertence ao usuário
            if session_data.get('user_id') != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado a esta sessão'
                })
            
            if 'analysis_result' not in session_data or 'transacoes' not in session_data['analysis_result']:
                return jsonify({
                    'success': False,
                    'message': 'Dados de sessão inválidos - transações não encontradas'
                })
            
            transactions = session_data['analysis_result']['transacoes']
            
            if not transactions:
                return jsonify({
                    'success': False,
                    'message': 'Nenhuma transação encontrada para salvar'
                })
            
            # Adicionar informações do usuário às transações
            payment_date = session_data.get('payment_date')
            for transaction in transactions:
                transaction['data_pagamento'] = payment_date
                transaction['user_id'] = current_user.id
                transaction['user_username'] = current_user.username
                transaction['created_at'] = datetime.now().isoformat()
            
            # Salvar localmente
            result = data_handler.save_transactions(transactions, card_origin, remove_duplicates)
            
            return jsonify(result)
            
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'message': f'Erro ao ler arquivo de sessão: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Erro ao salvar localmente: {str(e)}'
            })
    
    @app.route('/transactions')
    @login_required
    def view_transactions():
        """Página de visualização de transações"""
        try:
            if not MONGODB_AVAILABLE or not mongo_connected or not mongo_handler:
                flash('Funcionalidade de transações não disponível - MongoDB necessário', 'error')
                return redirect(url_for('index'))
            
            # Obter parâmetros de filtro
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            keyword = request.args.get('keyword', '').strip() or None
            start_date = request.args.get('start_date', '').strip() or None
            end_date = request.args.get('end_date', '').strip() or None
            payment_start_date = request.args.get('payment_start_date', '').strip() or None
            payment_end_date = request.args.get('payment_end_date', '').strip() or None
            card_origin = request.args.get('card_origin', '').strip() or None
            banco = request.args.get('banco', '').strip() or None
            categoria = request.args.get('categoria', '').strip() or None
            
            # Se não há filtros de data de pagamento, preencher com mês corrente
            if not payment_start_date and not payment_end_date:
                from datetime import datetime, date
                today = date.today()
                # Primeiro dia do mês atual
                payment_start_date = today.replace(day=1).strftime('%Y-%m-%d')
                # Último dia do mês atual
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                payment_end_date = (next_month - date.resolution).strftime('%Y-%m-%d')
            
            # Obter transações do MongoDB com filtros
            try:
                result = mongo_handler.get_transactions_paginated(
                    page=page,
                    per_page=per_page,
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    card_origin=card_origin,
                    banco=banco,
                    payment_start_date=payment_start_date,
                    payment_end_date=payment_end_date
                )
            except Exception as e:
                print(f"DEBUG: Erro na chamada get_transactions_paginated: {e}")
                # Fallback para chamada sem os novos parâmetros
                result = mongo_handler.get_transactions_paginated(
                    page=page,
                    per_page=per_page,
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    card_origin=card_origin,
                    banco=banco
                )
            
            if not result.get('success', False):
                flash(f'Erro ao carregar transações: {result.get("message", "Erro desconhecido")}', 'error')
                return redirect(url_for('index'))
            
            # Obter transações e paginação
            transactions = result.get('transactions', [])
            pagination_info = result.get('pagination', {})
            
            # Filtrar por categoria se especificado
            if categoria:
                transactions = [t for t in transactions if t.get('categoria') == categoria]
                # Atualizar informações de paginação
                pagination_info['total_count'] = len(transactions)
                pagination_info['total_pages'] = (len(transactions) + per_page - 1) // per_page
            
            # Obter categorias disponíveis para o filtro
            available_categories = mongo_handler.get_categories()
            
            # Obter origens de cartão disponíveis
            card_origins = mongo_handler.get_card_origins()
            
            # Obter bancos disponíveis
            available_banks = mongo_handler.get_available_banks()
            
            return render_template('transactions.html',
                                 transactions=transactions,
                                 pagination=pagination_info,
                                 available_categories=available_categories,
                                 card_origins=card_origins,
                                 available_banks=available_banks,
                                 current_filters={
                                     'page': page,
                                     'per_page': per_page,
                                     'keyword': keyword or '',
                                     'start_date': start_date or '',
                                     'end_date': end_date or '',
                                     'payment_start_date': payment_start_date or '',
                                     'payment_end_date': payment_end_date or '',
                                     'card_origin': card_origin or '',
                                     'banco': banco or '',
                                     'categoria': categoria or ''
                                 },
                                 mongo_connected=mongo_connected,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao carregar transações: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/comparison')
    @login_required
    def monthly_comparison():
        """Página de comparativo mensal"""
        try:
            if not MONGODB_AVAILABLE or not comparator:
                flash('Funcionalidade de comparação não disponível - MongoDB necessário', 'error')
                return redirect(url_for('index'))
                
            card_origin = request.args.get('card_origin', None)
            
            # Gerar relatório comparativo
            report = comparator.generate_comparison_report(card_origin)
            
            # Obter dados de categorias por mês para o gráfico
            categories_data = mongo_handler.get_categories_by_month(months_back=6, card_origin=card_origin)
            
            # Obter dados de parcelamentos futuros
            installments_data = mongo_handler.get_future_installments(months_ahead=6)
            
            return render_template('comparison.html', 
                                 report=report, 
                                 categories_data=categories_data,
                                 installments_data=installments_data,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao gerar comparativo: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/category_report')
    @login_required
    def category_report():
        """Página de relatório por categoria"""
        try:
            if not MONGODB_AVAILABLE or not mongo_connected or not mongo_handler:
                flash('Funcionalidade de relatório por categoria não disponível - MongoDB necessário', 'error')
                return redirect(url_for('index'))
            
            # Obter parâmetros da URL
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            category = request.args.get('category', '').strip() or None
            card_origin = request.args.get('card_origin', '').strip() or None
            
            # Valores padrão se não especificados
            if not start_date or not end_date:
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Gerar relatório
            report = mongo_handler.get_transactions_by_category_and_period(
                start_date=start_date,
                end_date=end_date,
                category=category,
                card_origin=card_origin
            )
            
            # Obter categorias disponíveis para o filtro
            available_categories = mongo_handler.get_categories()
            
            # Obter origens de cartão disponíveis
            card_origins = mongo_handler.get_card_origins()
            
            return render_template('category_report.html', 
                                 report=report,
                                 available_categories=available_categories,
                                 card_origins=card_origins,
                                 current_filters={
                                     'start_date': start_date,
                                     'end_date': end_date,
                                     'category': category,
                                     'card_origin': card_origin
                                 },
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao gerar relatório por categoria: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/export/<format>')
    @login_required
    def export_data(format):
        """Exporta dados do usuário"""
        data = request.args.get('data')
        if not data:
            return jsonify({'error': 'Nenhum dado para exportar'}), 400
        
        try:
            transactions = json.loads(data)
            
            # Filtrar transações do usuário atual por segurança
            user_transactions = [
                t for t in transactions 
                if t.get('user_id') == current_user.id
            ]
            
            if not user_transactions:
                return jsonify({'error': 'Nenhuma transação encontrada para este usuário'}), 400
            
            df = pd.DataFrame(user_transactions)
            
            if format == 'csv':
                output = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                df.to_csv(output.name, index=False, encoding='utf-8-sig')
                return send_file(output.name, as_attachment=True, 
                               download_name=f'faturas_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv')
            
            elif format == 'excel':
                output = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                df.to_excel(output.name, index=False, engine='openpyxl')
                return send_file(output.name, as_attachment=True, 
                               download_name=f'faturas_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.xlsx')
            
            elif format == 'json':
                output = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w')
                json.dump(user_transactions, output, indent=2, ensure_ascii=False)
                output.close()
                return send_file(output.name, as_attachment=True, 
                               download_name=f'faturas_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.json')
            
        except Exception as e:
            return jsonify({'error': f'Erro ao exportar dados: {str(e)}'}), 500
    
    @app.route('/categories')
    @login_required
    def manage_categories():
        """Página de gerenciamento de categorias"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                flash('Funcionalidade de categorias não disponível - MongoDB necessário', 'error')
                return redirect(url_for('index'))
            
            # Inicializar categorias padrão se necessário
            mongo_handler.initialize_default_categories()
            
            # Obter categorias
            categories = mongo_handler.get_categories()
            
            return render_template('categories.html', 
                                 categories=categories,
                                 mongo_connected=mongo_connected,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao carregar categorias: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/categorization_stats')
    @login_required
    def categorization_stats():
        """Página de estatísticas de categorização automática"""
        try:
            if not MONGODB_AVAILABLE or not mongo_connected or not mongo_handler:
                flash('Funcionalidade não disponível - MongoDB necessário', 'error')
                return redirect(url_for('index'))
            
            stats = mongo_handler.get_categorization_stats()
            
            return render_template('categorization_stats.html', 
                                 stats=stats,
                                 mongo_connected=mongo_connected,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/api/transactions/mongodb')
    @login_required
    @csrf.exempt
    def api_get_mongodb_transactions():
        """API para obter transações do MongoDB com paginação e filtros"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            # Parâmetros de paginação
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # Parâmetros de filtro
            keyword = request.args.get('keyword', '').strip() or None
            start_date = request.args.get('start_date', '').strip() or None
            end_date = request.args.get('end_date', '').strip() or None
            card_origin = request.args.get('card_origin', '').strip() or None
            banco = request.args.get('banco', '').strip() or None
            
            result = mongo_handler.get_transactions_paginated(
                page=page,
                per_page=per_page,
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                card_origin=card_origin,
                banco=banco,
                payment_start_date=None,
                payment_end_date=None
            )
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/update_transaction_category', methods=['POST'])
    @login_required
    @csrf.exempt
    def update_transaction_category():
        """Atualiza a categoria de uma transação"""
        try:
            data = request.get_json()
            transaction_hash = data.get('transaction_hash')
            new_category = data.get('new_category')
            
            if not transaction_hash or not new_category:
                return jsonify({
                    'success': False,
                    'message': 'Hash da transação e nova categoria são obrigatórios'
                })
            
            # Obter dados da transação para salvar o padrão
            transaction_data = None
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                # Buscar transação no MongoDB
                transaction = mongo_handler.collection.find_one({'transaction_hash': transaction_hash})
                if transaction:
                    transaction_data = transaction
                else:
                    # Buscar no arquivo local
                    local_transactions = data_handler.get_transactions()
                    for trans in local_transactions:
                        if trans.get('transaction_hash') == transaction_hash:
                            transaction_data = trans
                            break
            
            # Atualizar no arquivo local
            result = data_handler.update_transaction_category(transaction_hash, new_category)
            
            # Se MongoDB estiver disponível, atualizar lá também
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                try:
                    mongo_result = mongo_handler.update_transaction_category(transaction_hash, new_category)
                    if mongo_result['success']:
                        result['message'] += f" (MongoDB: {mongo_result['message']})"
                        
                        # Salvar padrão de categorização para aprendizado automático
                        if transaction_data and result['success']:
                            pattern_result = mongo_handler.save_categorization_pattern(
                                descricao=transaction_data.get('descricao', ''),
                                categoria=new_category,
                                banco=transaction_data.get('banco'),
                                origem_cartao=transaction_data.get('origem_cartao')
                            )
                            if pattern_result['success']:
                                print(f"✅ Padrão de categorização salvo: {transaction_data.get('descricao', '')} -> {new_category}")
                            else:
                                print(f"⚠️ Erro ao salvar padrão: {pattern_result['message']}")
                except Exception as e:
                    result['message'] += f" (Erro no MongoDB: {str(e)})"
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Erro ao atualizar categoria: {str(e)}'
            })

    @app.route('/api/stats')
    @login_required
    @csrf.exempt
    def api_stats():
        """API para estatísticas"""
        try:
            stats = data_handler.get_statistics()
            mongo_count = 0
            
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                try:
                    mongo_count = mongo_handler.get_transactions_count()
                except:
                    pass
            
            return jsonify({
                'local': stats,
                'mongo_count': mongo_count,
                'mongo_connected': mongo_connected
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export_mongodb')
    @login_required
    @csrf.exempt
    def api_export_mongodb():
        """API para exportar dados para MongoDB"""
        try:
            transactions = data_handler.export_to_mongodb_format()
            
            if not transactions:
                return jsonify({'error': 'Nenhuma transação para exportar'}), 400
            
            # Salvar em arquivo
            filename = f"transacoes_mongodb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'count': len(transactions)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/categories', methods=['GET'])
    @login_required
    @csrf.exempt
    def api_get_categories():
        """API para obter categorias"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            categories = mongo_handler.get_categories()
            return jsonify({'success': True, 'categories': categories})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/categories', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_add_category():
        """API para adicionar categoria"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            data = request.get_json()
            nome = data.get('nome', '').strip()
            descricao = data.get('descricao', '').strip()
            cor = data.get('cor', '#6c757d')
            
            if not nome:
                return jsonify({'error': 'Nome da categoria é obrigatório'}), 400
            
            result = mongo_handler.add_category(nome, descricao, cor)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/categories/<category_id>', methods=['PUT'])
    @login_required
    @csrf.exempt
    def api_update_category(category_id):
        """API para atualizar categoria"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            data = request.get_json()
            result = mongo_handler.update_category(
                category_id,
                nome=data.get('nome'),
                descricao=data.get('descricao'),
                cor=data.get('cor'),
                ativo=data.get('ativo')
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/categories/<category_id>', methods=['DELETE'])
    @login_required
    @csrf.exempt
    def api_delete_category(category_id):
        """API para remover categoria"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            result = mongo_handler.delete_category(category_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/auto_categorize', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_auto_categorize():
        """API para aplicar categorização automática baseada em padrões"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            data = request.get_json()
            descricao = data.get('descricao', '')
            banco = data.get('banco')
            origem_cartao = data.get('origem_cartao')
            
            if not descricao:
                return jsonify({'error': 'Descrição é obrigatória'}), 400
            
            # Buscar categoria correspondente
            match_result = mongo_handler.find_matching_category(descricao, banco, origem_cartao)
            
            return jsonify({
                'success': True,
                'found': match_result['found'],
                'categoria': match_result.get('categoria'),
                'confidence': match_result.get('confidence', 0.0),
                'match_type': match_result.get('match_type', 'none')
            })
            
        except Exception as e:
            return jsonify({'error': f'Erro ao categorizar automaticamente: {str(e)}'}), 500

    @app.route('/api/categorization_stats')
    @login_required
    @csrf.exempt
    def api_categorization_stats():
        """API para obter estatísticas de categorização automática"""
        try:
            if not MONGODB_AVAILABLE or not mongo_handler:
                return jsonify({'error': 'MongoDB não disponível'}), 400
            
            stats = mongo_handler.get_categorization_stats()
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({'error': f'Erro ao obter estatísticas: {str(e)}'}), 500

    @app.route('/api/session/remove_transaction', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_remove_session_transaction():
        """API para remover uma transação da sessão"""
        try:
            data = request.get_json()
            transaction_index = data.get('transaction_index')
            session_id = data.get('session_id')
            
            if transaction_index is None or not session_id:
                return jsonify({'success': False, 'message': 'Índice da transação e ID da sessão são obrigatórios'}), 400
            
            # Construir nome do arquivo de sessão com user_id
            session_file = f'session_{current_user.id}_{session_id}.json'
            if not os.path.exists(session_file):
                return jsonify({'success': False, 'message': 'Sessão não encontrada'}), 404
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verificar se a sessão pertence ao usuário
            if session_data.get('user_id') != current_user.id:
                return jsonify({'success': False, 'message': 'Acesso negado a esta sessão'}), 403
            
            if 'analysis_result' not in session_data or 'transacoes' not in session_data['analysis_result']:
                return jsonify({'success': False, 'message': 'Dados de sessão inválidos'}), 400
            
            transactions = session_data['analysis_result']['transacoes']
            
            if transaction_index >= len(transactions):
                return jsonify({'success': False, 'message': 'Índice da transação inválido'}), 400
            
            # Remover transação
            removed_transaction = transactions.pop(transaction_index)
            
            # Salvar sessão atualizada
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': f'Transação removida: {removed_transaction.get("descricao", "N/A")}',
                'removed_transaction': removed_transaction,
                'remaining_count': len(transactions)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao remover transação da sessão: {str(e)}'}), 500

    @app.route('/api/transactions/remove', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_remove_transaction():
        """API para remover uma transação específica"""
        try:
            data = request.get_json()
            transaction_hash = data.get('transaction_hash')
            storage_type = data.get('storage_type', 'local')  # 'local' ou 'mongodb'
            
            if not transaction_hash:
                return jsonify({'success': False, 'message': 'Hash da transação é obrigatório'}), 400
            
            if storage_type == 'local':
                # Recarregar dados antes de tentar remover
                data_handler.load_data()
                result = data_handler.remove_transaction(transaction_hash)
            elif storage_type == 'mongodb':
                if not MONGODB_AVAILABLE or not mongo_handler:
                    return jsonify({'success': False, 'message': 'MongoDB não disponível'}), 400
                result = mongo_handler.remove_transaction(transaction_hash)
            else:
                return jsonify({'success': False, 'message': 'Tipo de armazenamento inválido'}), 400
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao remover transação: {str(e)}'}), 500

    @app.route('/api/transactions/remove_all', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_remove_all_transactions():
        """API para remover todas as transações"""
        try:
            data = request.get_json()
            storage_type = data.get('storage_type', 'local')  # 'local' ou 'mongodb'
            
            if storage_type == 'local':
                result = data_handler.remove_all_transactions()
            elif storage_type == 'mongodb':
                if not MONGODB_AVAILABLE or not mongo_handler:
                    return jsonify({'success': False, 'message': 'MongoDB não disponível'}), 400
                result = mongo_handler.remove_all_transactions()
            else:
                return jsonify({'success': False, 'message': 'Tipo de armazenamento inválido'}), 400
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao remover todas as transações: {str(e)}'}), 500

    @app.route('/api/session/update_category', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_update_session_category():
        """API para atualizar categoria de uma transação na sessão"""
        try:
            data = request.get_json()
            transaction_index = data.get('transaction_index')
            session_id = data.get('session_id')
            new_category = data.get('new_category')
            
            if transaction_index is None or not session_id or not new_category:
                return jsonify({'success': False, 'message': 'Índice da transação, ID da sessão e nova categoria são obrigatórios'}), 400
            
            # Construir nome do arquivo de sessão com user_id
            session_file = f'session_{current_user.id}_{session_id}.json'
            if not os.path.exists(session_file):
                return jsonify({'success': False, 'message': 'Sessão não encontrada'}), 404
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verificar se a sessão pertence ao usuário
            if session_data.get('user_id') != current_user.id:
                return jsonify({'success': False, 'message': 'Acesso negado a esta sessão'}), 403
            
            if 'analysis_result' not in session_data or 'transacoes' not in session_data['analysis_result']:
                return jsonify({'success': False, 'message': 'Dados de sessão inválidos'}), 400
            
            transactions = session_data['analysis_result']['transacoes']
            
            if transaction_index >= len(transactions):
                return jsonify({'success': False, 'message': 'Índice da transação inválido'}), 400
            
            # Obter transação atual
            transaction = transactions[transaction_index]
            old_category = transaction.get('categoria', 'outros')
            
            # Atualizar categoria
            transaction['categoria'] = new_category
            
            # Salvar padrão de categorização para aprendizado automático se MongoDB estiver disponível
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                try:
                    pattern_result = mongo_handler.save_categorization_pattern(
                        descricao=transaction.get('descricao', ''),
                        categoria=new_category,
                        banco=transaction.get('banco'),
                        origem_cartao=transaction.get('origem_cartao', 'Cartão Principal')
                    )
                    if pattern_result['success']:
                        print(f"✅ Padrão de categorização salvo: {transaction.get('descricao', '')} -> {new_category}")
                except Exception as e:
                    print(f"⚠️ Erro ao salvar padrão: {e}")
            
            # Salvar sessão atualizada
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': f'Categoria atualizada de "{old_category}" para "{new_category}"',
                'old_category': old_category,
                'new_category': new_category,
                'pattern_saved': MONGODB_AVAILABLE and mongo_connected
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Erro ao atualizar categoria da sessão: {str(e)}'}), 500

    # Manipulador de erro 404
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    # Manipulador de erro 403
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Manipulador de erro 500
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("🔐 INICIANDO SISTEMA SEGURO - ANALISADOR DE PDFs")
    print("="*60)
    print("🔑 Sistema com autenticação habilitada")
    print(f"🌐 Interface disponível em: http://localhost:{port}")
    print("👤 Usuário padrão: admin / admin123")
    print("🔒 Todas as rotas protegidas por login")
    print("="*60)
    
    app.run(debug=debug, host='0.0.0.0', port=port)