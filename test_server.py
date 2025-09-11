#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servidor de teste simplificado para validação do Analisador de PDFs
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile

# Importar módulos do projeto
try:
    from pdf_analyzer import PDFAnalyzer
    from data_handler import DataHandler
    PDF_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Módulos não disponíveis: {e}")
    PDF_ANALYZER_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'test_secret_key_2025'

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar componentes se disponíveis
if PDF_ANALYZER_AVAILABLE:
    analyzer = PDFAnalyzer()
    data_handler = DataHandler()
else:
    analyzer = None
    data_handler = None

# Simulação de dados para teste
sample_transactions = [
    {
        "data": "15/08/2025",
        "descricao": "SUPERMERCADO ABC LTDA",
        "valor": 125.50,
        "categoria": "alimentacao",
        "banco": "nubank",
        "parcelado": "Não",
        "origem_cartao": "Principal"
    },
    {
        "data": "16/08/2025", 
        "descricao": "POSTO SHELL - Parcela 2/3",
        "valor": 200.00,
        "categoria": "transporte",
        "banco": "itau",
        "parcelado": "Sim",
        "origem_cartao": "Principal"
    },
    {
        "data": "17/08/2025",
        "descricao": "FARMACIA POPULAR",
        "valor": 45.80,
        "categoria": "saude",
        "banco": "bradesco",
        "parcelado": "Não", 
        "origem_cartao": "Adicional"
    }
]

def allowed_file(filename):
    """Verifica se o arquivo é permitido"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Página principal"""
    stats = {
        'total_transactions': len(sample_transactions),
        'total_amount': sum(t['valor'] for t in sample_transactions),
        'banks': list(set(t['banco'] for t in sample_transactions)),
        'categories': list(set(t['categoria'] for t in sample_transactions))
    }
    
    return render_template('test_index.html', 
                         stats=stats,
                         mongo_connected=False,
                         analyzer_available=PDF_ANALYZER_AVAILABLE)

@app.route('/view_transactions')
def view_transactions():
    """Visualizar transações"""
    return render_template('test_transactions.html', 
                         transactions=sample_transactions,
                         mongo_connected=False)

@app.route('/monthly_comparison') 
def monthly_comparison():
    """Comparativo mensal"""
    return render_template('test_comparison.html',
                         mongo_connected=False)

@app.route('/manage_categories')
def manage_categories():
    """Gerenciar categorias"""
    categories = list(set(t['categoria'] for t in sample_transactions))
    return render_template('test_categories.html',
                         categories=categories,
                         mongo_connected=False)

@app.route('/categorization_stats')
def categorization_stats():
    """Estatísticas de categorização"""
    return render_template('test_stats.html',
                         mongo_connected=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload e análise de arquivo PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Se o analisador estiver disponível, usar ele
            if PDF_ANALYZER_AVAILABLE and analyzer:
                result = analyzer.analyze_pdf(filepath)
                os.remove(filepath)  # Limpar arquivo temporário
                return jsonify({
                    'success': True,
                    'data': result,
                    'filename': file.filename
                })
            else:
                # Simular resultado para teste
                os.remove(filepath)  # Limpar arquivo temporário
                result = {
                    'bank': 'Teste',
                    'total_transactions': 3,
                    'transactions': sample_transactions
                }
                return jsonify({
                    'success': True,
                    'data': result,
                    'filename': file.filename,
                    'note': 'Resultado simulado - analisador não disponível'
                })
            
        except Exception as e:
            return jsonify({'error': f'Erro ao processar PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Formato de arquivo inválido. Apenas PDFs são aceitos.'}), 400

@app.route('/test_status')
def test_status():
    """Status do ambiente de teste"""
    status = {
        'server_running': True,
        'pdf_analyzer_available': PDF_ANALYZER_AVAILABLE,
        'upload_folder': os.path.exists(UPLOAD_FOLDER),
        'sample_data_loaded': len(sample_transactions) > 0,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

if __name__ == '__main__':
    print("🧪 AMBIENTE DE TESTE - ANALISADOR DE PDFs")
    print("="*50)
    print("🌐 Interface disponível em: http://localhost:8000")
    print("📊 Dados de exemplo carregados")
    print(f"📁 Upload habilitado: {UPLOAD_FOLDER}")
    print(f"🔍 Analisador PDF: {'✅ Disponível' if PDF_ANALYZER_AVAILABLE else '❌ Não disponível'}")
    print("📋 Funcionalidades de teste:")
    print("   • Upload de PDFs")
    print("   • Visualização de transações")
    print("   • Interface básica")
    print("="*50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("\n👋 Servidor de teste interrompido")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")