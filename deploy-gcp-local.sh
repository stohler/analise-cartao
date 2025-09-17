#!/bin/bash

# 🚀 Script de Deploy Local para GCP e2-micro
# Execute este script para testar o deploy localmente antes do GitHub Actions

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

# Configurações (ajuste conforme necessário)
GCP_VM_IP="35.196.129.74"
GCP_VM_USER="gcp-user"
SSH_KEY="$HOME/.ssh/gcp-deploy"
REMOTE_DIR="/home/gcp-user/analise-cartao"

echo "🚀 DEPLOY LOCAL PARA GCP e2-micro"
echo "=================================="
print_status "VM: $GCP_VM_USER@$GCP_VM_IP"
print_status "Diretório remoto: $REMOTE_DIR"
echo ""

# Verificar se chave SSH existe
if [ ! -f "$SSH_KEY" ]; then
    print_error "Chave SSH não encontrada: $SSH_KEY"
    print_status "Execute o setup inicial primeiro: SETUP_GCP.md"
    exit 1
fi

# Verificar conectividade
print_status "Testando conectividade com a VM..."
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
   "$GCP_VM_USER@$GCP_VM_IP" "echo 'Conexão OK'" > /dev/null 2>&1; then
    print_success "VM acessível"
else
    print_error "Não foi possível conectar à VM"
    print_status "Verifique:"
    print_status "1. VM está ligada"
    print_status "2. IP está correto: $GCP_VM_IP"
    print_status "3. Chave SSH está configurada"
    print_status "4. Firewall permite SSH"
    exit 1
fi

# Verificar se aplicação atual está rodando e parar
print_status "Parando aplicação atual..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR || { echo 'Diretório não existe, criando...'; mkdir -p $REMOTE_DIR; cd $REMOTE_DIR; }
    if [ -f docker-compose.yml ]; then
        echo 'Parando containers...'
        docker-compose down || echo 'Nenhum container rodando'
    else
        echo 'Primeira execução - sem containers para parar'
    fi
"

# Fazer backup
print_status "Fazendo backup da versão atual..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR
    BACKUP_DIR='backups/local_deploy_$(date +%Y%m%d_%H%M%S)'
    mkdir -p \$BACKUP_DIR
    
    [ -f users.json ] && cp users.json \$BACKUP_DIR/
    [ -f .env ] && cp .env \$BACKUP_DIR/
    [ -d uploads ] && cp -r uploads \$BACKUP_DIR/ 2>/dev/null || true
    
    echo 'Backup criado em' \$BACKUP_DIR
"

# Sincronizar arquivos
print_status "Enviando arquivos atualizados..."

# Criar lista de exclusões
cat > /tmp/.rsync_exclude << EOF
.git/
.github/
__pycache__/
*.pyc
.pytest_cache/
node_modules/
.env
users.json
uploads/
logs/
backups/
ssl/
.vscode/
.idea/
*.log
EOF

# Rsync otimizado
rsync -avz --delete --exclude-from=/tmp/.rsync_exclude \
    --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    ./ "$GCP_VM_USER@$GCP_VM_IP:$REMOTE_DIR/"

rm /tmp/.rsync_exclude
print_success "Arquivos sincronizados"

# Configurar ambiente
print_status "Configurando ambiente na VM..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR
    
    # Criar diretórios necessários
    mkdir -p uploads logs ssl backups
    
    # Usar docker-compose otimizado para GCP
    if [ -f docker-compose-gcp.yml ]; then
        cp docker-compose-gcp.yml docker-compose.yml
        echo 'Usando docker-compose otimizado para GCP'
    fi
    
    # Usar Dockerfile otimizado para GCP
    if [ -f Dockerfile-gcp ]; then
        cp Dockerfile-gcp Dockerfile
        echo 'Usando Dockerfile otimizado para GCP'
    fi
    
    # Usar nginx otimizado para GCP
    if [ -f nginx-gcp.conf ]; then
        cp nginx-gcp.conf nginx.conf
        echo 'Usando nginx otimizado para GCP'
    fi
    
    # Configurar .env se não existir
    if [ ! -f .env ]; then
        echo 'Criando arquivo .env básico...'
        cat > .env << 'EOL'
FLASK_ENV=production
SECRET_KEY=\$(python3 -c \"import secrets; print(secrets.token_hex(32))\")
MONGODB_URI=mongodb://localhost:27017/analise_cartao
REGISTRATION_ENABLED=false
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PORT=5000
HOST=0.0.0.0
EOL
        echo '⚠️ Configure o arquivo .env com suas credenciais!'
    fi
"

# Configurar SSL básico
print_status "Configurando SSL..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR
    
    if [ ! -f ssl/cert.pem ]; then
        echo 'Criando certificado auto-assinado...'
        mkdir -p ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj '/C=BR/ST=SP/L=SaoPaulo/O=AnalisadorPDF/CN=$GCP_VM_IP' \
            2>/dev/null
        echo 'Certificado auto-assinado criado'
    else
        echo 'Certificado SSL já existe'
    fi
"

# Limpar Docker e construir
print_status "Preparando ambiente Docker..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR
    
    # Limpar imagens antigas para economizar espaço
    docker system prune -f
    
    # Verificar recursos disponíveis
    echo '📊 Recursos disponíveis:'
    echo '  Memória:' \$(free -h | grep Mem | awk '{print \$7}')
    echo '  Disco:' \$(df -h / | tail -1 | awk '{print \$4}')
"

# Construir e iniciar
print_status "Construindo e iniciando aplicação..."
ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
    cd $REMOTE_DIR
    
    # Construir imagem
    echo '🔨 Construindo imagem otimizada...'
    docker-compose build --no-cache web
    
    # Iniciar serviços
    echo '▶️ Iniciando serviços...'
    docker-compose up -d
    
    # Aguardar inicialização
    echo '⏳ Aguardando inicialização (30s)...'
    sleep 30
    
    # Verificar status
    echo '📊 Status dos containers:'
    docker-compose ps
    
    echo ''
    echo '💾 Uso de recursos após deploy:'
    echo '  Memória:' \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')
    echo '  Swap:' \$(free -h | grep Swap | awk '{print \$3\"/\"\$2}')
    echo '  Disco:' \$(df -h / | tail -1 | awk '{print \$5 \" usado\"}')
"

# Verificar se aplicação está respondendo
print_status "Verificando se aplicação está funcionando..."
sleep 10

if curl -f -m 15 -s "http://$GCP_VM_IP/auth/login" > /dev/null; then
    print_success "✅ Aplicação está respondendo!"
    echo ""
    echo "🌐 ACESSO À APLICAÇÃO:"
    echo "  HTTP:  http://$GCP_VM_IP"
    echo "  HTTPS: https://$GCP_VM_IP (certificado auto-assinado)"
    echo ""
    echo "👤 LOGIN PADRÃO:"
    echo "  Usuário: admin"
    echo "  Senha: admin123"
    echo ""
    print_warning "⚠️ ALTERE A SENHA PADRÃO IMEDIATAMENTE!"
    echo ""
    echo "📋 COMANDOS ÚTEIS:"
    echo "  ssh -i $SSH_KEY $GCP_VM_USER@$GCP_VM_IP"
    echo "  cd $REMOTE_DIR && docker-compose logs -f"
    echo "  cd $REMOTE_DIR && docker-compose ps"
    echo ""
else
    print_error "❌ Aplicação não está respondendo"
    print_status "Verificando logs..."
    
    ssh -i "$SSH_KEY" "$GCP_VM_USER@$GCP_VM_IP" "
        cd $REMOTE_DIR
        echo '🔍 Logs da aplicação:'
        docker-compose logs --tail=20 web
        echo ''
        echo '🔍 Logs do Nginx:'
        docker-compose logs --tail=10 nginx
        echo ''
        echo '📊 Status dos containers:'
        docker-compose ps
    "
    
    exit 1
fi

print_success "🎉 Deploy local concluído com sucesso!"
print_status "A aplicação está pronta para receber deploys automáticos via GitHub Actions"