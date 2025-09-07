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

# MongoDB não disponível
mongo_handler = None
comparator = None
mongo_connected = False
MONGODB_AVAILABLE = False

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
                             mongo_connected=mongo_connected)
    except Exception as e:
        flash(f'Erro ao carregar resultado: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/save_to_mongodb', methods=['POST'])
def save_to_mongodb():
    """Salva transações no MongoDB"""
    return jsonify({
        'success': False,
        'message': 'MongoDB não disponível'
    })

@app.route('/save_to_local', methods=['POST'])
def save_to_local():
    """Salva transações localmente"""
    try:
        data = request.get_json()
        session_file = data.get('session_file')
        card_origin = data.get('card_origin', 'Cartão Principal')
        remove_duplicates = data.get('remove_duplicates', True)
        
        # Carregar dados da sessão
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        transactions = session_data['analysis_result']['transacoes']
        
        # Salvar localmente
        result = data_handler.save_transactions(transactions, card_origin, remove_duplicates)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar localmente: {str(e)}'
        })

@app.route('/transactions')
def view_transactions():
    """Página de visualização de transações"""
    try:
        # Obter transações locais
        local_transactions = data_handler.get_all_transactions(limit=100)
        
        # MongoDB não disponível
        mongo_transactions = []
        
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
    flash('Funcionalidade de comparação não disponível - MongoDB necessário', 'error')
    return redirect(url_for('index'))

@app.route('/api/stats')
def api_stats():
    """API para estatísticas"""
    try:
        stats = data_handler.get_statistics()
        mongo_count = 0
        
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
    return jsonify({'error': 'MongoDB não disponível'}), 400

if __name__ == '__main__':
    print("🌐 Iniciando servidor web...")
    print("📊 Interface disponível em: http://localhost:5000")
    print("🔗 MongoDB:", "❌ Desconectado")
    app.run(debug=True, host='0.0.0.0', port=5000)
