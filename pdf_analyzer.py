import PyPDF2
import pdfplumber
import re
from datetime import datetime
from dateutil.parser import parse
import json

class PDFAnalyzer:
    def __init__(self):
        # Padrões para diferentes formatos de fatura
        self.patterns = {
            'nubank': {
                'transaction': r'(\d{2}/\d{2})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                'installment': r'(\d+)/(\d+)',
                'date_format': '%d/%m',
                'currency': r'R\$\s*([\d.,]+)',
                'categories': {
                    'alimentacao': ['restaurante', 'lanchonete', 'delivery', 'ifood', 'uber eats'],
                    'transporte': ['uber', '99', 'posto', 'combustivel', 'estacionamento'],
                    'saude': ['farmacia', 'drogaria', 'hospital', 'clinica', 'medico'],
                    'compras': ['magazine', 'americanas', 'mercado livre', 'amazon'],
                    'servicos': ['netflix', 'spotify', 'internet', 'telefone']
                }
            },
            'itau': {
                'transaction': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)',
                'installment': r'PARC\s*(\d+)/(\d+)',
                'date_format': '%d/%m/%Y',
                'currency': r'([\d.,]+)',
                'categories': {
                    'alimentacao': ['rest', 'lanch', 'delivery', 'ifood'],
                    'transporte': ['uber', 'taxi', 'posto', 'shell', 'br'],
                    'saude': ['farm', 'drog', 'hosp', 'clin'],
                    'compras': ['mag', 'loja', 'shopping'],
                    'servicos': ['netflix', 'spotify', 'tim', 'vivo']
                }
            },
            'bradesco': {
                'transaction': r'(\d{2}/\d{2})\s+(.+?)\s+(\d+,\d{2})',
                'installment': r'(\d+)ª\s*DE\s*(\d+)',
                'date_format': '%d/%m',
                'currency': r'(\d+,\d{2})',
                'categories': {
                    'alimentacao': ['rest', 'alim', 'delivery'],
                    'transporte': ['combustivel', 'posto', 'uber'],
                    'saude': ['farmacia', 'saude'],
                    'compras': ['varejo', 'loja'],
                    'servicos': ['assinatura', 'streaming']
                }
            },
            'santander': {
                'transaction': r'(\d{2}/\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)',
                'installment': r'PARCELA\s*(\d+)/(\d+)',
                'date_format': '%d/%m/%y',
                'currency': r'([\d.,]+)',
                'categories': {
                    'alimentacao': ['restaurante', 'alimentacao'],
                    'transporte': ['combustivel', 'transporte'],
                    'saude': ['saude', 'farmacia'],
                    'compras': ['compras', 'varejo'],
                    'servicos': ['servicos', 'utilidades']
                }
            },
            'caixa': {
                'transaction': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                'installment': r'(\d+)/(\d+)\s*PARCELA',
                'date_format': '%d/%m/%Y',
                'currency': r'R\$\s*([\d.,]+)',
                'categories': {
                    'alimentacao': ['aliment', 'rest', 'lanch'],
                    'transporte': ['combust', 'posto', 'transport'],
                    'saude': ['farm', 'saude', 'medic'],
                    'compras': ['loja', 'magazine', 'compra'],
                    'servicos': ['servico', 'assinatura']
                }
            },
            'btg': {
                'transaction': r'(\d{2}\s+\w{3})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                'installment': r'\((\d+)/(\d+)\)',
                'date_format': '%d %b',
                'currency': r'R\$\s*([\d.,]+)',
                'categories': {
                    'alimentacao': ['restaurante', 'bread', 'chef', 'california'],
                    'transporte': ['posto', 'grid', 'combustivel'],
                    'saude': ['farmacia', 'clinica', 'medico'],
                    'compras': ['damyller', 'calcad', 'livraria', 'shopping'],
                    'servicos': ['mensalidade', 'hotel', 'hair']
                }
            },
            'unicred': {
                'transaction': r'(\d{1,2}/\w{3})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                'installment': r'Parc\.(\d+)/(\d+)',
                'date_format': '%d/%b',
                'currency': r'R\$\s*([\d.,]+)',
                'categories': {
                    'alimentacao': ['angeloni', 'cooper', 'nosso pao', 'mc donalds', 'pizzaria', 'cantina', 'burger', 'lanches', 'cafe'],
                    'transporte': ['posto', 'postos'],
                    'saude': ['farmacia', 'drogaria', 'raia'],
                    'compras': ['garden', 'magazine'],
                    'servicos': ['seguros', 'anuidade', 'live']
                }
            },
            'c6': {
                'transaction': r'(\d{1,2}\s+\w{3})\s+(.+?)\s+([\d.,]+)$',
                'installment': r'-\s*Parcela\s+(\d+)/(\d+)',
                'date_format': '%d %b',
                'currency': r'([\d.,]+)',
                'categories': {
                    'alimentacao': ['ifood', 'restaurante'],
                    'transporte': ['latam', 'uber', 'posto'],
                    'saude': ['farmacia', 'clinica'],
                    'compras': ['amazon', 'flexform', 'mysadigital'],
                    'servicos': ['paypal', 'microsoft', 'google', 'prime', 'xbox', 'anuidade']
                }
            }
        }

    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto do PDF usando múltiplas bibliotecas"""
        text_content = ""
        
        # Tentar com pdfplumber primeiro (melhor para tabelas)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            print(f"Erro com pdfplumber: {e}")
        
        # Se não conseguiu extrair texto, tentar com PyPDF2
        if not text_content.strip():
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
            except Exception as e:
                print(f"Erro com PyPDF2: {e}")
        
        return text_content

    def detect_bank_format(self, text):
        """Detecta o formato do banco baseado no conteúdo do texto"""
        text_lower = text.lower()
        
        if 'nubank' in text_lower or 'nu pagamentos' in text_lower:
            return 'nubank'
        elif 'itau' in text_lower or 'itaú' in text_lower:
            return 'itau'
        elif 'bradesco' in text_lower:
            return 'bradesco'
        elif 'santander' in text_lower:
            return 'santander'
        elif 'btg' in text_lower or 'btg pactual' in text_lower:
            return 'btg'
        elif 'unicred' in text_lower:
            return 'unicred'
        elif 'c6' in text_lower or 'c6 bank' in text_lower or 'banco c6' in text_lower or 'c6 carbon' in text_lower:
            return 'c6'
        elif 'caixa' in text_lower or 'cef' in text_lower:
            return 'caixa'
        
        # Fallback: tentar detectar por padrões de transação
        for bank, patterns in self.patterns.items():
            if re.search(patterns['transaction'], text, re.IGNORECASE | re.MULTILINE):
                return bank
        
        return 'nubank'  # Default

    def categorize_transaction(self, description, bank_format):
        """Categoriza a transação baseada na descrição"""
        description_lower = description.lower()
        categories = self.patterns[bank_format]['categories']
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return 'outros'

    def parse_currency(self, currency_str):
        """Converte string de moeda para float"""
        if not currency_str:
            return 0.0
        
        # Remove símbolos de moeda e espaços
        clean_str = re.sub(r'[R$\s]', '', currency_str)
        
        # Substitui vírgula por ponto se for o separador decimal
        if ',' in clean_str and '.' not in clean_str:
            clean_str = clean_str.replace(',', '.')
        elif ',' in clean_str and '.' in clean_str:
            # Formato brasileiro: 1.234,56
            clean_str = clean_str.replace('.', '').replace(',', '.')
        
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    def parse_date(self, date_str, date_format, year=None):
        """Converte string de data para objeto datetime"""
        try:
            if year and '%Y' not in date_format:
                date_str = f"{date_str}/{year}"
                date_format = f"{date_format}/%Y"
            
            # Para BTG e Unicred, converter mês abreviado para português
            if '%b' in date_format:
                months_pt = {
                    'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr',
                    'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug',
                    'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'
                }
                for pt, en in months_pt.items():
                    if pt in date_str.lower():
                        date_str = date_str.lower().replace(pt, en)
                        break
            
            return datetime.strptime(date_str, date_format)
        except ValueError:
            try:
                return parse(date_str)
            except:
                return datetime.now()

    def extract_transactions(self, text, bank_format):
        """Extrai transações do texto baseado no formato do banco"""
        transactions = []
        patterns = self.patterns[bank_format]
        
        # Buscar transações
        transaction_matches = re.finditer(patterns['transaction'], text, re.IGNORECASE | re.MULTILINE)
        
        current_year = datetime.now().year
        
        for match in transaction_matches:
            try:
                groups = match.groups()
                
                if bank_format == 'nubank':
                    date_str, description, amount_str = groups
                elif bank_format == 'itau':
                    date_str, description, amount_str = groups
                    # Para Itaú, adicionar R$ se não estiver presente
                    if not amount_str.startswith('R$'):
                        amount_str = amount_str
                elif bank_format == 'caixa':
                    date_str, description, amount_str = groups
                elif bank_format == 'bradesco':
                    date_str, description, amount_str = groups
                elif bank_format == 'santander':
                    date_str, description, amount_str = groups
                elif bank_format == 'btg':
                    date_str, description, amount_str = groups
                elif bank_format == 'unicred':
                    date_str, description, amount_str = groups
                elif bank_format == 'c6':
                    date_str, description, amount_str = groups
                
                # Processar data
                transaction_date = self.parse_date(date_str, patterns['date_format'], current_year)
                
                # Processar valor
                amount = self.parse_currency(amount_str)
                
                # Verificar se é parcelado
                is_installment = False
                current_installment = 1
                total_installments = 1
                
                installment_match = re.search(patterns['installment'], description, re.IGNORECASE)
                if installment_match:
                    is_installment = True
                    current_installment = int(installment_match.group(1))
                    total_installments = int(installment_match.group(2))
                
                # Categorizar transação
                category = self.categorize_transaction(description, bank_format)
                
                transaction = {
                    'data': transaction_date.strftime('%d/%m/%Y'),
                    'descricao': description.strip(),
                    'parcelado': 'Sim' if is_installment else 'Não',
                    'parcela_atual': current_installment if is_installment else None,
                    'parcela_total': total_installments if is_installment else None,
                    'valor': amount,
                    'categoria': category,
                    'banco': bank_format
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                print(f"Erro ao processar transação: {e}")
                continue
        
        return transactions

    def analyze_pdf(self, pdf_path):
        """Analisa um PDF de fatura e retorna as transações extraídas"""
        try:
            # Extrair texto do PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                raise Exception("Não foi possível extrair texto do PDF")
            
            # Detectar formato do banco
            bank_format = self.detect_bank_format(text)
            
            # Extrair transações
            transactions = self.extract_transactions(text, bank_format)
            
            if not transactions:
                raise Exception("Nenhuma transação encontrada no PDF")
            
            return {
                'banco_detectado': bank_format,
                'total_transacoes': len(transactions),
                'transacoes': transactions
            }
            
        except Exception as e:
            raise Exception(f"Erro ao analisar PDF: {str(e)}")

    def get_supported_formats(self):
        """Retorna os formatos de banco suportados"""
        return list(self.patterns.keys())