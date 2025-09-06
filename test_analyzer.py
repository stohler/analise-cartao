#!/usr/bin/env python3
"""
Script de teste para o analisador de PDF de faturas
"""

from pdf_analyzer import PDFAnalyzer
import json

def test_analyzer():
    """Testa o analisador de PDF com texto de exemplo"""
    
    print("🧪 Testando Analisador de PDF de Faturas")
    print("=" * 50)
    
    # Inicializar analisador
    analyzer = PDFAnalyzer()
    
    # Texto de exemplo do Nubank
    sample_nubank_text = """
    Nu Pagamentos S.A.
    Fatura do Cartão de Crédito
    
    12/01  UBER TRIP                    R$ 15,50
    15/01  IFOOD DELIVERY               R$ 45,80
    18/01  POSTO BR COMBUSTIVEL         R$ 120,00
    20/01  FARMACIA DROGASIL            R$ 28,90
    22/01  NETFLIX 1/1                  R$ 39,90
    25/01  AMAZON COMPRA 2/3            R$ 89,90
    28/01  RESTAURANTE OUTBACK          R$ 178,50
    """
    
    # Texto de exemplo do Itaú
    sample_itau_text = """
    BANCO ITAÚ S.A.
    Fatura do Cartão
    
    12/01/2024  UBER VIAGEM                    45,50
    15/01/2024  MAGAZINE LUIZA                 299,90
    18/01/2024  POSTO SHELL PARC 1/2           89,90
    20/01/2024  FARMACIA PACHECO               67,80
    22/01/2024  SPOTIFY PREMIUM                19,90
    """
    
    print("🔍 Testando detecção de formato...")
    
    # Testar detecção Nubank
    format_nubank = analyzer.detect_bank_format(sample_nubank_text)
    print(f"Formato detectado Nubank: {format_nubank}")
    
    # Testar detecção Itaú
    format_itau = analyzer.detect_bank_format(sample_itau_text)
    print(f"Formato detectado Itaú: {format_itau}")
    
    print("\n📊 Testando extração de transações...")
    
    # Testar extração Nubank
    transactions_nubank = analyzer.extract_transactions(sample_nubank_text, format_nubank)
    print(f"\nTransações Nubank encontradas: {len(transactions_nubank)}")
    for i, trans in enumerate(transactions_nubank[:3], 1):  # Mostrar apenas 3 primeiras
        print(f"  {i}. {trans['data']} - {trans['descricao'][:30]}... - R$ {trans['valor']:.2f} - {trans['categoria']}")
    
    # Testar extração Itaú
    transactions_itau = analyzer.extract_transactions(sample_itau_text, format_itau)
    print(f"\nTransações Itaú encontradas: {len(transactions_itau)}")
    for i, trans in enumerate(transactions_itau[:3], 1):  # Mostrar apenas 3 primeiras
        print(f"  {i}. {trans['data']} - {trans['descricao'][:30]}... - R$ {trans['valor']:.2f} - {trans['categoria']}")
    
    print("\n🏷️ Testando categorização...")
    
    test_descriptions = [
        "UBER TRIP SAO PAULO",
        "IFOOD DELIVERY PIZZA",
        "FARMACIA DROGASIL",
        "NETFLIX STREAMING",
        "POSTO BR COMBUSTIVEL",
        "AMAZON MARKETPLACE",
        "RESTAURANTE OUTBACK"
    ]
    
    for desc in test_descriptions:
        category = analyzer.categorize_transaction(desc, 'nubank')
        print(f"  '{desc}' → {category}")
    
    print("\n💰 Testando conversão de moeda...")
    
    test_currencies = [
        "R$ 15,50",
        "45,80",
        "R$ 1.234,56",
        "2.500,00",
        "R$ 89,90"
    ]
    
    for curr in test_currencies:
        value = analyzer.parse_currency(curr)
        print(f"  '{curr}' → {value:.2f}")
    
    print("\n✅ Teste concluído!")
    print("\n🎯 Formatos suportados:")
    for fmt in analyzer.get_supported_formats():
        print(f"  • {fmt.upper()}")

if __name__ == "__main__":
    test_analyzer()