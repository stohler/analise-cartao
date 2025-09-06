# Analisador de Faturas de Cartão de Crédito

Uma aplicação web moderna para análise automática de faturas de cartão de crédito em PDF de 5 bancos diferentes.

## 🏦 Bancos Suportados

- **Nubank**
- **Itaú** 
- **Bradesco**
- **Santander**
- **Caixa Econômica Federal**

## 📊 Dados Extraídos

Para cada transação, a aplicação extrai:

- **Data** da transação
- **Descrição** completa
- **Parcelado** (Sim/Não)
- **Parcela atual** e **total de parcelas** (se parcelado)
- **Valor** da transação
- **Categoria** automática (alimentação, transporte, saúde, compras, serviços, outros)

## 🚀 Funcionalidades

### ✨ Interface Web Moderna
- Upload por drag & drop ou clique
- Interface responsiva e intuitiva
- Visualização em tempo real dos resultados
- Estatísticas resumidas

### 📈 Análise Inteligente
- Detecção automática do formato do banco
- Categorização automática das transações
- Identificação de parcelas e parcelamentos
- Extração precisa de valores e datas

### 📤 Exportação de Dados
- **CSV** - Para análise em planilhas
- **Excel** - Formato .xlsx com formatação
- **JSON** - Para integração com outros sistemas

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone ou baixe o projeto**
```bash
cd /workspace
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Execute a aplicação**
```bash
python app.py
```

4. **Acesse no navegador**
```
http://localhost:5000
```

## 📝 Como Usar

### 1. Upload do PDF
- Acesse a aplicação no navegador
- Clique na área de upload ou arraste seu PDF de fatura
- Aguarde o processamento (alguns segundos)

### 2. Visualização dos Resultados
- Veja o resumo estatístico no topo
- Analise a distribuição por categorias
- Examine a tabela detalhada de transações

### 3. Exportação
- Clique em um dos botões de exportação (CSV, Excel, JSON)
- O arquivo será baixado automaticamente

## 🔧 Estrutura do Projeto

```
/workspace/
├── app.py                 # Aplicação Flask principal
├── pdf_analyzer.py        # Módulo de análise de PDF
├── requirements.txt       # Dependências Python
├── templates/
│   └── index.html        # Interface web
├── static/
│   ├── css/
│   │   └── style.css     # Estilos customizados
│   └── js/
│       └── app.js        # JavaScript frontend
└── uploads/              # Diretório temporário (criado automaticamente)
```

## 🎯 Padrões de Reconhecimento

### Nubank
- Formato de data: DD/MM
- Padrão de transação: `DD/MM DESCRIÇÃO R$ VALOR`
- Parcelas: `N/N`

### Itaú
- Formato de data: DD/MM/YYYY
- Padrão de transação: `DD/MM/YYYY DESCRIÇÃO VALOR`
- Parcelas: `PARC N/N`

### Bradesco
- Formato de data: DD/MM
- Padrão de transação: `DD/MM DESCRIÇÃO VALOR`
- Parcelas: `NªDE N`

### Santander
- Formato de data: DD/MM/YY
- Padrão de transação: `DD/MM/YY DESCRIÇÃO VALOR`
- Parcelas: `PARCELA N/N`

### Caixa
- Formato de data: DD/MM/YYYY
- Padrão de transação: `DD/MM/YYYY DESCRIÇÃO R$ VALOR`
- Parcelas: `N/N PARCELA`

## 🏷️ Categorização Automática

As transações são automaticamente categorizadas baseadas em palavras-chave:

- **Alimentação**: restaurante, lanchonete, delivery, ifood, uber eats
- **Transporte**: uber, 99, posto, combustível, estacionamento
- **Saúde**: farmácia, drogaria, hospital, clínica, médico
- **Compras**: magazine, americanas, mercado livre, amazon
- **Serviços**: netflix, spotify, internet, telefone
- **Outros**: transações que não se encaixam nas categorias acima

## 🔒 Segurança

- Arquivos PDF são processados localmente
- Arquivos temporários são automaticamente removidos
- Limite de 16MB por arquivo
- Apenas arquivos PDF são aceitos

## 🐛 Solução de Problemas

### Erro: "Nenhuma transação encontrada"
- Verifique se o PDF contém texto (não é apenas imagem)
- Confirme se é uma fatura de um dos bancos suportados
- Tente um PDF de melhor qualidade

### Erro: "Não foi possível extrair texto do PDF"
- O PDF pode estar protegido ou corrompido
- Tente salvar o PDF novamente ou usar uma versão diferente

### Interface não carrega
- Verifique se todas as dependências foram instaladas
- Confirme se a porta 5000 não está sendo usada por outro programa

## 📧 Suporte

Para enviar PDFs de exemplo ou reportar problemas:
1. Certifique-se de remover informações pessoais dos PDFs
2. Descreva o banco e o formato da fatura
3. Inclua detalhes sobre o erro encontrado

## 🔄 Atualizações Futuras

- Suporte a mais bancos
- Análise de tendências de gastos
- Alertas de gastos por categoria
- API REST para integração
- Processamento em lote de múltiplos PDFs