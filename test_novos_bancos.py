#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Script de Teste para Novos Bancos
====================================

Este script ajuda a validar PDFs de bancos que ainda não são suportados
(BTG Pactual, Unicred, C6 Bank) e identificar padrões para implementação.

Uso:
    python test_novos_bancos.py caminho/para/fatura.pdf
"""

import sys
import os
import re
from pdf_analyzer import PDFAnalyzer

class NovosBancosAnalyzer:
    def __init__(self):
        self.analyzer = PDFAnalyzer()
        
        # Padrões experimentais para novos bancos
        self.experimental_patterns = {
            'btg': [
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                r'(\d{2}/\d{2})\s+(.+?)\s+(R\$\s*[\d.,]+)',
            ],
            'unicred': [
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)',
                r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)',
            ],
            'c6': [
                r'(\d{2}/\d{2})\s+(.+?)\s+(R\$\s*[\d.,]+)',
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(R\$\s*[\d.,]+)',
            ]
        }
        
        # Identificadores de banco
        self.bank_identifiers = {
            'btg': ['btg', 'btg pactual', 'banco btg'],
            'unicred': ['unicred', 'cooperativa', 'sicoob'],
            'c6': ['c6', 'c6 bank', 'banco c6']
        }

    def detect_new_bank(self, text):
        """Tenta detectar qual novo banco é baseado no texto"""
        text_lower = text.lower()
        
        for bank, identifiers in self.bank_identifiers.items():
            for identifier in identifiers:
                if identifier in text_lower:
                    return bank
        
        return None

    def extract_sample_lines(self, text, max_lines=20):
        """Extrai linhas que podem conter transações"""
        lines = text.split('\n')
        potential_transactions = []
        
        # Padrões gerais que podem indicar transações
        transaction_patterns = [
            r'\d{2}/\d{2}',  # Data DD/MM
            r'\d{2}/\d{2}/\d{4}',  # Data DD/MM/YYYY
            r'R\$\s*\d',  # Valor com R$
            r'\d+,\d{2}',  # Valor decimal
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Verificar se linha contém padrões de transação
            matches = 0
            for pattern in transaction_patterns:
                if re.search(pattern, line):
                    matches += 1
            
            if matches >= 2:  # Linha tem pelo menos 2 padrões (ex: data + valor)
                potential_transactions.append(line)
                
            if len(potential_transactions) >= max_lines:
                break
        
        return potential_transactions

    def test_patterns_on_text(self, text, bank_name):
        """Testa padrões experimentais no texto"""
        if bank_name not in self.experimental_patterns:
            return []
        
        results = []
        patterns = self.experimental_patterns[bank_name]
        
        for i, pattern in enumerate(patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            pattern_results = []
            
            for match in matches:
                groups = match.groups()
                if len(groups) >= 3:
                    pattern_results.append({
                        'linha_original': match.group(0),
                        'data': groups[0],
                        'descricao': groups[1].strip(),
                        'valor': groups[2]
                    })
            
            if pattern_results:
                results.append({
                    'padrao_numero': i + 1,
                    'regex': pattern,
                    'transacoes_encontradas': len(pattern_results),
                    'exemplos': pattern_results[:5]  # Primeiros 5 exemplos
                })
        
        return results

    def analyze_new_bank_pdf(self, pdf_path):
        """Analisa PDF de banco novo e gera relatório"""
        print(f"🔍 ANALISANDO PDF: {os.path.basename(pdf_path)}")
        print("=" * 60)
        
        try:
            # Extrair texto
            text = self.analyzer.extract_text_from_pdf(pdf_path)
            if not text.strip():
                print("❌ Erro: Não foi possível extrair texto do PDF")
                return
            
            print(f"✅ Texto extraído com sucesso ({len(text)} caracteres)")
            
            # Detectar banco
            detected_bank = self.detect_new_bank(text)
            if detected_bank:
                print(f"🏦 Banco detectado: {detected_bank.upper()}")
            else:
                print("🤔 Banco não identificado automaticamente")
                print("📝 Identifique manualmente baseado no conteúdo")
            
            print("\n" + "=" * 60)
            
            # Extrair linhas potenciais
            sample_lines = self.extract_sample_lines(text)
            print(f"📋 LINHAS POTENCIAIS DE TRANSAÇÃO ({len(sample_lines)} encontradas):")
            print("-" * 60)
            
            for i, line in enumerate(sample_lines[:15], 1):
                print(f"{i:2d}. {line}")
            
            if len(sample_lines) > 15:
                print(f"    ... e mais {len(sample_lines) - 15} linhas")
            
            # Testar padrões experimentais se banco foi detectado
            if detected_bank:
                print(f"\n🧪 TESTANDO PADRÕES PARA {detected_bank.upper()}:")
                print("-" * 60)
                
                pattern_results = self.test_patterns_on_text(text, detected_bank)
                
                if pattern_results:
                    for result in pattern_results:
                        print(f"\n📊 Padrão {result['padrao_numero']}: {result['transacoes_encontradas']} transações")
                        print(f"   Regex: {result['regex']}")
                        print("   Exemplos:")
                        
                        for exemplo in result['exemplos']:
                            print(f"     • {exemplo['data']} | {exemplo['descricao'][:30]}... | {exemplo['valor']}")
                else:
                    print("❌ Nenhum padrão experimental funcionou")
                    print("💡 Será necessário criar padrões específicos")
            
            # Sugestões para implementação
            print(f"\n💡 SUGESTÕES PARA IMPLEMENTAÇÃO:")
            print("-" * 60)
            print("1. 📄 Analise as linhas potenciais acima")
            print("2. 🔍 Identifique o padrão comum de:")
            print("   - Formato de data (DD/MM, DD/MM/YYYY, etc.)")
            print("   - Posição da descrição")
            print("   - Formato do valor (R$ X,XX ou X,XX)")
            print("   - Formato de parcelas (se houver)")
            print("3. 📝 Crie regex baseado no padrão identificado")
            print("4. 🧪 Teste com este script")
            print("5. 📤 Envie feedback com os padrões encontrados")
            
            # Instruções para contribuição
            print(f"\n📤 COMO CONTRIBUIR:")
            print("-" * 60)
            print("1. 📋 Copie as linhas potenciais mostradas acima")
            print("2. 🏦 Identifique qual banco é (BTG/Unicred/C6)")
            print("3. 📝 Descreva o padrão que você vê")
            print("4. 📧 Envie via GitHub Issues com:")
            print("   - PDF anonimizado")
            print("   - Saída deste script")
            print("   - Padrões identificados")
            
        except Exception as e:
            print(f"❌ Erro ao analisar PDF: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("🧪 Teste de Novos Bancos")
        print("=" * 30)
        print("Uso: python test_novos_bancos.py <caminho_do_pdf>")
        print("\nExemplo:")
        print("  python test_novos_bancos.py fatura_btg.pdf")
        print("  python test_novos_bancos.py fatura_unicred.pdf")
        print("  python test_novos_bancos.py fatura_c6.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Erro: Arquivo não encontrado: {pdf_path}")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ Erro: Arquivo deve ser um PDF: {pdf_path}")
        return
    
    analyzer = NovosBancosAnalyzer()
    analyzer.analyze_new_bank_pdf(pdf_path)
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print("1. Leia o arquivo CONTRIBUIR_NOVOS_BANCOS.md")
    print("2. Remova informações pessoais do PDF")
    print("3. Envie o PDF + saída deste script")
    print("4. Aguarde implementação do suporte!")

if __name__ == "__main__":
    main()