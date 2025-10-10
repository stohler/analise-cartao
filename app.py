from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
import pandas as pd
from pdf_analyzer import PDFAnalyzer
from subtransaction_models import SubTransactionManager
from xml_parser import NFeParser
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar o analisador de PDF
pdf_analyzer = PDFAnalyzer()

# Inicializar gerenciador de subtransações
subtransaction_manager = SubTransactionManager()
xml_parser = NFeParser()

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

# ==========================================
# ROTAS PARA SUBTRANSAÇÕES
# ==========================================

@app.route('/subtransactions')
def subtransactions():
    """Página principal de subtransações"""
    unreconciled_xmls = subtransaction_manager.get_unreconciled_xmls()
    return render_template('subtransactions.html', 
                         unreconciled_xmls=unreconciled_xmls,
                         total_xmls=len(subtransaction_manager.xmls))

@app.route('/upload_xml', methods=['POST'])
def upload_xml():
    """Upload de XML de subtransações"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and file.filename.lower().endswith('.xml'):
        try:
            # Ler conteúdo do arquivo
            xml_content = file.read().decode('utf-8')
            
            # Parsear XML
            xml_obj = xml_parser.parse_xml_text(xml_content, file.filename)
            
            if xml_obj:
                # Adicionar ao gerenciador
                subtransaction_manager.add_xml(xml_obj)
                
                return jsonify({
                    'success': True,
                    'message': f'XML processado com sucesso! {xml_obj.get_total_items()} itens encontrados.',
                    'data': {
                        'xml_id': xml_obj.xml_id,
                        'establishment': xml_obj.establishment_name,
                        'total_value': xml_obj.total_value,
                        'items_count': xml_obj.get_total_items(),
                        'emission_date': xml_obj.emission_date.isoformat()
                    }
                })
            else:
                return jsonify({'error': 'Não foi possível processar o XML'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Erro ao processar XML: {str(e)}'}), 500
    
    return jsonify({'error': 'Formato de arquivo inválido. Apenas XMLs são aceitos.'}), 400

@app.route('/api/subtransactions')
def api_subtransactions():
    """API para listar subtransações não conciliadas"""
    unreconciled_xmls = subtransaction_manager.get_unreconciled_xmls()
    
    xmls_data = []
    for xml in unreconciled_xmls:
        xmls_data.append({
            'xml_id': xml.xml_id,
            'filename': xml.filename,
            'establishment_name': xml.establishment_name,
            'total_value': xml.total_value,
            'emission_date': xml.emission_date.isoformat(),
            'items_count': xml.get_total_items(),
            'categories_summary': xml.get_categories_summary()
        })
    
    return jsonify({
        'success': True,
        'data': xmls_data
    })

@app.route('/api/reconciliation_suggestions')
def api_reconciliation_suggestions():
    """API para obter sugestões de conciliação"""
    target_date_str = request.args.get('date')
    target_value_str = request.args.get('value')
    
    if not target_date_str or not target_value_str:
        return jsonify({'error': 'Data e valor são obrigatórios'}), 400
    
    try:
        target_date = datetime.fromisoformat(target_date_str)
        target_value = float(target_value_str)
        
        suggestions = subtransaction_manager.get_reconciliation_suggestions(
            target_date, target_value
        )
        
        suggestions_data = []
        for xml in suggestions:
            suggestions_data.append({
                'xml_id': xml.xml_id,
                'filename': xml.filename,
                'establishment_name': xml.establishment_name,
                'total_value': xml.total_value,
                'emission_date': xml.emission_date.isoformat(),
                'items_count': xml.get_total_items(),
                'categories_summary': xml.get_categories_summary()
            })
        
        return jsonify({
            'success': True,
            'data': suggestions_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar sugestões: {str(e)}'}), 500

@app.route('/api/reconcile_xml', methods=['POST'])
def api_reconcile_xml():
    """API para conciliar um XML com uma transação"""
    data = request.get_json()
    xml_id = data.get('xml_id')
    transaction_id = data.get('transaction_id')
    
    if not xml_id or not transaction_id:
        return jsonify({'error': 'XML ID e Transaction ID são obrigatórios'}), 400
    
    try:
        success = subtransaction_manager.reconcile_xml_with_transaction(xml_id, transaction_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'XML conciliado com sucesso!'
            })
        else:
            return jsonify({'error': 'XML não encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Erro ao conciliar XML: {str(e)}'}), 500

@app.route('/subcategory_report')
def subcategory_report():
    """Página de relatório por subcategoria"""
    # Agrupar subtransações por categoria e subcategoria
    from collections import defaultdict
    
    category_data = defaultdict(lambda: defaultdict(float))
    total_by_category = defaultdict(float)
    total_by_subcategory = defaultdict(float)
    
    for subtransaction in subtransaction_manager.subtransactions.values():
        if not subtransaction.reconciled:
            category = subtransaction.category
            subcategory = subtransaction.subcategory
            value = subtransaction.total_value
            
            category_data[category][subcategory] += value
            total_by_category[category] += value
            total_by_subcategory[f"{category}/{subcategory}"] += value
    
    return render_template('subcategory_report.html',
                         category_data=dict(category_data),
                         total_by_category=dict(total_by_category),
                         total_by_subcategory=dict(total_by_subcategory))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)