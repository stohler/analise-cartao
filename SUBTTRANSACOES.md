# 🛒 Sistema de Subtransações

## Visão Geral

O sistema de subtransações permite analisar e categorizar itens individuais de compras de supermercado a partir de XMLs de Nota Fiscal Eletrônica (NFe). Este sistema oferece uma visão detalhada dos gastos por categoria e subcategoria de produtos.

## Funcionalidades Implementadas

### ✅ 1. Upload de XMLs de NFe
- **Interface**: Página dedicada para upload de XMLs
- **Suporte**: Arquivos XML de NFe padrão brasileiro
- **Processamento**: Extração automática de itens e informações da nota

### ✅ 2. Categorização Automática
- **Categorias Principais**:
  - Laticínios (leite, queijo, iogurte, etc.)
  - Carnes (bovinas, suínas, aves, embutidos)
  - Frutas e Verduras (frutas, verduras, legumes)
  - Bebidas (água, sucos, alcoólicas, café)
  - Limpeza (produtos, papelaria, utensílios)
  - Higiene (cuidados pessoais, bucal, bebê)
  - Padaria (pães, doces, salgados)
  - Outros

- **Subcategorias**: Cada categoria possui subcategorias específicas
- **IA**: Categorização baseada em palavras-chave nos nomes dos produtos

### ✅ 3. Interface de Gerenciamento
- **Lista de XMLs**: Visualização de todos os XMLs não conciliados
- **Detalhes**: Informações do estabelecimento, data, valor total e itens
- **Estatísticas**: Resumo de XMLs processados e taxa de conciliação

### ✅ 4. Relatórios por Subcategoria
- **Resumo por Categoria**: Valores totais por categoria principal
- **Detalhamento**: Breakdown por subcategoria dentro de cada categoria
- **Gráficos**: Visualização em barras das distribuições
- **Exportação**: Tabelas com dados detalhados para análise

### ✅ 5. Sistema de Conciliação
- **Sugestões Automáticas**: Busca por XMLs compatíveis por data e valor
- **Tolerância Configurável**: Ajuste de dias e percentual de diferença
- **Associação**: Vinculação de XMLs com transações principais

## Como Usar

### 1. Acessar o Sistema
- Navegue até **Subtransações** no menu principal
- Ou acesse diretamente: `/subtransactions`

### 2. Upload de XMLs
1. Clique em "Selecionar XML" ou arraste um arquivo XML
2. Aguarde o processamento automático
3. Visualize os itens categorizados

### 3. Visualizar Relatórios
- Acesse **Relatório Subcategorias** no menu
- Analise os gastos por categoria e subcategoria
- Exporte dados para análise externa

### 4. Conciliação (Em Desenvolvimento)
- Use as sugestões automáticas para encontrar transações compatíveis
- Associe XMLs com transações do cartão de crédito
- Mantenha histórico de conciliações

## Estrutura de Dados

### SubTransaction
```python
{
    'item_id': 'item_1',
    'description': 'IOGURTE NESTLE 100G',
    'quantity': 1.0,
    'unit_value': 2.98,
    'total_value': 2.98,
    'category': 'laticinios',
    'subcategory': 'leite_derivados',
    'xml_id': '42250982647165002087651070000703619632606586',
    'reconciled': False,
    'transaction_id': None
}
```

### SubTransactionXML
```python
{
    'xml_id': '42250982647165002087651070000703619632606586',
    'filename': 'nota_fiscal.xml',
    'total_value': 69.44,
    'emission_date': '2025-09-23T18:28:05-03:00',
    'establishment_name': 'JS VILA NOVA',
    'subtransactions': [...],
    'reconciled': False
}
```

## APIs Disponíveis

### Upload de XML
```
POST /upload_xml
Content-Type: multipart/form-data
```

### Listar Subtransações
```
GET /api/subtransactions
```

### Sugestões de Conciliação
```
GET /api/reconciliation_suggestions?date=2025-09-23&value=69.44
```

### Conciliação
```
POST /api/reconcile_xml
{
    "xml_id": "42250982647165002087651070000703619632606586",
    "transaction_id": "transaction_123"
}
```

## Exemplos de XMLs Suportados

O sistema foi testado com XMLs de:
- **Cooperativas**: JS VILA NOVA (exemplo incluído)
- **Supermercados**: Qualquer NFe padrão brasileiro
- **Formato**: XML com namespace `http://www.portalfiscal.inf.br/nfe`

## Arquivos Criados

### Modelos e Lógica
- `subtransaction_models.py` - Modelos de dados e gerenciador
- `xml_parser.py` - Parser para XMLs de NFe

### Interface Web
- `templates/subtransactions.html` - Página principal
- `templates/subcategory_report.html` - Relatórios

### Integração
- `app.py` - Rotas e APIs adicionadas
- `templates/base.html` - Menu atualizado

## Próximos Passos

### 🔄 Em Desenvolvimento
- [ ] Interface de conciliação completa
- [ ] Visualização detalhada de itens por XML
- [ ] Histórico de conciliações
- [ ] Exportação de dados conciliados

### 🚀 Futuras Melhorias
- [ ] Integração com MongoDB para persistência
- [ ] Machine Learning para categorização
- [ ] Análise de padrões de compra
- [ ] Alertas de gastos por categoria
- [ ] Comparativo mensal por subcategoria

## Troubleshooting

### XML não é processado
- Verifique se é um XML de NFe válido
- Confirme se tem o namespace correto
- Verifique logs do servidor para erros

### Categorização incorreta
- Os itens são categorizados por palavras-chave
- Produtos não reconhecidos vão para "outros"
- Sistema pode ser expandido com novas categorias

### Problemas de conciliação
- Verifique se as datas estão no formato correto
- Ajuste tolerâncias se necessário
- Confirme se as transações existem no sistema

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do servidor
2. Confirme se os XMLs seguem o padrão NFe
3. Teste com os XMLs de exemplo fornecidos
4. Consulte a documentação das APIs

---

**Status**: ✅ Sistema implementado e funcional
**Versão**: 1.0.0
**Última Atualização**: Outubro 2025

