#!/bin/bash

# 🚀 Script de Instalação - Analisador de PDFs com Autenticação
# Para AWS EC2 Ubuntu 22.04 LTS

set -e

echo "🚀 INSTALANDO ANALISADOR DE PDFs - AWS FREE TIER"
echo "================================================"

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

# Verificar se é Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    print_error "Este script é para Ubuntu. Abortando."
    exit 1
fi

print_status "Detectado Ubuntu $(lsb_release -rs)"

# Atualizar sistema
print_status "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y
print_success "Sistema atualizado"

# Instalar dependências básicas
print_status "Instalando dependências básicas..."
sudo apt install -y curl wget git unzip python3 python3-pip python3-venv
print_success "Dependências básicas instaladas"

# Instalar Docker
print_status "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker instalado"
else
    print_success "Docker já instalado"
fi

# Instalar Docker Compose
print_status "Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose instalado"
else
    print_success "Docker Compose já instalado"
fi

# Configurar firewall UFW
print_status "Configurando firewall UFW..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
print_success "Firewall configurado"

# Instalar Fail2Ban
print_status "Instalando Fail2Ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
print_success "Fail2Ban instalado e configurado"

# Configurar swap (importante para t2.micro)
print_status "Configurando swap de 2GB..."
if [[ ! -f /swapfile ]]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    print_success "Swap configurado"
else
    print_success "Swap já configurado"
fi

# Criar diretório da aplicação
APP_DIR="/home/$USER/analisador-pdfs"
print_status "Criando diretório da aplicação: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Se os arquivos não estão no diretório atual, instruir o usuário
if [[ ! -f "docker-compose.yml" ]]; then
    print_warning "Arquivos da aplicação não encontrados no diretório atual."
    print_status "Você precisa transferir os arquivos da aplicação para: $APP_DIR"
    print_status ""
    print_status "Opções:"
    print_status "1. Via Git: git clone <seu-repositorio> ."
    print_status "2. Via SCP: scp -r /caminho/local/* $USER@$(curl -s http://checkip.amazonaws.com):$APP_DIR/"
    print_status "3. Via upload manual"
    print_status ""
    print_warning "Execute este script novamente após transferir os arquivos."
    exit 0
fi

# Configurar ambiente
print_status "Configurando ambiente..."
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_warning "Arquivo .env criado a partir do exemplo."
        print_warning "EDITE o arquivo .env antes de continuar!"
        print_status "Especialmente:"
        print_status "- SECRET_KEY: $(python3 -c 'import secrets; print(secrets.token_hex(32))')"
        print_status "- MONGODB_URI: sua string de conexão MongoDB Atlas"
        print_status "- FLASK_ENV: production"
        print_status ""
        print_status "Após editar .env, execute: python3 start_production.py"
        exit 0
    else
        print_error "Arquivo .env.example não encontrado!"
        exit 1
    fi
fi

# Verificar se .env foi editado
if grep -q "your-secret-key-here-change-in-production" .env; then
    print_error "Você precisa editar o arquivo .env primeiro!"
    print_status "Edite .env e altere pelo menos a SECRET_KEY"
    exit 1
fi

# Criar diretórios necessários
print_status "Criando diretórios necessários..."
mkdir -p uploads logs ssl backups
print_success "Diretórios criados"

# Instalar Certbot (para SSL)
print_status "Instalando Certbot para SSL..."
sudo apt install -y certbot
print_success "Certbot instalado"

# Configurar cron para backup
print_status "Configurando backup automático..."
cat > backup.sh << 'EOF'
#!/bin/bash
# Script de backup automático

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/$(whoami)/analisador-pdfs/backups"
APP_DIR="/home/$(whoami)/analisador-pdfs"

mkdir -p $BACKUP_DIR

# Backup dos dados de usuários
if [[ -f $APP_DIR/users.json ]]; then
    cp $APP_DIR/users.json $BACKUP_DIR/users_$DATE.json
fi

# Backup dos uploads
if [[ -d $APP_DIR/uploads ]]; then
    tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $APP_DIR uploads/
fi

# Backup das configurações (sem senhas)
if [[ -f $APP_DIR/.env ]]; then
    grep -v "PASSWORD\|SECRET\|KEY" $APP_DIR/.env > $BACKUP_DIR/env_$DATE.backup
fi

# Limpar backups antigos (manter 7 dias)
find $BACKUP_DIR -name "*.json" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup concluído: $DATE"
EOF

chmod +x backup.sh

# Adicionar ao cron
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh >> /var/log/backup.log 2>&1") | crontab -
print_success "Backup automático configurado (diário às 2h)"

# Script de monitoramento
print_status "Configurando monitoramento..."
cat > monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoramento

cd "$(dirname "$0")"

# Verificar se containers estão rodando
if ! docker-compose ps | grep -q "Up"; then
    echo "$(date): ALERTA: Containers não estão rodando! Reiniciando..."
    docker-compose up -d
fi

# Verificar espaço em disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): ALERTA: Uso de disco alto: ${DISK_USAGE}%"
fi

# Verificar memória
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "$(date): ALERTA: Uso de memória alto: ${MEM_USAGE}%"
fi
EOF

chmod +x monitor.sh

# Adicionar monitoramento ao cron (a cada 5 minutos)
(crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/monitor.sh >> /var/log/monitor.log 2>&1") | crontab -
print_success "Monitoramento configurado"

# Configurar logrotate
print_status "Configurando rotação de logs..."
sudo tee /etc/logrotate.d/analisador-pdfs > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 $USER $USER
}
EOF
print_success "Rotação de logs configurada"

# Reiniciar para aplicar mudanças do Docker group
print_status "Verificando se precisa reiniciar..."
if groups $USER | grep -q docker; then
    print_success "Usuário já no grupo docker"
else
    print_warning "Você precisa fazer logout/login ou reiniciar para aplicar as mudanças do grupo docker"
    print_status "Execute 'newgrp docker' ou reinicie a sessão"
fi

# Instruções finais
print_success "Instalação básica concluída!"
print_status ""
print_status "📋 PRÓXIMOS PASSOS:"
print_status "1. Configure MongoDB Atlas (gratuito): https://www.mongodb.com/atlas"
print_status "2. Edite o arquivo .env com suas configurações"
print_status "3. Execute: python3 start_production.py"
print_status "4. Configure SSL: sudo certbot certonly --standalone -d seu-dominio.com"
print_status "5. Configure DNS apontando para este servidor"
print_status ""
print_status "🔧 ARQUIVOS IMPORTANTES:"
print_status "- $APP_DIR/.env (configurações)"
print_status "- $APP_DIR/users.json (banco de usuários)"
print_status "- $APP_DIR/docker-compose.yml (containers)"
print_status ""
print_status "📊 MONITORAMENTO:"
print_status "- Backup automático: diário às 2h"
print_status "- Monitoramento: a cada 5 minutos"
print_status "- Logs: $APP_DIR/logs/"
print_status ""
print_status "🌐 ACESSO:"
print_status "- Local: http://localhost"
print_status "- Externo: http://$(curl -s http://checkip.amazonaws.com)"
print_status "- Login: admin / admin123 (altere imediatamente!)"
print_status ""
print_success "Sistema pronto para produção! 🎉"