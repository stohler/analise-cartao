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
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configurações da aplicação
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['REGISTRATION_ENABLED'] = os.environ.get('REGISTRATION_ENABLED', 'true').lower() == 'true'
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicializar extensões
    csrf = CSRFProtect(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Configurar user loader
    user_manager = get_user_manager()
    
    @login_manager.user_loader
    def load_user(user_id):
        return user_manager.get_user(user_id)
    
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
            
            return render_template('analysis.html', 
                                 session_data=session_data,
                                 session_file=session_file,
                                 session_id=session_id,
                                 mongo_connected=mongo_connected,
                                 user=current_user)
        except Exception as e:
            flash(f'Erro ao carregar resultado: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/save_to_mongodb', methods=['POST'])
    @login_required
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
            # Obter transações locais do usuário
            local_transactions = data_handler.get_user_transactions(current_user.id, limit=100)
            
            # Obter transações do MongoDB se conectado
            mongo_transactions = []
            if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
                try:
                    mongo_transactions = mongo_handler.get_user_transactions(current_user.id, limit=100)
                except:
                    pass
            
            return render_template('transactions.html',
                                 local_transactions=local_transactions,
                                 mongo_transactions=mongo_transactions,
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
            
            # Gerar relatório comparativo para o usuário atual
            report = comparator.generate_user_comparison_report(current_user.id, card_origin)
            
            return render_template('comparison.html', report=report, user=current_user)
        except Exception as e:
            flash(f'Erro ao gerar comparativo: {str(e)}', 'error')
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