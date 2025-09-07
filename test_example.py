#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pdf_analyzer import PDFAnalyzer
from data_handler import DataHandler

def test_complete_workflow():
    """Testa o fluxo completo de análise e armazenamento"""
    
    print("🧪 TESTE COMPLETO DO SISTEMA")
    print("="*50)
    
    # Inicializar componentes
    analyzer = PDFAnalyzer()
    data_handler = DataHandler()
    
    # Simular texto de PDF do Nubank
    nubank_text = """
    Nubank
    Fatura do Cartão de Crédito
    Período: 01/06/2024 a 30/06/2024
    
    29 JUN •••• 0652 Disal Ecommerce - Parcela 7/7 R$ 51,82
    29 JUN •••• 5787 Doctoraliabrazil - Parcela 3/12 R$ 349,00
    29 JUN •••• 2565 Sn Consultoria Medicin - Parcela 4/4 R$ 1.075,00
    07 JUL •••• 2557 Amazon Digital R$ 27,53
    07 JUL •••• 0652 Asa*Peg Ai Loja Inteli R$ 16,38
    08 JUL •••• 2565 Ifd*Napedra Pizzaria J R$ 106,99
    08 JUL •••• 2565 Subadq *Amadeirado Res R$ 39,56
    """
    
    print("1. 📄 Analisando texto simulado do Nubank...")
    
    try:
        # Analisar texto
        result = analyzer.analyze_pdf_text(nubank_text)
        
        print(f"   ✅ Banco detectado: {result['banco_detectado']}")
        print(f"   ✅ Transações encontradas: {result['total_transacoes']}")
        
        # Mostrar algumas transações
        print("\n   📋 Primeiras 3 transações:")
        for i, trans in enumerate(result['transacoes'][:3], 1):
            print(f"      {i}. {trans['data']} - {trans['descricao']} - R$ {trans['valor']}")
        
        print("\n2. 💾 Salvando transações...")
        
        # Salvar transações
        save_result = data_handler.save_transactions(
            result['transacoes'], 
            "Cartão Principal", 
            remove_duplicates=True
        )
        
        print(f"   ✅ {save_result['message']}")
        print(f"   📊 Salvas: {save_result['saved']}, Duplicadas: {save_result['duplicates']}")
        
        print("\n3. 📊 Verificando estatísticas...")
        
        # Mostrar estatísticas
        stats = data_handler.get_statistics()
        print(f"   📈 Total: {stats['total']} transações")
        print(f"   💰 Valor total: R$ {stats['valor_total']:.2f}")
        print(f"   📅 Parceladas: {stats['parceladas']}")
        
        print("\n   🏦 Por banco:")
        for banco, count in stats['por_banco'].items():
            print(f"      • {banco}: {count}")
        
        print("\n   🏷️  Por categoria:")
        for categoria, count in stats['por_categoria'].items():
            print(f"      • {categoria}: {count}")
        
        print("\n4. 🔄 Testando duplicados...")
        
        # Tentar salvar as mesmas transações novamente
        duplicate_result = data_handler.save_transactions(
            result['transacoes'], 
            "Cartão Principal", 
            remove_duplicates=True
        )
        
        print(f"   ✅ {duplicate_result['message']}")
        print(f"   📊 Salvas: {duplicate_result['saved']}, Duplicadas: {duplicate_result['duplicates']}")
        
        print("\n5. 📤 Exportando para MongoDB...")
        
        # Exportar para formato MongoDB
        mongo_data = data_handler.export_to_mongodb_format()
        print(f"   ✅ {len(mongo_data)} transações prontas para MongoDB")
        
        # Mostrar exemplo de transação exportada
        if mongo_data:
            example = mongo_data[0]
            print(f"   📋 Exemplo de transação exportada:")
            print(f"      Data: {example['data']}")
            print(f"      Descrição: {example['descricao']}")
            print(f"      Valor: R$ {example['valor']}")
            print(f"      Origem: {example['origem_cartao']}")
            print(f"      Hash: {example['transaction_hash'][:16]}...")
        
        print("\n" + "="*50)
        print("🎉 TESTE COMPLETO FINALIZADO COM SUCESSO!")
        print("✅ Todas as funcionalidades estão operacionais")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        return False

if __name__ == "__main__":
    test_complete_workflow()
