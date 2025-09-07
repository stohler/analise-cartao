# 📊 Comparação Mês a Mês - Analisador de Faturas

## 🎯 Funcionalidade Implementada

Foi criada uma nova página que permite comparar gastos por categoria ao longo de até 6 meses, analisando múltiplas faturas de cartão de crédito.

## 🚀 Como Usar

### 1. Acesso à Página
- Acesse a página principal do analisador
- Clique no botão **"Comparação Mês a Mês"** no cabeçalho
- Ou acesse diretamente: `http://localhost:5000/comparison`

### 2. Upload de Múltiplas Faturas
- **Arraste e solte** até 6 arquivos PDF de faturas
- Ou **clique** na área de upload para selecionar arquivos
- **Limite**: Máximo 6 arquivos (representando até 6 meses)
- **Formatos suportados**: PDF de faturas dos bancos suportados

### 3. Análise e Visualização
- Clique em **"Analisar Comparação"**
- Aguarde o processamento das faturas
- Visualize os resultados em gráficos e tabelas

## 📈 Recursos da Página

### Estatísticas Resumidas
- **Meses Analisados**: Quantidade de meses processados
- **Total de Transações**: Número total de transações encontradas
- **Valor Total**: Soma de todos os gastos analisados

### Gráfico de Barras
- **Visualização**: Gastos por categoria mês a mês
- **Interativo**: Hover para ver valores detalhados
- **Cores**: Cada categoria tem uma cor diferente
- **Formato**: Valores em reais (R$)

### Detalhamento Mensal
- **Cards por Mês**: Cada mês em um card colorido
- **Categorias**: Badges com valores e percentuais
- **Total Mensal**: Valor total gasto no mês
- **Percentuais**: Distribuição percentual por categoria

## 🛠️ Implementação Técnica

### Backend (Flask)
- **Nova rota**: `/comparison` - Página de comparação
- **Nova rota**: `/upload_multiple` - Upload de múltiplos PDFs
- **Função**: `process_comparison_data()` - Processa dados para comparação

### Frontend (HTML/CSS/JavaScript)
- **Template**: `templates/comparison.html`
- **Bibliotecas**: Bootstrap 5, Chart.js, Font Awesome
- **Funcionalidades**: Drag & drop, upload múltiplo, gráficos interativos

### Processamento de Dados
```python
def process_comparison_data(transactions):
    # Agrupa transações por mês e categoria
    # Calcula totais e percentuais
    # Retorna dados estruturados para visualização
```

## 📊 Estrutura dos Dados

### Entrada
```json
[
    {
        "data": "15/01/2024",
        "categoria": "alimentacao",
        "valor": 50.0,
        "arquivo": "fatura_janeiro.pdf"
    }
]
```

### Saída
```json
{
    "monthly_breakdown": {
        "2024-01": {
            "month_name": "January/2024",
            "categories": {
                "alimentacao": 150.0,
                "transporte": 80.0
            },
            "total": 230.0
        }
    },
    "category_totals": {
        "alimentacao": 300.0,
        "transporte": 120.0
    },
    "months": ["2024-01", "2024-02"],
    "categories": ["alimentacao", "transporte"]
}
```

## 🎨 Interface do Usuário

### Design Responsivo
- **Mobile-first**: Funciona em dispositivos móveis
- **Bootstrap 5**: Framework CSS moderno
- **Cores**: Gradientes e paleta consistente

### Experiência do Usuário
- **Drag & Drop**: Interface intuitiva para upload
- **Feedback Visual**: Loading states e progress bars
- **Gráficos Interativos**: Chart.js para visualizações
- **Navegação**: Links entre páginas principais

## 🔧 Configurações

### Limites
- **Máximo de arquivos**: 6 PDFs
- **Tamanho máximo**: 16MB por arquivo
- **Período**: Até 6 meses de dados

### Bancos Suportados
- Nubank
- Itaú
- Bradesco
- Santander
- Caixa
- BTG Pactual
- Unicred
- C6 Bank

## 🚀 Como Executar

1. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Executar aplicação**:
   ```bash
   python app.py
   ```

3. **Acessar no navegador**:
   ```
   http://localhost:5000/comparison
   ```

## 📝 Exemplo de Uso

1. **Preparar faturas**: Colete PDFs de 3-6 meses de faturas
2. **Acessar página**: Vá para a página de comparação
3. **Upload**: Arraste os PDFs para a área de upload
4. **Analisar**: Clique em "Analisar Comparação"
5. **Visualizar**: Veja gráficos e estatísticas detalhadas
6. **Comparar**: Analise tendências mês a mês por categoria

## ✅ Benefícios

- **Visão Histórica**: Compare gastos ao longo do tempo
- **Análise de Tendências**: Identifique padrões de consumo
- **Categorização**: Veja distribuição por categoria
- **Visualização**: Gráficos claros e informativos
- **Múltiplos Bancos**: Suporte a vários bancos
- **Interface Intuitiva**: Fácil de usar

## 🔮 Possíveis Melhorias Futuras

- Exportar relatórios em PDF/Excel
- Filtros por categoria ou período
- Comparação com meses anteriores
- Metas de gastos por categoria
- Alertas de gastos excessivos
- Integração com APIs bancárias
