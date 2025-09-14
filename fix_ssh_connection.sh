#!/bin/bash

# 🔧 Script para diagnosticar e corrigir problemas de SSH no deploy GCP
# Este script ajuda a resolver problemas de "Permission denied (publickey)"

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

# Configurações
SSH_KEY="$HOME/.ssh/gcp-deploy"
GCP_VM_IP="35.196.129.74"
GCP_VM_USER="gcp-user"

echo "🔧 DIAGNÓSTICO E CORREÇÃO SSH"
echo "============================="
echo ""

# 1. Verificar se chave SSH existe
print_status "1. Verificando se chave SSH existe..."
if [ -f "$SSH_KEY" ]; then
    print_success "Chave SSH encontrada: $SSH_KEY"
    
    # Verificar permissões
    PERMS=$(stat -c "%a" "$SSH_KEY")
    if [ "$PERMS" = "600" ]; then
        print_success "Permissões da chave estão corretas (600)"
    else
        print_warning "Permissões da chave incorretas: $PERMS"
        print_status "Corrigindo permissões..."
        chmod 600 "$SSH_KEY"
        print_success "Permissões corrigidas para 600"
    fi
else
    print_error "Chave SSH não encontrada: $SSH_KEY"
    print_status "Execute primeiro: ssh-keygen -t rsa -b 4096 -f $SSH_KEY"
    exit 1
fi

# 2. Verificar se chave tem passphrase
print_status "2. Verificando se chave tem passphrase..."
if ssh-keygen -y -f "$SSH_KEY" >/dev/null 2>&1; then
    print_success "Chave SSH não tem passphrase (ideal para automação)"
else
    print_error "Chave SSH tem passphrase ou está corrompida"
    echo ""
    print_status "SOLUÇÕES PARA CHAVE COM PASSPHRASE:"
    echo ""
    echo "🔑 OPÇÃO 1 - Remover passphrase (RECOMENDADO para deploy automático):"
    echo "   ssh-keygen -p -f $SSH_KEY"
    echo "   (Digite a passphrase atual, depois ENTER duas vezes para remover)"
    echo ""
    echo "🔑 OPÇÃO 2 - Usar ssh-agent (para uso manual):"
    echo "   eval \$(ssh-agent -s)"
    echo "   ssh-add $SSH_KEY"
    echo ""
    echo "🔑 OPÇÃO 3 - Criar nova chave sem passphrase:"
    echo "   ssh-keygen -t rsa -b 4096 -f $SSH_KEY -N ''"
    echo "   (Isso substituirá a chave atual!)"
    echo ""
    
    read -p "Deseja remover a passphrase agora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removendo passphrase..."
        ssh-keygen -p -f "$SSH_KEY"
        print_success "Execute o script novamente para continuar"
        exit 0
    else
        print_warning "Mantenha a passphrase, mas configure o ssh-agent para uso manual"
        exit 1
    fi
fi

# 3. Verificar conectividade básica
print_status "3. Testando conectividade básica com a VM..."
if ping -c 1 -W 5 "$GCP_VM_IP" >/dev/null 2>&1; then
    print_success "VM responde ao ping"
else
    print_error "VM não responde ao ping"
    print_status "Verifique:"
    print_status "- VM está ligada no Google Cloud Console"
    print_status "- IP está correto: $GCP_VM_IP"
    print_status "- Firewall permite ICMP"
fi

# 4. Testar conexão SSH com debug
print_status "4. Testando conexão SSH..."
print_status "Executando: ssh -i $SSH_KEY -o ConnectTimeout=10 -v $GCP_VM_USER@$GCP_VM_IP 'echo Conexao OK'"
echo ""

if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
   "$GCP_VM_USER@$GCP_VM_IP" "echo 'Conexão SSH OK'" 2>/dev/null; then
    print_success "✅ Conexão SSH funcionando!"
else
    print_error "❌ Falha na conexão SSH"
    echo ""
    print_status "Executando diagnóstico detalhado..."
    echo ""
    
    # Executar com verbose para diagnóstico
    ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no -v \
        "$GCP_VM_USER@$GCP_VM_IP" "echo 'Teste'" 2>&1 | head -20
    
    echo ""
    print_status "POSSÍVEIS SOLUÇÕES:"
    echo ""
    echo "🔧 1. Verificar se a chave pública está no servidor:"
    echo "   - Acesse o Google Cloud Console"
    echo "   - VM instances → $GCP_VM_USER → Edit"
    echo "   - SSH Keys → Add SSH Key"
    echo "   - Cole o conteúdo de: $SSH_KEY.pub"
    echo ""
    echo "🔧 2. Verificar configuração do servidor SSH:"
    echo "   - Conecte via console do GCP"
    echo "   - Verifique: sudo systemctl status ssh"
    echo "   - Verifique: sudo cat /etc/ssh/sshd_config | grep -E 'PubkeyAuthentication|PasswordAuthentication'"
    echo ""
    echo "🔧 3. Verificar logs do servidor:"
    echo "   - No servidor: sudo tail -f /var/log/auth.log"
    echo "   - Execute este script novamente em outro terminal"
    echo ""
    echo "🔧 4. Recriar chave SSH:"
    echo "   ssh-keygen -t rsa -b 4096 -f $SSH_KEY -N ''"
    echo "   cat $SSH_KEY.pub  # Copie e adicione no GCP"
    echo ""
fi

# 5. Mostrar chave pública para facilitar configuração
print_status "5. Chave pública para adicionar no GCP:"
echo ""
if [ -f "$SSH_KEY.pub" ]; then
    echo "📋 Copie esta chave e adicione no Google Cloud Console:"
    echo "----------------------------------------"
    cat "$SSH_KEY.pub"
    echo "----------------------------------------"
    echo ""
    echo "🌐 Como adicionar no GCP:"
    echo "1. Acesse: https://console.cloud.google.com/compute/instances"
    echo "2. Clique na VM: $GCP_VM_USER"
    echo "3. Clique em 'Edit' (✏️)"
    echo "4. Role até 'SSH Keys'"
    echo "5. Clique 'Add SSH Key'"
    echo "6. Cole a chave acima"
    echo "7. Salve as alterações"
else
    print_error "Arquivo de chave pública não encontrado: $SSH_KEY.pub"
    print_status "Recrie a chave com: ssh-keygen -t rsa -b 4096 -f $SSH_KEY"
fi

echo ""
print_status "🔄 Após configurar a chave no GCP, execute novamente:"
echo "   ./fix_ssh_connection.sh"
echo ""
print_status "🚀 Para fazer o deploy, execute:"
echo "   ./deploy-gcp-local.sh"