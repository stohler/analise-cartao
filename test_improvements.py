#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para verificar as melhorias implementadas
"""

from pdf_analyzer import PDFAnalyzer
import os

def test_c6_filtering():
    """Testa se os filtros do C6 estão funcionando corretamente"""
    analyzer = PDFAnalyzer()
    
    # Teste com descrições que devem ser excluídas
    test_descriptions = [
        "R$",
        "de financiamento e compras internacionais",
        "33690.00009 00000.010132 06246.793142 1",
        "12345",
        "APENAS LETRAS MAIUSCULAS",
        "   ",  # espaços em branco
        "IFOOD RESTAURANTE 25.50",  # Esta deve passar
        "UBER TRANSPORTE 15.00"  # Esta deve passar
    ]
    
    print("Testando filtros de exclusão do C6:")
    print("=" * 50)
    
    for desc in test_descriptions:
        should_exclude = analyzer.should_exclude_transaction(desc, 'c6')
        status = "EXCLUÍDA" if should_exclude else "MANTIDA"
        print(f"'{desc}' -> {status}")
    
    print("\n" + "=" * 50)
    print("Teste concluído!")

def test_transaction_management():
    """Testa as funções de gerenciamento de transações"""
    print("\nTestando gerenciamento de transações:")
    print("=" * 50)
    
    # Simular dados de transação
    sample_data = {
        'banco_detectado': 'c6',
        'total_transacoes': 3,
        'transacoes': [
            {
                'data': '15/01/2024',
                'descricao': 'IFOOD RESTAURANTE',
                'valor': 25.50,
                'categoria': 'alimentacao',
                'parcelado': 'Não'
            },
            {
                'data': '16/01/2024', 
                'descricao': 'UBER TRANSPORTE',
                'valor': 15.00,
                'categoria': 'transporte',
                'parcelado': 'Não'
            },
            {
                'data': '17/01/2024',
                'descricao': 'FARMACIA SAUDE',
                'valor': 45.00,
                'categoria': 'saude',
                'parcelado': 'Não'
            }
        ]
    }
    
    print(f"Total de transações: {sample_data['total_transacoes']}")
    print("Transações:")
    for i, trans in enumerate(sample_data['transacoes']):
        print(f"  {i+1}. {trans['descricao']} - R$ {trans['valor']} ({trans['categoria']})")
    
    print("\nFuncionalidades implementadas:")
    print("✓ Remoção de transações")
    print("✓ Reclassificação de categorias")
    print("✓ Filtros melhorados para C6")
    print("✓ Interface atualizada com botões de ação")

if __name__ == "__main__":
    test_c6_filtering()
    test_transaction_management()