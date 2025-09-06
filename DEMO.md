# 🎯 DEMONSTRAÇÃO - Analisador de Faturas de Cartão

## 🚀 Como Executar

### Opção 1: Script Automático
```bash
./start.sh
```

### Opção 2: Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar aplicação
python app.py
```

### Opção 3: Teste do Analisador
```bash
# Testar funcionalidades sem interface web
python test_analyzer.py
```

## 🌐 Acessando a Aplicação

1. Execute um dos comandos acima
2. Abra seu navegador
3. Acesse: `http://localhost:5000`

## 📋 Como Usar

### 1. Upload do PDF
- **Arraste e solte** seu PDF na área de upload
- Ou **clique na área** para selecionar o arquivo
- Formatos aceitos: `.pdf` (máximo 16MB)

### 2. Análise Automática
A aplicação irá:
- ✅ Detectar automaticamente o banco (Nubank, Itaú, Bradesco, Santander, Caixa)
- ✅ Extrair todas as transações
- ✅ Identificar parcelas e parcelamentos  
- ✅ Categorizar automaticamente as transações
- ✅ Calcular estatísticas resumidas

### 3. Visualização dos Resultados
Você verá:
- **Resumo**: Total de transações, valor gasto, parcelas
- **Categorias**: Distribuição por tipo (alimentação, transporte, etc.)
- **Tabela detalhada**: Todas as transações com dados completos

### 4. Exportação
Clique em um dos botões para baixar:
- **CSV**: Para análise em planilhas
- **Excel**: Formato .xlsx com formatação
- **JSON**: Para integração com outros sistemas

## 🏦 Bancos Suportados

| Banco | Status | Padrão de Data | Formato de Parcela |
|-------|--------|----------------|-------------------|
| **Nubank** | ✅ | DD/MM | N/N |
| **Itaú** | ✅ | DD/MM/YYYY | PARC N/N |
| **Bradesco** | ✅ | DD/MM | NªDE N |
| **Santander** | ✅ | DD/MM/YY | PARCELA N/N |
| **Caixa** | ✅ | DD/MM/YYYY | N/N PARCELA |

## 📊 Dados Extraídos

Para cada transação:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| **Data** | Data da transação | 15/01/2024 |
| **Descrição** | Nome do estabelecimento | UBER TRIP SAO PAULO |
| **Valor** | Valor em reais | R$ 25,50 |
| **Parcelado** | Se é parcelado | Sim/Não |
| **Parcela** | Parcela atual/total | 2/6 |
| **Categoria** | Categoria automática | transporte |

## 🏷️ Categorias Automáticas

- **🍕 Alimentação**: restaurante, delivery, ifood, lanchonete
- **🚗 Transporte**: uber, posto, combustível, estacionamento
- **💊 Saúde**: farmácia, hospital, clínica, médico
- **🛍️ Compras**: magazine, amazon, mercado livre, loja
- **📱 Serviços**: netflix, spotify, internet, telefone
- **📦 Outros**: transações não categorizadas

## 🧪 Teste Rápido

Execute o teste para ver o analisador em ação:

```bash
python test_analyzer.py
```

**Saída esperada:**
```
🧪 Testando Analisador de PDF de Faturas
==================================================
🔍 Testando detecção de formato...
Formato detectado Nubank: nubank
Formato detectado Itaú: itau

📊 Testando extração de transações...
Transações Nubank encontradas: 7
  1. 12/01/2025 - UBER TRIP... - R$ 15.50 - transporte
  2. 15/01/2025 - IFOOD DELIVERY... - R$ 45.80 - alimentacao
  3. 18/01/2025 - POSTO BR COMBUSTIVEL... - R$ 120.00 - transporte
```

## 🔒 Segurança e Privacidade

- ✅ Processamento **100% local** - seus dados não saem do seu computador
- ✅ Arquivos temporários são **automaticamente removidos**
- ✅ Não há armazenamento permanente de dados
- ✅ Interface web local (não exposta à internet)

## 📁 Estrutura de Arquivos

```
/workspace/
├── app.py              # Aplicação Flask principal
├── pdf_analyzer.py     # Módulo de análise de PDF
├── start.sh           # Script de inicialização
├── test_analyzer.py   # Script de teste
├── requirements.txt   # Dependências Python
├── templates/
│   └── index.html     # Interface web
├── static/
│   ├── css/style.css  # Estilos
│   └── js/app.js      # JavaScript
└── venv/             # Ambiente virtual Python
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.13, Flask
- **PDF**: PyPDF2, pdfplumber
- **Data**: pandas, openpyxl
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Regex**: Padrões customizados para cada banco

## 🎯 Próximos Passos

Para enviar **PDFs de exemplo** para melhorar o sistema:

1. **Remova informações pessoais** (CPF, números de conta, etc.)
2. **Mantenha apenas** as transações e estrutura
3. **Indique o banco** no nome do arquivo
4. **Descreva problemas** encontrados na análise

## 📞 Suporte

- Execute `python test_analyzer.py` para diagnósticos
- Verifique se todas as dependências estão instaladas
- Confirme que o PDF contém texto (não apenas imagens)
- Teste com PDFs de diferentes bancos para comparar resultados