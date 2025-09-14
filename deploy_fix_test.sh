#!/bin/bash

# 🔧 Script para testar a solução do erro de tar
# Execute este script para testar a correção do erro "file changed as we read it"

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔧 TESTE DA CORREÇÃO DO ERRO TAR"
echo "================================="
echo ""

# Limpar pacotes anteriores
print_status "Limpando pacotes anteriores..."
rm -f deploy_package.tar.gz deploy_package_old.tar.gz

# Método antigo (que causa erro)
print_status "Testando método antigo (pode causar erro)..."
echo "📦 Preparando arquivos para envio (método antigo)..."

if tar --exclude='.git' \
       --exclude='.github' \
       --exclude='__pycache__' \
       --exclude='*.pyc' \
       --exclude='.env' \
       --exclude='users.json' \
       --exclude='uploads' \
       --exclude='logs' \
       --exclude='backups' \
       --exclude='.pytest_cache' \
       --exclude='node_modules' \
       --exclude='venv*' \
       -czf deploy_package_old.tar.gz . 2>/dev/null; then
    print_success "Método antigo funcionou (sem erro desta vez)"
    OLD_SIZE=$(ls -lh deploy_package_old.tar.gz | awk '{print $5}')
    echo "  Tamanho: $OLD_SIZE"
else
    print_warning "Método antigo falhou (erro esperado: 'file changed as we read it')"
fi

echo ""

# Método novo (corrigido)
print_status "Testando método novo (corrigido)..."
echo "📦 Preparando arquivos para envio (método novo)..."

# Criar diretório temporário para arquivos limpos
TEMP_DIR=$(mktemp -d)
print_status "Criando pacote limpo em: $TEMP_DIR"

# Copiar arquivos necessários para o diretório temporário
print_status "Copiando arquivos..."
if rsync -av --exclude='.git/' \
              --exclude='.github/' \
              --exclude='__pycache__/' \
              --exclude='*.pyc' \
              --exclude='.env' \
              --exclude='users.json' \
              --exclude='uploads/' \
              --exclude='logs/' \
              --exclude='backups/' \
              --exclude='.pytest_cache/' \
              --exclude='node_modules/' \
              --exclude='venv*/' \
              --exclude='*.log' \
              --exclude='session_*.json' \
              --exclude='deploy_package*.tar.gz' \
              ./ $TEMP_DIR/ > /dev/null 2>&1; then
    print_success "Arquivos copiados para diretório temporário"
else
    print_error "Erro ao copiar arquivos"
    rm -rf $TEMP_DIR
    exit 1
fi

# Criar arquivo compactado do diretório limpo
print_status "Compactando arquivos..."
if tar -czf deploy_package.tar.gz -C $TEMP_DIR . 2>/dev/null; then
    print_success "Arquivo compactado criado com sucesso"
    NEW_SIZE=$(ls -lh deploy_package.tar.gz | awk '{print $5}')
    echo "  Tamanho: $NEW_SIZE"
else
    print_error "Erro ao criar arquivo compactado"
    rm -rf $TEMP_DIR
    exit 1
fi

# Limpar diretório temporário
rm -rf $TEMP_DIR
print_success "Diretório temporário limpo"

echo ""

# Comparar resultados
print_status "Comparação dos métodos:"
if [ -f deploy_package_old.tar.gz ] && [ -f deploy_package.tar.gz ]; then
    OLD_BYTES=$(stat -f%z deploy_package_old.tar.gz 2>/dev/null || stat -c%s deploy_package_old.tar.gz)
    NEW_BYTES=$(stat -f%z deploy_package.tar.gz 2>/dev/null || stat -c%s deploy_package.tar.gz)
    
    echo "  Método antigo: $OLD_SIZE ($OLD_BYTES bytes)"
    echo "  Método novo:   $NEW_SIZE ($NEW_BYTES bytes)"
    
    if [ $NEW_BYTES -le $OLD_BYTES ]; then
        print_success "Novo método produziu arquivo igual ou menor (melhor)"
    else
        print_warning "Novo método produziu arquivo maior"
    fi
elif [ -f deploy_package.tar.gz ]; then
    echo "  Método antigo: FALHOU"
    echo "  Método novo:   $NEW_SIZE ✅"
    print_success "Apenas o novo método funcionou!"
fi

echo ""

# Testar integridade do arquivo
print_status "Testando integridade do arquivo..."
if tar -tzf deploy_package.tar.gz > /dev/null 2>&1; then
    print_success "Arquivo íntegro e válido"
    FILE_COUNT=$(tar -tzf deploy_package.tar.gz | wc -l)
    echo "  Arquivos no pacote: $FILE_COUNT"
else
    print_error "Arquivo corrompido!"
    exit 1
fi

echo ""

# Mostrar alguns arquivos incluídos
print_status "Primeiros 10 arquivos no pacote:"
tar -tzf deploy_package.tar.gz | head -10 | sed 's/^/  /'

echo ""

# Verificar se arquivos importantes estão incluídos
print_status "Verificando arquivos importantes:"
IMPORTANT_FILES=("app.py" "requirements.txt" "docker-compose.yml" "Dockerfile")
for file in "${IMPORTANT_FILES[@]}"; do
    if tar -tzf deploy_package.tar.gz | grep -q "^$file$" || tar -tzf deploy_package.tar.gz | grep -q "^./$file$"; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (AUSENTE!)"
    fi
done

echo ""

# Verificar se arquivos desnecessários foram excluídos
print_status "Verificando exclusões:"
EXCLUDED_PATTERNS=("__pycache__" "*.pyc" ".git" "session_*.json" "*.log")
FOUND_EXCLUDED=0
for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    if tar -tzf deploy_package.tar.gz | grep -q "$pattern"; then
        echo "  ⚠️ Encontrado: $pattern"
        FOUND_EXCLUDED=1
    fi
done

if [ $FOUND_EXCLUDED -eq 0 ]; then
    print_success "Nenhum arquivo desnecessário encontrado"
else
    print_warning "Alguns arquivos desnecessários podem estar incluídos"
fi

echo ""
print_success "🎉 Teste concluído!"
echo ""
print_status "Próximos passos:"
echo "1. Se o teste passou, use o método corrigido no deploy_alternative.yml"
echo "2. O arquivo deploy_package.tar.gz está pronto para envio"
echo "3. Execute o deploy real com confiança"
echo ""
print_warning "Lembre-se de limpar os arquivos de teste:"
echo "  rm -f deploy_package*.tar.gz"