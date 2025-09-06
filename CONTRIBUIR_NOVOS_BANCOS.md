# 🏦 Como Contribuir com Novos Bancos

## 📋 Bancos Solicitados

Atualmente precisamos de PDFs de exemplo para implementar suporte aos seguintes bancos:

- **BTG Pactual** 🏦
- **Unicred** 🏦  
- **C6 Bank** 🏦

## 🎯 Como Enviar PDFs de Exemplo

### 1. 📄 Preparação do PDF

#### ✅ O que INCLUIR:
- **Estrutura completa** da fatura do cartão de crédito
- **Transações reais** (pelo menos 10-15 transações)
- **Diferentes tipos** de transações:
  - Compras à vista
  - Compras parceladas (2x, 3x, 6x, 12x, etc.)
  - Diferentes estabelecimentos
  - Valores variados
- **Cabeçalho** com informações do banco
- **Datas** em formato completo
- **Layout original** do banco

#### ❌ O que REMOVER (Informações Pessoais):
- **CPF/CNPJ**
- **Números de conta** e cartão
- **Nome completo** do titular
- **Endereço** completo
- **Telefone** e email
- **Código de segurança**
- **Limite de crédito** (se sensível)

**💡 DICA**: Você pode substituir informações pessoais por:
- Nome: "FULANO DE TAL"
- CPF: "000.000.000-00" 
- Conta: "0000-0"

### 2. 📝 Informações Necessárias

Para cada PDF enviado, inclua as seguintes informações:

#### **Dados do Banco:**
```
Banco: [BTG/Unicred/C6]
Tipo de cartão: [Crédito/Débito]
Período da fatura: [MM/AAAA]
```

#### **Padrões Identificados:**
```
Formato de data: [DD/MM, DD/MM/YYYY, etc.]
Formato de valor: [R$ 0,00 ou 0,00 ou R$0.00]
Formato de parcela: [1/12, PARC 1/12, 1ª DE 12, etc.]
Identificador único: [Texto que aparece só nesse banco]
```

#### **Exemplos de Transações:**
```
Linha exemplo 1: "15/01/2024 UBER TRIP SAO PAULO R$ 25,50"
Linha exemplo 2: "16/01/2024 IFOOD DELIVERY PARC 2/6 R$ 45,80"
Linha exemplo 3: "17/01/2024 POSTO SHELL BR R$ 120,00"
```

### 3. 📤 Formas de Envio

#### **Opção 1: GitHub Issues** (Recomendado)
1. Acesse o repositório do projeto
2. Crie uma nova **Issue**
3. Título: `[NOVO BANCO] Suporte para [Nome do Banco]`
4. Anexe o PDF anonimizado
5. Inclua todas as informações solicitadas

#### **Opção 2: Email** 
- Envie para: `[email-do-projeto]`
- Assunto: `PDF Exemplo - [Nome do Banco]`
- Anexe o PDF e informações

#### **Opção 3: Pull Request**
Se você souber programar:
1. Fork do repositório
2. Adicione os padrões em `pdf_analyzer.py`
3. Teste com seu PDF
4. Abra Pull Request

### 4. 🔍 O que Analisamos no PDF

#### **Estrutura de Transações:**
- Como as transações aparecem no PDF?
- Qual o padrão de cada linha?
- Onde ficam data, descrição e valor?

#### **Formato de Datas:**
- `15/01` (Nubank)
- `15/01/2024` (Itaú, Caixa)  
- `15/01/24` (Santander)

#### **Formato de Valores:**
- `R$ 25,50` (Nubank, Caixa)
- `25,50` (Bradesco)
- `25.50` (alguns bancos internacionais)

#### **Formato de Parcelas:**
- `2/6` (Nubank)
- `PARC 2/6` (Itaú)
- `2ª DE 6` (Bradesco)
- `PARCELA 2/6` (Santander)

### 5. 🧪 Teste Seu PDF

Antes de enviar, teste se conseguimos extrair texto do PDF:

```bash
# Execute no terminal
python test_analyzer.py
```

Se o teste não funcionar com seu PDF, pode ser que:
- PDF seja apenas imagem (precisa de OCR)
- PDF esteja protegido/criptografado
- Formato seja muito diferente dos suportados

### 6. 📊 Exemplo de Estrutura Esperada

#### **BTG Pactual** (Exemplo hipotético):
```
Data       Descrição                    Valor
15/01/24   UBER TRIP SAO PAULO         R$ 25,50
16/01/24   IFOOD DELIVERY 2/6          R$ 45,80
17/01/24   POSTO SHELL                 R$ 120,00
```

#### **Unicred** (Exemplo hipotético):
```
15/01/2024  UBER TRIP SAO PAULO         25,50
16/01/2024  IFOOD DELIVERY PARC 2/6     45,80  
17/01/2024  POSTO SHELL BR              120,00
```

#### **C6 Bank** (Exemplo hipotético):
```
15/01  UBER TRIP SAO PAULO             R$ 25,50
16/01  IFOOD DELIVERY [2/6]            R$ 45,80
17/01  POSTO SHELL                     R$ 120,00
```

## 🚀 Processo de Implementação

### **Após receber seu PDF:**

1. **Análise** - Estudamos o formato e padrões
2. **Implementação** - Adicionamos suporte no código
3. **Teste** - Validamos com seu PDF
4. **Ajustes** - Refinamos se necessário
5. **Release** - Disponibilizamos na próxima versão

### **Tempo estimado:** 3-7 dias

## 🎁 Reconhecimento

Contribuidores que enviarem PDFs válidos serão:
- **Mencionados** no README do projeto
- **Creditados** no changelog
- **Notificados** quando o suporte for implementado

## ❓ Dúvidas Frequentes

### **"Meu PDF tem informações sensíveis"**
- Remova ou mascare todas as informações pessoais
- Mantenha apenas a estrutura e transações
- Use dados fictícios se necessário

### **"Não tenho fatura recente"**
- Faturas antigas também servem
- O importante é a estrutura, não as datas
- Pode ser de qualquer mês/ano

### **"Meu PDF não tem muitas transações"**
- Mínimo de 5-10 transações
- Inclua pelo menos 1 transação parcelada
- Varie os tipos de estabelecimento

### **"Posso enviar múltiplos PDFs do mesmo banco?"**
- Sim! Quanto mais exemplos, melhor
- Diferentes períodos ajudam
- Diferentes tipos de cartão também

## 📞 Contato e Suporte

- **GitHub Issues**: Para relatar problemas ou enviar PDFs
- **Documentação**: Leia este guia completo antes de enviar
- **Testes**: Execute `python test_analyzer.py` para diagnósticos

---

## 🏆 Contribua para o Projeto

Sua contribuição ajuda milhares de usuários a analisar suas faturas automaticamente!

**Banco atual suportados:** 5  
**Bancos solicitados:** BTG, Unicred, C6  
**Meta:** 10+ bancos até final de 2024

---

*Obrigado por contribuir com o projeto! 🙏*