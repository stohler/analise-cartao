# 📋 RESUMO: Como Enviar PDFs para BTG, Unicred e C6

## 🎯 Objetivo
Adicionar suporte aos bancos **BTG Pactual**, **Unicred** e **C6 Bank** no analisador de faturas.

## 📤 Como Enviar (Passo a Passo)

### 1. 📄 Prepare seu PDF
- ✅ Fatura de cartão de crédito completa
- ✅ Pelo menos 10-15 transações variadas
- ✅ Inclua transações parceladas e à vista
- ❌ **REMOVA** informações pessoais:
  - CPF, nome completo, número do cartão
  - Endereço, telefone, email
  - Substitua por dados fictícios se necessário

### 2. 🧪 Teste seu PDF (Opcional)
```bash
python test_novos_bancos.py sua_fatura.pdf
```
Este comando irá:
- Extrair texto do PDF
- Identificar possíveis padrões
- Mostrar linhas de transações
- Gerar relatório para envio

### 3. 📧 Envie os Dados

#### **Via GitHub Issues** (Recomendado):
1. Acesse o repositório do projeto
2. Crie nova Issue: `[NOVO BANCO] Suporte para BTG/Unicred/C6`
3. Anexe o PDF anonimizado
4. Inclua as informações abaixo

#### **Informações Obrigatórias:**
```
BANCO: [BTG Pactual / Unicred / C6 Bank]
PERÍODO: MM/AAAA da fatura

EXEMPLOS DE TRANSAÇÕES:
• Linha 1: "15/01/2024 UBER TRIP SAO PAULO R$ 25,50"
• Linha 2: "16/01/2024 IFOOD DELIVERY 2/6 R$ 45,80"
• Linha 3: "17/01/2024 POSTO SHELL R$ 120,00"

PADRÕES IDENTIFICADOS:
• Data: DD/MM/YYYY ou DD/MM
• Valor: R$ X,XX ou X,XX
• Parcela: X/X ou PARC X/X ou [X/X]
• Identificador: Texto único que aparece no PDF
```

## 🔍 O que Analisamos

### **Estrutura de Transações**
- Como cada linha de transação aparece
- Posição de data, descrição e valor
- Separadores utilizados

### **Formatos Específicos**
- **Data**: `15/01`, `15/01/2024`, `15/01/24`
- **Valor**: `R$ 25,50`, `25,50`, `25.50`
- **Parcela**: `2/6`, `PARC 2/6`, `[2/6]`, `2ª DE 6`

### **Identificadores Únicos**
- Nome do banco no cabeçalho
- Logos ou textos específicos
- Formatação característica

## ⏱️ Processo e Tempo

1. **Recebimento**: Análise do PDF enviado
2. **Desenvolvimento**: Criação dos padrões (3-5 dias)
3. **Teste**: Validação com seu PDF
4. **Ajustes**: Refinamento se necessário
5. **Release**: Disponibilização na próxima versão

**Tempo total estimado:** 7-10 dias

## 🎁 Reconhecimento

Contribuidores que enviarem PDFs válidos:
- ✨ Serão mencionados no README
- 🏆 Creditados no changelog
- 📧 Notificados quando implementado
- 🎯 Terão acesso antecipado ao suporte

## 📞 Suporte

- **Dúvidas**: Leia `CONTRIBUIR_NOVOS_BANCOS.md`
- **Problemas**: Execute `python test_novos_bancos.py`
- **Contato**: GitHub Issues ou email do projeto

---

## 🚀 Arquivos Criados para Ajudar

1. **`CONTRIBUIR_NOVOS_BANCOS.md`** - Guia completo detalhado
2. **`test_novos_bancos.py`** - Script para testar PDFs
3. **`EXEMPLO_IMPLEMENTACAO_BANCO.py`** - Como implementamos
4. **`RESUMO_CONTRIBUICAO.md`** - Este resumo rápido

---

## 💡 Exemplo Rápido

**Se você tem uma fatura do BTG:**

```bash
# 1. Remova dados pessoais do PDF
# 2. Execute o teste
python test_novos_bancos.py fatura_btg_anonimizada.pdf

# 3. Copie a saída do comando
# 4. Crie GitHub Issue com:
#    - PDF anexado
#    - Saída do comando
#    - Banco: BTG Pactual
```

**Pronto! Em 7-10 dias teremos suporte ao BTG implementado! 🎉**

---

*Obrigado por contribuir para o projeto! Sua ajuda permite que milhares de usuários analisem suas faturas automaticamente.* 🙏