#!/bin/bash

# Script para iniciar a aplicação com autenticação

echo "🔒 Iniciando Analisador de Faturas com Autenticação..."
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
python3 -c "import flask, PyPDF2, pdfplumber, pandas, openpyxl, flask_login, flask_wtf" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Todas as dependências estão instaladas!"
else
    echo "❌ Algumas dependências estão faltando. Instalando..."
    pip install -r requirements.txt
fi

# Criar diretório de uploads se não existir
mkdir -p uploads

# Configurar variáveis de ambiente se não existirem
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo .env..."
    cat > .env << EOF
SECRET_KEY=dev-key-change-in-production-$(date +%s)
FLASK_ENV=development
SESSION_COOKIE_SECURE=false
REGISTRATION_ENABLED=true
MONGODB_URI=mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
EOF
fi

echo ""
echo "🌐 Iniciando servidor web com autenticação..."
echo "📍 Acesse: http://localhost:5000"
echo "🔑 Login padrão: admin / admin123"
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

# Configurar PATH para usar pip atualizado
export PATH="/root/.local/bin:$PATH"

# Iniciar aplicação com autenticação
python3 app_secure.py
