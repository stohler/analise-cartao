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

def process_comparison_data(transactions):
    """Processa dados de transações para comparação mês a mês"""
    from collections import defaultdict
    import calendar
    
    # Agrupar por mês e categoria
    monthly_data = defaultdict(lambda: defaultdict(float))
    category_totals = defaultdict(float)
    
    for transaction in transactions:
        try:
            # Extrair mês e ano da data
            date_str = transaction.get('data', '')
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) >= 2:
                    month = int(parts[1])
                    year = int(parts[2]) if len(parts) > 2 else datetime.now().year
                    
                    # Criar chave do mês (YYYY-MM)
                    month_key = f"{year}-{month:02d}"
                    
                    # Obter categoria
                    category = transaction.get('categoria', 'outros')
                    value = float(transaction.get('valor', 0))
                    
                    # Acumular valores
                    monthly_data[month_key][category] += value
                    category_totals[category] += value
        except (ValueError, IndexError):
            continue
    
    # Converter para formato mais amigável
    comparison_data = {
        'monthly_breakdown': {},
        'category_totals': dict(category_totals),
        'months': sorted(monthly_data.keys()),
        'categories': list(category_totals.keys())
    }
    
    # Processar dados mensais
    for month_key in sorted(monthly_data.keys()):
        year, month = month_key.split('-')
        month_name = calendar.month_name[int(month)]
        comparison_data['monthly_breakdown'][month_key] = {
            'month_name': f"{month_name}/{year}",
            'categories': dict(monthly_data[month_key]),
            'total': sum(monthly_data[month_key].values())
        }
    
    return comparison_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/upload_multiple', methods=['POST'])
def upload_multiple_files():
    if 'files' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        all_transactions = []
        processed_files = []
        
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                # Salvar arquivo temporariamente
                filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Analisar PDF
                result = pdf_analyzer.analyze_pdf(filepath)
                
                # Adicionar nome do arquivo aos dados
                for transaction in result.get('transactions', []):
                    transaction['arquivo'] = file.filename
                    all_transactions.append(transaction)
                
                processed_files.append({
                    'filename': file.filename,
                    'bank': result.get('bank', 'Desconhecido'),
                    'total_transactions': len(result.get('transactions', []))
                })
                
                # Limpar arquivo temporário
                os.remove(filepath)
        
        # Processar dados para comparação
        comparison_data = process_comparison_data(all_transactions)
        
        return jsonify({
            'success': True,
            'data': comparison_data,
            'processed_files': processed_files,
            'total_transactions': len(all_transactions)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar PDFs: {str(e)}'}), 500

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