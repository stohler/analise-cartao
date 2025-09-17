# 🔧 Configuração Inicial GCP - VM e2-micro

Este guia configura sua VM GCP para receber deploys automáticos via GitHub Actions.

## 📋 Informações da VM
- **VM**: `analise-carta-20250914-133510`
- **Zona**: `us-east1-c`
- **Projeto**: `divine-command-231619`
- **IP**: `35.196.129.74`
- **SO**: Ubuntu 22.04 LTS Minimal
- **Usuário**: `gcp-user`

## 🔑 Passo 1: Configurar Service Account

### 1.1 Criar Service Account no Console GCP

1. **Acesse**: https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Selecione projeto**: `divine-command-231619`
3. **Criar Service Account**:
   - **Nome**: `github-actions-deploy`
   - **ID**: `github-actions-deploy`
   - **Descrição**: `Service Account para deploy via GitHub Actions`

### 1.2 Conceder Permissões

Adicione as seguintes roles à Service Account:
- **Compute Instance Admin (v1)**: `roles/compute.instanceAdmin.v1`
- **Service Account User**: `roles/iam.serviceAccountUser`
- **Compute OS Login**: `roles/compute.osLogin`

### 1.3 Gerar Chave JSON

1. **Clique na Service Account criada**
2. **Aba "Keys"** → **Add Key** → **Create New Key**
3. **Tipo**: JSON
4. **Download** do arquivo JSON (será usado no GitHub)

## 🔐 Passo 2: Configurar SSH

### 2.1 Gerar Par de Chaves SSH

Execute no seu computador local:

```bash
# Gerar chave SSH específica para deploy
ssh-keygen -t rsa -b 4096 -C "github-actions@analise-cartao" -f ~/.ssh/gcp-deploy

# Isso criará:
# ~/.ssh/gcp-deploy (chave privada - para GitHub Secrets)
# ~/.ssh/gcp-deploy.pub (chave pública - para GCP)
```

### 2.2 Adicionar Chave Pública à VM

```bash
# Ver conteúdo da chave pública
cat ~/.ssh/gcp-deploy.pub

# Copie o conteúdo completo
```

**No Console GCP**:
1. **Compute Engine** → **VM Instances**
2. **Clique na VM** `analise-carta-20250914-133510`
3. **Editar**
4. **SSH Keys** → **Add Item**
5. **Cole a chave pública completa**
6. **Salvar**

### 2.3 Testar Conexão SSH

```bash
# Testar conexão
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Se conectar com sucesso, sair
exit
```

## 🔥 Passo 3: Configurar Firewall

### 3.1 Verificar Tags da VM

```bash
# No Cloud Shell ou gcloud CLI local
gcloud compute instances describe analise-carta-20250914-133510 \
    --zone=us-east1-c \
    --project=divine-command-231619 \
    --format="value(tags.items)"
```

### 3.2 Adicionar Tags se Necessário

```bash
# Adicionar tags http-server e https-server
gcloud compute instances add-tags analise-carta-20250914-133510 \
    --tags=http-server,https-server \
    --zone=us-east1-c \
    --project=divine-command-231619
```

### 3.3 Verificar Regras de Firewall

```bash
# Verificar se as regras existem
gcloud compute firewall-rules list --filter="name:(default-allow-http OR default-allow-https)"
```

Se não existirem, criar:

```bash
# Criar regra HTTP
gcloud compute firewall-rules create default-allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server \
    --description "Allow HTTP traffic"

# Criar regra HTTPS
gcloud compute firewall-rules create default-allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server \
    --description "Allow HTTPS traffic"
```

## 📦 Passo 4: Preparar VM para Deploy

### 4.1 Conectar à VM

```bash
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74
```

### 4.2 Instalar Dependências Básicas

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y curl wget git unzip python3 python3-pip

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar para aplicar mudanças do grupo docker
sudo reboot
```

### 4.3 Configurar Diretório da Aplicação

```bash
# Conectar novamente após reboot
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Criar diretório
mkdir -p /home/gcp-user/analise-cartao
cd /home/gcp-user/analise-cartao

# Criar estrutura básica
mkdir -p uploads logs ssl backups
```

### 4.4 Configurar Swap (importante para e2-micro com 512MB RAM)

```bash
# Criar swap de 1GB (adequado para e2-micro)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Configurar swappiness para e2-micro
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

## 🔐 Passo 5: Configurar GitHub Secrets

No seu repositório GitHub (`stohler/analise-cartao`):

### 5.1 Acessar Settings → Secrets and Variables → Actions

### 5.2 Adicionar os seguintes Repository Secrets:

**GCP_PROJECT_ID**:
```
divine-command-231619
```

**GCP_SERVICE_ACCOUNT_KEY**:
```
{
  "type": "service_account",
  "project_id": "divine-command-231619",
  ...
  // Cole aqui o conteúdo completo do arquivo JSON baixado
}
```

**GCP_VM_NAME**:
```
analise-carta-20250914-133510
```

**GCP_VM_ZONE**:
```
us-east1-c
```

**GCP_VM_USER**:
```
gcp-user
```

**GCP_VM_IP**:
```
35.196.129.74
```

**SSH_PRIVATE_KEY**:
```
-----BEGIN OPENSSH PRIVATE KEY-----
// Cole aqui o conteúdo completo de ~/.ssh/gcp-deploy (chave privada)
-----END OPENSSH PRIVATE KEY-----
```

**SECRET_KEY** (para a aplicação):
```bash
# Gerar uma chave forte
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**MONGODB_URI**:
```
mongodb+srv://usuario:senha@cluster.mongodb.net/?retryWrites=true&w=majority&appName=AppName
```

## ✅ Passo 6: Verificação

### 6.1 Testar Conexão SSH do GitHub

```bash
# No seu computador local, simular conexão do GitHub Actions
ssh -i ~/.ssh/gcp-deploy -o StrictHostKeyChecking=no gcp-user@35.196.129.74 "echo 'Conexão OK'"
```

### 6.2 Verificar Docker

```bash
# Na VM
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Testar Docker
docker --version
docker-compose --version

# Testar permissões
docker run hello-world
```

### 6.3 Verificar Recursos da VM

```bash
# Verificar memória e swap
free -h

# Verificar espaço em disco
df -h

# Verificar CPU
nproc
```

## 🎯 Próximos Passos

Após completar esta configuração:

1. ✅ **Service Account criada e configurada**
2. ✅ **SSH configurado entre GitHub Actions e VM**
3. ✅ **Firewall configurado para HTTP/HTTPS**
4. ✅ **VM preparada com Docker e dependências**
5. ✅ **GitHub Secrets configurados**

**Agora você pode**:
- Fazer push para branch `main` e o deploy será automático
- Acessar a aplicação via `http://35.196.129.74`
- SSL será configurado automaticamente no primeiro deploy

## 🆘 Troubleshooting

### Erro de Conexão SSH
```bash
# Verificar se a chave foi adicionada corretamente
gcloud compute instances describe analise-carta-20250914-133510 \
    --zone=us-east1-c \
    --format="value(metadata.items[ssh-keys])"
```

### Erro de Permissões Docker
```bash
# Na VM, verificar se usuário está no grupo docker
groups $USER
# Se não estiver, adicionar e reiniciar sessão
sudo usermod -aG docker $USER
```

### VM com Pouca Memória
```bash
# Verificar uso de memória
free -h
# Verificar processos que mais consomem
top -o %MEM
```

## 📊 Monitoramento Básico

### Script de Status (opcional)
```bash
# Criar script de status
cat > /home/gcp-user/status.sh << 'EOF'
#!/bin/bash
echo "=== STATUS DA VM ==="
echo "Data: $(date)"
echo "Uptime: $(uptime)"
echo "Memória: $(free -h | grep Mem)"
echo "Disco: $(df -h / | tail -1)"
echo "Docker: $(docker ps --format 'table {{.Names}}\t{{.Status}}')"
EOF

chmod +x /home/gcp-user/status.sh
```

Configuração inicial completa! 🎉