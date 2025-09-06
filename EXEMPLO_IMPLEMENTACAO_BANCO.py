# 🏦 EXEMPLO: Como Implementar Suporte a Novos Bancos
# Este arquivo mostra como adicionar BTG, Unicred e C6 no sistema

# ==========================================
# 1. ADICIONAR PADRÕES NO pdf_analyzer.py
# ==========================================

# Exemplo de como os padrões seriam adicionados:

NOVOS_PADROES = {
    # BTG PACTUAL - Exemplo baseado em padrões típicos
    'btg': {
        'transaction': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(R\$\s*[\d.,]+)',
        'installment': r'(\d+)/(\d+)',  # Formato: 2/6
        'date_format': '%d/%m/%Y',
        'currency': r'R\$\s*([\d.,]+)',
        'categories': {
            'alimentacao': ['restaurante', 'delivery', 'ifood', 'lanche'],
            'transporte': ['uber', '99', 'posto', 'combustivel', 'taxi'],
            'saude': ['farmacia', 'drogaria', 'hospital', 'clinica'],
            'compras': ['magazine', 'loja', 'shopping', 'mercado'],
            'servicos': ['netflix', 'spotify', 'streaming', 'assinatura']
        }
    },
    
    # UNICRED - Exemplo baseado em padrões de cooperativas
    'unicred': {
        'transaction': r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)',
        'installment': r'PARC\s*(\d+)/(\d+)',  # Formato: PARC 2/6
        'date_format': '%d/%m/%Y',
        'currency': r'([\d.,]+)',
        'categories': {
            'alimentacao': ['rest', 'aliment', 'delivery', 'lanche'],
            'transporte': ['combust', 'posto', 'uber', 'taxi'],
            'saude': ['farm', 'saude', 'medic', 'hosp'],
            'compras': ['loja', 'varejo', 'shopping'],
            'servicos': ['servico', 'streaming', 'internet']
        }
    },
    
    # C6 BANK - Exemplo baseado em bancos digitais modernos
    'c6': {
        'transaction': r'(\d{2}/\d{2})\s+(.+?)\s+(R\$\s*[\d.,]+)',
        'installment': r'\[(\d+)/(\d+)\]',  # Formato: [2/6]
        'date_format': '%d/%m',
        'currency': r'R\$\s*([\d.,]+)',
        'categories': {
            'alimentacao': ['restaurante', 'delivery', 'ifood', 'food'],
            'transporte': ['uber', 'posto', 'combustivel', 'transport'],
            'saude': ['farmacia', 'saude', 'hospital', 'medico'],
            'compras': ['loja', 'shopping', 'ecommerce', 'varejo'],
            'servicos': ['netflix', 'spotify', 'streaming', 'digital']
        }
    }
}

# ==========================================
# 2. ATUALIZAR MÉTODO detect_bank_format()
# ==========================================

def detect_bank_format_NOVO(self, text):
    """Versão atualizada com novos bancos"""
    text_lower = text.lower()
    
    # Bancos existentes
    if 'nubank' in text_lower or 'nu pagamentos' in text_lower:
        return 'nubank'
    elif 'itau' in text_lower or 'itaú' in text_lower:
        return 'itau'
    elif 'bradesco' in text_lower:
        return 'bradesco'
    elif 'santander' in text_lower:
        return 'santander'
    elif 'caixa' in text_lower or 'cef' in text_lower:
        return 'caixa'
    
    # NOVOS BANCOS
    elif 'btg' in text_lower or 'btg pactual' in text_lower:
        return 'btg'
    elif 'unicred' in text_lower:
        return 'unicred'
    elif 'c6' in text_lower or 'c6 bank' in text_lower or 'banco c6' in text_lower:
        return 'c6'
    
    # Fallback: tentar detectar por padrões
    for bank, patterns in self.patterns.items():
        if re.search(patterns['transaction'], text, re.IGNORECASE | re.MULTILINE):
            return bank
    
    return 'nubank'  # Default

# ==========================================
# 3. EXEMPLOS DE TRANSAÇÕES ESPERADAS
# ==========================================

EXEMPLOS_TRANSACOES = {
    'btg': [
        "15/01/2024 UBER TRIP SAO PAULO R$ 25,50",
        "16/01/2024 IFOOD DELIVERY 2/6 R$ 45,80", 
        "17/01/2024 POSTO SHELL BR R$ 120,00",
        "18/01/2024 NETFLIX ASSINATURA R$ 32,90",
        "19/01/2024 MAGAZINE LUIZA 3/12 R$ 299,90"
    ],
    
    'unicred': [
        "15/01/2024 UBER TRIP SAO PAULO 25,50",
        "16/01/2024 IFOOD DELIVERY PARC 2/6 45,80",
        "17/01/2024 POSTO SHELL BR 120,00", 
        "18/01/2024 NETFLIX STREAMING 32,90",
        "19/01/2024 MAGAZINE LUIZA PARC 3/12 299,90"
    ],
    
    'c6': [
        "15/01 UBER TRIP SAO PAULO R$ 25,50",
        "16/01 IFOOD DELIVERY [2/6] R$ 45,80",
        "17/01 POSTO SHELL BR R$ 120,00",
        "18/01 NETFLIX DIGITAL R$ 32,90", 
        "19/01 MAGAZINE LUIZA [3/12] R$ 299,90"
    ]
}

# ==========================================
# 4. TESTE PARA VALIDAR PADRÕES
# ==========================================

def testar_novos_padroes():
    """Função para testar os novos padrões"""
    import re
    
    print("🧪 TESTANDO NOVOS PADRÕES DE BANCO")
    print("=" * 50)
    
    for banco, exemplos in EXEMPLOS_TRANSACOES.items():
        print(f"\n🏦 Testando {banco.upper()}:")
        padrao = NOVOS_PADROES[banco]['transaction']
        
        for exemplo in exemplos:
            match = re.search(padrao, exemplo)
            if match:
                grupos = match.groups()
                print(f"  ✅ {exemplo}")
                print(f"     Data: {grupos[0]}")
                print(f"     Descrição: {grupos[1]}")
                print(f"     Valor: {grupos[2]}")
            else:
                print(f"  ❌ {exemplo}")
    
    print("\n" + "=" * 50)
    print("✨ Teste concluído!")

# ==========================================
# 5. INSTRUÇÕES DE IMPLEMENTAÇÃO
# ==========================================

INSTRUCOES_IMPLEMENTACAO = """
📋 PASSOS PARA IMPLEMENTAR NOVOS BANCOS:

1. 📄 RECEBER PDF DE EXEMPLO
   - Analisar estrutura das transações
   - Identificar padrões de data, valor e parcelas
   - Encontrar identificadores únicos do banco

2. 🔍 CRIAR PADRÕES REGEX
   - Baseado nos exemplos reais do PDF
   - Testar com múltiplas transações
   - Validar formatos de data e moeda

3. 📝 ADICIONAR NO CÓDIGO
   - Incluir padrões em pdf_analyzer.py
   - Atualizar método detect_bank_format()
   - Adicionar categorias específicas

4. 🧪 TESTAR IMPLEMENTAÇÃO
   - Usar PDF real para validar
   - Verificar extração de todas as transações
   - Confirmar categorização automática

5. 📚 ATUALIZAR DOCUMENTAÇÃO
   - Adicionar banco na lista suportados
   - Incluir exemplos de formato
   - Atualizar README.md

6. 🚀 RELEASE
   - Testar com múltiplos PDFs
   - Validar edge cases
   - Disponibilizar para usuários
"""

# ==========================================
# 6. TEMPLATE PARA NOVOS BANCOS
# ==========================================

TEMPLATE_NOVO_BANCO = {
    'NOME_BANCO': {
        # Padrão principal para extrair transações
        # Grupos: (data, descrição, valor)
        'transaction': r'REGEX_AQUI',
        
        # Padrão para identificar parcelas
        # Grupos: (parcela_atual, parcela_total)  
        'installment': r'REGEX_PARCELA_AQUI',
        
        # Formato da data para parsing
        'date_format': '%d/%m/%Y',  # ou '%d/%m' ou '%d/%m/%y'
        
        # Padrão para extrair valor monetário
        'currency': r'REGEX_VALOR_AQUI',
        
        # Palavras-chave para categorização automática
        'categories': {
            'alimentacao': ['restaurante', 'delivery', 'ifood'],
            'transporte': ['uber', 'posto', 'combustivel'],
            'saude': ['farmacia', 'hospital', 'clinica'],
            'compras': ['loja', 'shopping', 'varejo'],
            'servicos': ['netflix', 'streaming', 'internet']
        }
    }
}

if __name__ == "__main__":
    # Executar teste dos novos padrões
    testar_novos_padroes()
    
    print("\n📖 PRÓXIMOS PASSOS:")
    print("1. Envie PDFs de exemplo dos bancos BTG, Unicred e C6")
    print("2. Analisaremos os padrões reais")
    print("3. Implementaremos baseado na estrutura mostrada aqui")
    print("4. Testaremos com seus PDFs")
    print("5. Disponibilizaremos o suporte completo")
    
    print("\n📧 COMO ENVIAR:")
    print("- Leia o arquivo CONTRIBUIR_NOVOS_BANCOS.md")
    print("- Remova informações pessoais dos PDFs")
    print("- Inclua exemplos de transações variadas")
    print("- Descreva os padrões que você identificou")