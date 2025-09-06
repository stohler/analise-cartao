from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import pandas as pd
from pdf_analyzer import PDFAnalyzer
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar o analisador de PDF
pdf_analyzer = PDFAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Salvar arquivo temporariamente
            filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Analisar PDF
            result = pdf_analyzer.analyze_pdf(filepath)
            
            # Limpar arquivo temporário
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'data': result,
                'filename': file.filename
            })
            
        except Exception as e:
            return jsonify({'error': f'Erro ao processar PDF: {str(e)}'}), 500
    
    return jsonify({'error': 'Formato de arquivo inválido. Apenas PDFs são aceitos.'}), 400

@app.route('/export/<format>')
def export_data(format):
    data = request.args.get('data')
    if not data:
        return jsonify({'error': 'Nenhum dado para exportar'}), 400
    
    try:
        transactions = json.loads(data)
        df = pd.DataFrame(transactions)
        
        if format == 'csv':
            output = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            df.to_csv(output.name, index=False, encoding='utf-8-sig')
            return send_file(output.name, as_attachment=True, download_name='faturas_analisadas.csv')
        
        elif format == 'excel':
            output = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            df.to_excel(output.name, index=False, engine='openpyxl')
            return send_file(output.name, as_attachment=True, download_name='faturas_analisadas.xlsx')
        
        elif format == 'json':
            output = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w')
            json.dump(transactions, output, indent=2, ensure_ascii=False)
            output.close()
            return send_file(output.name, as_attachment=True, download_name='faturas_analisadas.json')
        
    except Exception as e:
        return jsonify({'error': f'Erro ao exportar dados: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)