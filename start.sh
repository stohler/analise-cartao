#!/bin/bash

# Script para iniciar a aplicação de análise de faturas

echo "🚀 Iniciando Analisador de Faturas de Cartão..."
echo "================================================="

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "📦 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado. Criando..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Instalando dependências..."
    pip install -r requirements.txt
fi

# Verificar se todas as dependências estão instaladas
echo "🔍 Verificando dependências..."
python -c "import flask, PyPDF2, pdfplumber, pandas, openpyxl" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Todas as dependências estão instaladas!"
else
    echo "❌ Algumas dependências estão faltando. Instalando..."
    pip install -r requirements.txt
fi

# Criar diretório de uploads se não existir
mkdir -p uploads

echo ""
echo "🌐 Iniciando servidor web..."
echo "📍 Acesse: http://localhost:5000"
echo "💡 Para parar: Ctrl+C"
echo ""
echo "📋 Bancos suportados:"
echo "   • Nubank"
echo "   • Itaú" 
echo "   • Bradesco"
echo "   • Santander"
echo "   • Caixa Econômica Federal"
echo ""
echo "================================================="

# Iniciar aplicação
python app.py