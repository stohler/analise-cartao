#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from pdf_analyzer import PDFAnalyzer
from data_handler import DataHandler
import threading
from datetime import datetime

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

app = Flask(__name__)
app.secret_key = 'analise_cartao_secret_key_2025'

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar componentes
analyzer = PDFAnalyzer()
data_handler = DataHandler()

# Inicializar MongoDB se disponível
mongo_handler = None
comparator = None
mongo_connected = False

if MONGODB_AVAILABLE:
    try:
        mongo_handler = MongoDBHandler("mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        comparator = MonthlyComparison(data_handler=data_handler, mongo_handler=mongo_handler)
        
        # Conectar ao MongoDB
        mongo_connected = mongo_handler.connect()
        if mongo_connected:
            mongo_handler.create_indexes()
            # Inicializar categorias padrão
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
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
                         mongo_count=mongo_count)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload e análise de arquivo PDF"""
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Analisar PDF
            result = analyzer.analyze_pdf(filepath)
            
            # Armazenar resultado na sessão
            session_data = {
                'filename': filename,
                'analysis_result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            # Salvar dados da sessão em arquivo temporário
            session_file = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
def analysis_result(session_file):
    """Página de resultado da análise"""
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return render_template('analysis.html', 
                             session_data=session_data,
                             session_file=session_file,
                             mongo_connected=mongo_connected)
    except Exception as e:
        flash(f'Erro ao carregar resultado: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/save_to_mongodb', methods=['POST'])
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
        
        # Verificar se o arquivo de sessão existe
        if not os.path.exists(session_file):
            return jsonify({
                'success': False,
                'message': f'Arquivo de sessão não encontrado: {session_file}'
            })
        
        # Carregar dados da sessão
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
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
        
        # Verificar se o arquivo de sessão existe
        if not os.path.exists(session_file):
            return jsonify({
                'success': False,
                'message': f'Arquivo de sessão não encontrado: {session_file}'
            })
        
        # Carregar dados da sessão
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
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

@app.route('/update_transaction_category', methods=['POST'])
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
        
        # Atualizar no arquivo local
        result = data_handler.update_transaction_category(transaction_hash, new_category)
        
        # Se MongoDB estiver disponível, atualizar lá também
        if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
            try:
                mongo_result = mongo_handler.update_transaction_category(transaction_hash, new_category)
                if mongo_result['success']:
                    result['message'] += f" (MongoDB: {mongo_result['message']})"
            except Exception as e:
                result['message'] += f" (Erro no MongoDB: {str(e)})"
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar categoria: {str(e)}'
        })

@app.route('/transactions')
def view_transactions():
    """Página de visualização de transações"""
    try:
        # Obter transações locais
        local_transactions = data_handler.get_all_transactions(limit=100)
        
        # Obter transações do MongoDB se conectado
        mongo_transactions = []
        if MONGODB_AVAILABLE and mongo_connected and mongo_handler:
            try:
                mongo_transactions = mongo_handler.get_all_transactions(limit=100)
            except:
                pass
        
        return render_template('transactions.html',
                             local_transactions=local_transactions,
                             mongo_transactions=mongo_transactions,
                             mongo_connected=mongo_connected)
    except Exception as e:
        flash(f'Erro ao carregar transações: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/comparison')
def monthly_comparison():
    """Página de comparativo mensal"""
    try:
        if not MONGODB_AVAILABLE or not comparator:
            flash('Funcionalidade de comparação não disponível - MongoDB necessário', 'error')
            return redirect(url_for('index'))
            
        card_origin = request.args.get('card_origin', None)
        
        # Gerar relatório comparativo
        report = comparator.generate_comparison_report(card_origin)
        
        return render_template('comparison.html', report=report)
    except Exception as e:
        flash(f'Erro ao gerar comparativo: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/stats')
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

@app.route('/categories')
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
                             mongo_connected=mongo_connected)
    except Exception as e:
        flash(f'Erro ao carregar categorias: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/categories', methods=['GET'])
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
def api_delete_category(category_id):
    """API para remover categoria"""
    try:
        if not MONGODB_AVAILABLE or not mongo_handler:
            return jsonify({'error': 'MongoDB não disponível'}), 400
        
        result = mongo_handler.delete_category(category_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/remove', methods=['POST'])
def api_remove_transaction():
    """API para remover uma transação específica"""
    try:
        data = request.get_json()
        transaction_hash = data.get('transaction_hash')
        storage_type = data.get('storage_type', 'local')  # 'local' ou 'mongodb'
        
        if not transaction_hash:
            return jsonify({'success': False, 'message': 'Hash da transação é obrigatório'}), 400
        
        if storage_type == 'local':
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

@app.route('/api/transactions/mongodb')
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
            banco=banco
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Iniciando servidor web...")
    print("📊 Interface disponível em: http://localhost:5000")
    print("🔗 MongoDB:", "✅ Conectado" if mongo_connected else "❌ Desconectado")
    app.run(debug=True, host='0.0.0.0', port=5000)
