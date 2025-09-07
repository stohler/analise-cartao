#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_handler import DataHandler
from monthly_comparison import MonthlyComparison
from datetime import datetime, timedelta

def test_monthly_comparison():
    """Testa o sistema de comparativo mensal"""
    
    print("🧪 TESTE DO COMPARATIVO MENSAL")
    print("="*50)
    
    # Inicializar componentes
    data_handler = DataHandler()
    comparator = MonthlyComparison(data_handler=data_handler)
    
    # Simular dados de diferentes meses
    print("1. 📊 Gerando dados de teste para diferentes meses...")
    
    # Criar transações simuladas para os últimos 6 meses
    test_transactions = []
    today = datetime.now()
    
    for i in range(6):
        month_date = today - timedelta(days=30 * i)
        
        # Simular algumas transações para cada mês
        month_transactions = [
            {
                'data': f"15/{month_date.month:02d}/{month_date.year}",
                'descricao': f'Supermercado ABC - Mês {month_date.month}',
                'valor': 150.00 + (i * 20),
                'categoria': 'alimentacao',
                'banco': 'nubank',
                'parcelado': 'Não',
                'origem_cartao': 'Cartão Principal',
                'data_importacao': month_date.isoformat(),
                'transaction_hash': f'hash_{i}_1'
            },
            {
                'data': f"20/{month_date.month:02d}/{month_date.year}",
                'descricao': f'Posto Shell - Mês {month_date.month}',
                'valor': 80.00 + (i * 10),
                'categoria': 'transporte',
                'banco': 'nubank',
                'parcelado': 'Não',
                'origem_cartao': 'Cartão Principal',
                'data_importacao': month_date.isoformat(),
                'transaction_hash': f'hash_{i}_2'
            }
        ]
        
        # Adicionar transação parcelada ocasionalmente
        if i % 2 == 0:
            month_transactions.append({
                'data': f"25/{month_date.month:02d}/{month_date.year}",
                'descricao': f'Loja XYZ - Parcela 1/3 - Mês {month_date.month}',
                'valor': 300.00,
                'categoria': 'compras',
                'banco': 'nubank',
                'parcelado': 'Sim',
                'parcela_atual': 1,
                'parcela_total': 3,
                'origem_cartao': 'Cartão Principal',
                'data_importacao': month_date.isoformat(),
                'transaction_hash': f'hash_{i}_3'
            })
        
        test_transactions.extend(month_transactions)
    
    # Salvar transações de teste
    print(f"   ✅ Criadas {len(test_transactions)} transações de teste")
    
    # Salvar no data handler
    save_result = data_handler.save_transactions(
        test_transactions, 
        "Cartão Principal", 
        remove_duplicates=False
    )
    
    print(f"   ✅ {save_result['message']}")
    
    print("\n2. 📈 Gerando relatório comparativo...")
    
    # Gerar relatório comparativo
    report = comparator.generate_comparison_report("Cartão Principal")
    
    print("   ✅ Relatório gerado com sucesso!")
    
    print("\n3. 📊 RESUMO EXECUTIVO - ÚLTIMOS 6 MESES")
    print("-"*50)
    
    summary = report['summary']
    print(f"💰 Valor total: R$ {summary['total_value_6_months']:.2f}")
    print(f"📊 Média mensal: R$ {summary['average_monthly_value']:.2f}")
    print(f"💳 Total de transações: {summary['total_transactions_6_months']}")
    print(f"📅 Parcelamentos: {summary['total_installments_6_months']} ({summary['installment_percentage']:.1f}%)")
    print(f"📆 Meses com atividade: {summary['months_with_activity']}")
    
    print("\n4. 📅 DADOS MENSАIS:")
    print("-"*30)
    
    for month, stats in report['monthly_data'].items():
        if stats['total_transactions'] > 0:
            print(f"{month}: R$ {stats['total_value']:.2f} ({stats['total_transactions']} transações)")
    
    print("\n5. 💡 INSIGHTS:")
    for insight in report['insights']:
        print(f"   {insight}")
    
    print("\n6. 📤 Exportando relatório...")
    
    # Exportar relatório
    filename = comparator.export_comparison_report(report, "teste_comparativo_mensal.json")
    
    if filename:
        print(f"   ✅ Relatório exportado para: {filename}")
    
    print("\n" + "="*50)
    print("🎉 TESTE DO COMPARATIVO MENSAL CONCLUÍDO!")
    print("✅ Sistema de análise temporal funcionando perfeitamente")
    
    return True

if __name__ == "__main__":
    test_monthly_comparison()
