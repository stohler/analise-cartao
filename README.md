# 🏦 Analisador de PDFs de Cartão de Crédito

Sistema completo para análise e armazenamento de transações de cartão de crédito extraídas de PDFs de faturas bancárias.

## ✨ Funcionalidades

### 📄 Análise de PDFs
- **Suporte a múltiplos bancos**: Nubank, Itaú, Bradesco, Santander, BTG, Unicred, C6, Caixa
- **Detecção automática** do banco baseada no conteúdo do PDF
- **Extração inteligente** de transações com data, descrição, valor e categoria
- **Detecção de parcelamentos** automática
- **Categorização** das transações por tipo (alimentação, transporte, saúde, compras, serviços)

### 💾 Armazenamento
- **Remoção de duplicados** baseada em hash único
- **Origem do cartão** configurável (Principal, Adicional, Corporativo, etc.)
- **Armazenamento local** em arquivo JSON
- **Preparado para MongoDB** (formato de exportação incluído)

### 📊 Análise Temporal
- **Comparativo de 6 meses** com tendências e insights
- **Análise por origem do cartão** (filtros específicos)
- **Relatórios executivos** com estatísticas detalhadas
- **Exportação de relatórios** em formato JSON
- **Integração MongoDB** para consultas avançadas

### 🖥️ Interfaces
- **Interface web** (Flask) - Upload de PDFs e gravação automática no MongoDB
- **Interface gráfica** (tkinter) - quando disponível
- **Interface de linha de comando** - sempre funcional
- **Exportação** para formato MongoDB

## 🚀 Como Usar

### Interface Web (Recomendada)

```bash


```

Acesse: **http://localhost:5000**

**Funcionalidades da interface web:**
- 📤 **Upload de PDFs** com drag & drop
- 🔍 **Análise automática** de transações
- 💾 **Botão para gravar no MongoDB** automaticamente
- 📊 **Visualização** de transações em tabelas
- 📈 **Comparativo mensal** integrado
- 🎨 **Interface moderna** com Bootstrap

### Interface de Linha de Comando

```bash
python3 cli_analyzer.py
```

**Menu principal:**
1. **Analisar PDF** - Carrega e analisa um arquivo PDF
2. **Ver transações salvas** - Lista transações armazenadas
3. **Estatísticas** - Mostra estatísticas detalhadas
4. **Comparativo 6 meses** - Análise temporal com tendências
5. **Exportar para MongoDB** - Gera arquivo JSON para importação
6. **Sair**

### Interface Gráfica (se tkinter disponível)

```bash
python3 gui_analyzer.py
```

## 📋 Exemplo de Uso

### 1. Analisar PDF
```
Digite o caminho do arquivo PDF: /caminho/para/fatura.pdf
```

### 2. Resultado da Análise
```
✅ Análise concluída!
🏦 Banco detectado: NUBANK
📈 Total de transações: 7

💳 TRANSAÇÕES ENCONTRADAS:
--------------------------------------------------
 1. 29/06/2025 - Disal Ecommerce - Parcela 7/7
     💰 Valor: R$ 51.82
     🏷️  Categoria: compras
     🏦 Banco: nubank
     📅 Parcelado: 7/7
```

### 3. Salvar Transações
```
💾 Deseja salvar estas transações? (s/n): s
Origem do cartão: Cartão Principal
Remover duplicados? (s/n): s
✅ Operação concluída: 7 salvas, 0 duplicadas, 0 erros
```

## 🗂️ Estrutura de Arquivos

```
analise-cartao/
├── pdf_analyzer.py           # Motor de análise de PDFs
├── data_handler.py           # Gerenciador de dados (JSON)
├── mongodb_handler.py        # Gerenciador MongoDB
├── monthly_comparison.py     # Sistema de comparativo mensal
├── web_analyzer.py           # Interface web (Flask)
├── start_web.py              # Script para iniciar interface web
├── gui_analyzer.py           # Interface gráfica
├── cli_analyzer.py           # Interface linha de comando
├── templates/                # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── analysis.html
│   ├── transactions.html
│   └── comparison.html
├── uploads/                  # Pasta para uploads (criada automaticamente)
├── transacoes.json           # Arquivo de dados (criado automaticamente)
├── relatorio_comparativo_*.json # Relatórios exportados
└── requirements.txt          # Dependências
```

## 📊 Formato dos Dados

### Transação Individual
```json
{
  "data": "29/06/2025",
  "descricao": "Disal Ecommerce - Parcela 7/7",
  "valor": 51.82,
  "categoria": "compras",
  "banco": "nubank",
  "parcelado": "Sim",
  "parcela_atual": 7,
  "parcela_total": 7,
  "origem_cartao": "Cartão Principal",
  "data_importacao": "2025-01-27T10:30:00",
  "transaction_hash": "abc123..."
}
```

## 🏦 Bancos Suportados

| Banco | Formato de Data | Características |
|-------|----------------|-----------------|
| **Nubank** | DD MMM | •••• + números de cartão |
| **Itaú** | DD/MM | Valores com separadores |
| **Bradesco** | DD/MM | Parcelas em formato "Xª DE Y" |
| **Santander** | DD/MM/YY | Formato "PARCELA X/Y" |
| **BTG** | DD MMM | Mês abreviado em português |
| **Unicred** | DD/MMM | Formato "Parc.X/Y" |
| **C6** | DD MMM | Padrões específicos |
| **Caixa** | DD/MM/YYYY | Formato completo |

## 🔧 Configuração MongoDB

### String de Conexão
```
mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

### Importação
1. Exporte as transações usando a opção 4 do CLI
2. Use o arquivo `transacoes_mongodb.json` gerado
3. Importe no MongoDB usando mongoimport ou interface web

## 📈 Estatísticas Disponíveis

### Estatísticas Gerais
- **Total de transações** por banco
- **Categorização** automática
- **Valor total** gasto
- **Transações parceladas** vs à vista
- **Origem do cartão** (quando múltiplos cartões)

### Análise Temporal (6 meses)
- **Comparativo mensal** de gastos
- **Tendências** de aumento/diminuição
- **Média mensal** de gastos
- **Insights automáticos** sobre padrões
- **Relatórios executivos** exportáveis
- **Análise por categoria** ao longo do tempo

## 🛠️ Dependências

```bash
pip3 install -r requirements.txt
```

Ou instalar individualmente:
```bash
pip3 install PyPDF2 pdfplumber python-dateutil Flask pymongo
```

Para MongoDB (opcional):
```bash
pip3 install pymongo[srv]
```

## 🎯 Casos de Uso

1. **Controle financeiro pessoal** - Analise faturas de múltiplos cartões
2. **Relatórios empresariais** - Consolidação de gastos corporativos
3. **Análise de padrões** - Identificação de gastos por categoria
4. **Análise temporal** - Comparativo de gastos ao longo dos meses
5. **Backup de dados** - Armazenamento seguro de transações
6. **Integração com sistemas** - Exportação para MongoDB/outros bancos
7. **Relatórios executivos** - Análise de tendências e insights automáticos

## 🔍 Detecção de Duplicados

O sistema usa hash MD5 baseado em:
- Data da transação
- Descrição
- Valor
- Banco
- Origem do cartão

Isso garante que transações idênticas não sejam duplicadas, mesmo se importadas múltiplas vezes.

## 📝 Notas Importantes

- **Formato de PDF**: Funciona melhor com PDFs de texto (não escaneados)
- **Encoding**: Suporte completo a caracteres especiais (UTF-8)
- **Performance**: Otimizado para faturas com centenas de transações
- **Backup**: Dados salvos localmente em `transacoes.json`

## 🆘 Solução de Problemas

### Erro de OpenSSL
Se encontrar problemas com pymongo, use apenas o armazenamento local (JSON).

### PDF não analisado
- Verifique se o PDF contém texto (não é imagem escaneada)
- Teste com PDFs de outros bancos suportados

### Transações não detectadas
- Verifique se o formato do banco está suportado
- Contate para adicionar novos padrões de regex

---

**Desenvolvido para análise eficiente de faturas de cartão de crédito** 🏦💳