#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pdf_analyzer import PDFAnalyzer
from data_handler import DataHandler
from monthly_comparison import MonthlyComparison
from file_validator import FileValidator
from transaction_manager import TransactionManager

class CLIAnalyzer:
    def __init__(self):
        self.analyzer = PDFAnalyzer()
        self.data_handler = DataHandler()
        self.comparator = MonthlyComparison(data_handler=self.data_handler)
        self.file_validator = FileValidator()
        self.transaction_manager = TransactionManager()
    
    def show_menu(self):
        """Mostra o menu principal"""
        print("\n" + "="*60)
        print("🏦 ANALISADOR DE PDFs DE CARTÃO DE CRÉDITO")
        print("="*60)
        print("1. Analisar PDF")
        print("2. Ver transações salvas")
        print("3. Estatísticas")
        print("4. Comparativo 6 meses")
        print("5. Exportar para MongoDB (formato)")
        print("6. Gerenciar transações (editar categorias)")
        print("7. Validar arquivos PDF")
        print("8. Sair")
        print("-"*60)
    
    def analyze_pdf(self):
        """Analisa um PDF"""
        print("\n📄 ANÁLISE DE PDF")
        print("-"*30)
        
        # Usar validador de arquivos
        print("1. Digitar caminho manualmente")
        print("2. Seleção interativa de arquivo")
        
        choice = input("Escolha uma opção (1-2): ").strip()
        
        if choice == '2':
            pdf_path = self.file_validator.interactive_file_selection()
            if not pdf_path:
                return
        else:
            pdf_path = input("Digite o caminho do arquivo PDF: ").strip()
            if not pdf_path:
                print("❌ Caminho não fornecido")
                return
        
        # Validar arquivo
        validation = self.file_validator.validate_file_path(pdf_path)
        if not validation['valid']:
            print(f"❌ {validation['error']}")
            if validation['suggestions']:
                print("💡 Sugestões:")
                for suggestion in validation['suggestions']:
                    print(f"   - {suggestion}")
            return
        
        try:
            print("🔄 Analisando PDF...")
            result = self.analyzer.analyze_pdf(pdf_path)
            
            # Mostrar resultados
            print(f"\n✅ Análise concluída!")
            print(f"🏦 Banco detectado: {result['banco_detectado'].upper()}")
            print(f"📈 Total de transações: {result['total_transacoes']}")
            
            # Mostrar transações
            print(f"\n💳 TRANSAÇÕES ENCONTRADAS:")
            print("-"*50)
            
            for i, trans in enumerate(result['transacoes'], 1):
                print(f"{i:2d}. {trans['data']} - {trans['descricao']}")
                print(f"     💰 Valor: R$ {trans['valor']:.2f}")
                print(f"     🏷️  Categoria: {trans['categoria']}")
                print(f"     🏦 Banco: {trans['banco']}")
                
                if trans['parcelado'] == 'Sim':
                    print(f"     📅 Parcelado: {trans['parcela_atual']}/{trans['parcela_total']}")
                else:
                    print(f"     📅 Parcelado: Não")
                print()
            
            # Perguntar se quer salvar
            save = input("💾 Deseja salvar estas transações? (s/n): ").lower().strip()
            
            if save in ['s', 'sim', 'y', 'yes']:
                self.save_transactions(result['transacoes'])
            
        except Exception as e:
            print(f"❌ Erro ao analisar PDF: {e}")
    
    def save_transactions(self, transactions):
        """Salva transações"""
        print("\n💾 SALVAR TRANSAÇÕES")
        print("-"*30)
        
        # Solicitar origem do cartão
        print("Origens disponíveis:")
        print("1. Cartão Principal")
        print("2. Cartão Adicional") 
        print("3. Cartão Corporativo")
        print("4. Outro")
        
        choice = input("Escolha a origem (1-4): ").strip()
        
        origins = {
            '1': 'Cartão Principal',
            '2': 'Cartão Adicional',
            '3': 'Cartão Corporativo',
            '4': 'Outro'
        }
        
        card_origin = origins.get(choice, 'Cartão Principal')
        
        if choice == '4':
            card_origin = input("Digite a origem personalizada: ").strip() or 'Outro'
        
        # Perguntar sobre duplicados
        remove_duplicates = input("Remover duplicados? (s/n): ").lower().strip() in ['s', 'sim', 'y', 'yes']
        
        try:
            print("🔄 Salvando transações...")
            result = self.data_handler.save_transactions(transactions, card_origin, remove_duplicates)
            
            if result['success']:
                print(f"✅ {result['message']}")
                print(f"📊 Estatísticas:")
                print(f"   • Salvas: {result['saved']}")
                print(f"   • Duplicadas: {result['duplicates']}")
                print(f"   • Erros: {result['errors']}")
            else:
                print(f"❌ {result['message']}")
                
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
    
    def show_saved_transactions(self):
        """Mostra transações salvas"""
        print("\n📋 TRANSAÇÕES SALVAS")
        print("-"*30)
        
        try:
            count = self.data_handler.get_transactions_count()
            print(f"Total de transações salvas: {count}")
            
            if count == 0:
                print("Nenhuma transação salva ainda.")
                return
            
            # Mostrar últimas 10 transações
            transactions = self.data_handler.get_all_transactions(limit=10)
            
            print(f"\n📄 Últimas {len(transactions)} transações:")
            print("-"*50)
            
            for i, trans in enumerate(transactions, 1):
                print(f"{i:2d}. {trans['data']} - {trans['descricao']}")
                print(f"     💰 Valor: R$ {trans['valor']:.2f}")
                print(f"     🏷️  Categoria: {trans['categoria']}")
                print(f"     🏦 Banco: {trans['banco']}")
                print(f"     📍 Origem: {trans.get('origem_cartao', 'N/A')}")
                print()
                
        except Exception as e:
            print(f"❌ Erro ao carregar transações: {e}")
    
    def show_statistics(self):
        """Mostra estatísticas"""
        print("\n📊 ESTATÍSTICAS")
        print("-"*30)
        
        try:
            stats = self.data_handler.get_statistics()
            
            print(f"📈 Total de transações: {stats['total']}")
            print(f"💰 Valor total: R$ {stats['valor_total']:.2f}")
            print(f"📅 Transações parceladas: {stats['parceladas']}")
            
            print(f"\n🏦 Por banco:")
            for banco, count in stats['por_banco'].items():
                print(f"   • {banco}: {count}")
            
            print(f"\n🏷️  Por categoria:")
            for categoria, count in stats['por_categoria'].items():
                print(f"   • {categoria}: {count}")
            
            print(f"\n📍 Por origem:")
            for origem, count in stats['por_origem'].items():
                print(f"   • {origem}: {count}")
                
        except Exception as e:
            print(f"❌ Erro ao carregar estatísticas: {e}")
    
    def monthly_comparison(self):
        """Gera comparativo dos últimos 6 meses"""
        print("\n📊 COMPARATIVO DOS ÚLTIMOS 6 MESES")
        print("-"*40)
        
        # Perguntar sobre origem do cartão
        print("Origens disponíveis:")
        print("1. Todos os cartões")
        print("2. Cartão Principal")
        print("3. Cartão Adicional")
        print("4. Cartão Corporativo")
        print("5. Outro")
        
        choice = input("Escolha a origem (1-5): ").strip()
        
        origins = {
            '1': None,
            '2': 'Cartão Principal',
            '3': 'Cartão Adicional',
            '4': 'Cartão Corporativo',
            '5': 'Outro'
        }
        
        card_origin = origins.get(choice)
        
        if choice == '5':
            card_origin = input("Digite a origem personalizada: ").strip() or 'Outro'
        
        try:
            print("🔄 Gerando relatório comparativo...")
            report = self.comparator.generate_comparison_report(card_origin)
            
            # Mostrar resumo executivo
            print(f"\n📈 RESUMO EXECUTIVO - {report['period'].upper()}")
            print("="*50)
            summary = report['summary']
            print(f"💰 Valor total: R$ {summary['total_value_6_months']:.2f}")
            print(f"📊 Média mensal: R$ {summary['average_monthly_value']:.2f}")
            print(f"💳 Total de transações: {summary['total_transactions_6_months']}")
            print(f"📅 Parcelamentos: {summary['total_installments_6_months']} ({summary['installment_percentage']:.1f}%)")
            print(f"📆 Meses com atividade: {summary['months_with_activity']}")
            
            # Mostrar dados mensais
            print(f"\n📅 DADOS MENSАIS:")
            print("-"*30)
            for month, stats in report['monthly_data'].items():
                if stats['total_transactions'] > 0:
                    print(f"{month}: R$ {stats['total_value']:.2f} ({stats['total_transactions']} transações)")
            
            # Mostrar insights
            print(f"\n💡 INSIGHTS:")
            for insight in report['insights']:
                print(f"   {insight}")
            
            # Perguntar se quer exportar
            export = input("\n💾 Deseja exportar o relatório? (s/n): ").lower().strip()
            
            if export in ['s', 'sim', 'y', 'yes']:
                filename = self.comparator.export_comparison_report(report)
                if filename:
                    print(f"✅ Relatório salvo em: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar comparativo: {e}")
    
    def export_mongodb_format(self):
        """Exporta no formato para MongoDB"""
        print("\n📤 EXPORTAR PARA MONGODB")
        print("-"*30)
        
        try:
            transactions = self.data_handler.export_to_mongodb_format()
            
            if not transactions:
                print("Nenhuma transação para exportar.")
                return
            
            # Salvar em arquivo JSON
            filename = "transacoes_mongodb.json"
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {len(transactions)} transações exportadas para {filename}")
            print("📋 Formato pronto para importação no MongoDB")
            
        except Exception as e:
            print(f"❌ Erro ao exportar: {e}")
    
    def manage_transactions(self):
        """Gerencia transações (editar categorias)"""
        print("\n🔧 GERENCIAMENTO DE TRANSAÇÕES")
        print("-"*40)
        
        # Listar transações recentes
        transactions = self.transaction_manager.list_transactions(limit=20)
        
        if not transactions:
            print("❌ Nenhuma transação encontrada")
            return
        
        print(f"\n📊 {len(transactions)} transações recentes:")
        print("-" * 80)
        
        for i, transaction in enumerate(transactions, 1):
            print(f"{i:2d}. {transaction.get('data', 'N/A')} | "
                  f"{transaction.get('descricao', 'N/A')[:40]:<40} | "
                  f"R$ {transaction.get('valor', 0):>8.2f} | "
                  f"{transaction.get('categoria', 'N/A'):<12} | "
                  f"Hash: {transaction.get('transaction_hash', 'N/A')[:8]}...")
        
        print("\nOpções:")
        print("1. Buscar transação por descrição")
        print("2. Editar categoria por hash")
        print("3. Voltar ao menu principal")
        
        choice = input("Escolha uma opção (1-3): ").strip()
        
        if choice == '1':
            search_term = input("Termo de busca: ").strip()
            if search_term:
                results = self.transaction_manager.search_transactions(search_term)
                if results:
                    print(f"\n🔍 {len(results)} transações encontradas:")
                    for i, transaction in enumerate(results, 1):
                        print(f"{i:2d}. {transaction.get('data', 'N/A')} | "
                              f"{transaction.get('descricao', 'N/A')[:40]:<40} | "
                              f"R$ {transaction.get('valor', 0):>8.2f} | "
                              f"{transaction.get('categoria', 'N/A'):<12} | "
                              f"Hash: {transaction.get('transaction_hash', 'N/A')[:8]}...")
                else:
                    print("❌ Nenhuma transação encontrada")
        
        elif choice == '2':
            transaction_hash = input("Hash da transação: ").strip()
            if transaction_hash:
                transaction = self.transaction_manager.get_transaction_by_hash(transaction_hash)
                if transaction:
                    print(f"\n📄 Transação encontrada:")
                    print(f"Data: {transaction.get('data', 'N/A')}")
                    print(f"Descrição: {transaction.get('descricao', 'N/A')}")
                    print(f"Valor: R$ {transaction.get('valor', 0):.2f}")
                    print(f"Categoria atual: {transaction.get('categoria', 'N/A')}")
                    
                    categories = ['alimentacao', 'transporte', 'saude', 'compras', 'servicos', 'outros']
                    print(f"\nCategorias disponíveis: {', '.join(categories)}")
                    
                    new_category = input("Nova categoria: ").strip().lower()
                    if new_category in categories:
                        result = self.transaction_manager.update_transaction_category(transaction_hash, new_category)
                        if result['success']:
                            print(f"✅ {result['message']}")
                        else:
                            print(f"❌ {result['message']}")
                    else:
                        print("❌ Categoria inválida")
                else:
                    print("❌ Transação não encontrada")
    
    def validate_files(self):
        """Valida arquivos PDF"""
        print("\n🔍 VALIDAÇÃO DE ARQUIVOS PDF")
        print("-"*40)
        
        # Listar PDFs disponíveis
        pdf_files = self.file_validator.list_available_pdfs()
        
        if not pdf_files:
            print("❌ Nenhum arquivo PDF encontrado no diretório atual")
            return
        
        print(f"\n📄 {len(pdf_files)} arquivos PDF encontrados:")
        print("-" * 60)
        
        for file_info in pdf_files:
            validation = self.file_validator.validate_file_path(file_info['path'])
            status = "✅" if validation['valid'] else "❌"
            print(f"{status} {file_info['name']:<30} ({file_info['size_mb']:.1f}MB)")
            if not validation['valid']:
                print(f"   Erro: {validation['error']}")
    
    def run(self):
        """Executa o programa principal"""
        while True:
            self.show_menu()
            
            try:
                choice = input("Escolha uma opção (1-8): ").strip()
                
                if choice == '1':
                    self.analyze_pdf()
                elif choice == '2':
                    self.show_saved_transactions()
                elif choice == '3':
                    self.show_statistics()
                elif choice == '4':
                    self.monthly_comparison()
                elif choice == '5':
                    self.export_mongodb_format()
                elif choice == '6':
                    self.manage_transactions()
                elif choice == '7':
                    self.validate_files()
                elif choice == '8':
                    print("👋 Até logo!")
                    break
                else:
                    print("❌ Opção inválida. Tente novamente.")
                    
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    app = CLIAnalyzer()
    app.run()

if __name__ == "__main__":
    main()
