# 🚀 Início Rápido - Deploy GCP com GitHub Actions

Guia rápido para colocar o sistema no ar em **menos de 30 minutos**.

## ✅ Pré-requisitos

- ✅ Conta Google Cloud Platform
- ✅ VM e2-micro criada (`analise-carta-20250914-133510`)
- ✅ Repositório GitHub (`stohler/analise-cartao`)
- ✅ MongoDB Atlas configurado

## 🚀 Passos Rápidos

### 1️⃣ **Verificar Pré-requisitos** (2 min)

```bash
python3 check-requirements.py
```

### 2️⃣ **Configurar Service Account GCP** (5 min)

1. **Console GCP** → **IAM & Admin** → **Service Accounts**
2. **Criar Service Account**: `github-actions-deploy`
3. **Roles**: 
   - `Compute Instance Admin (v1)`
   - `Service Account User`
   - `Compute OS Login`
4. **Gerar chave JSON** e baixar

### 3️⃣ **Configurar SSH** (3 min)

```bash
# Gerar chave SSH
ssh-keygen -t rsa -b 4096 -C "github-actions@analise-cartao" -f ~/.ssh/gcp-deploy

# Ver chave pública
cat ~/.ssh/gcp-deploy.pub
```

**No Console GCP**:
- **Compute Engine** → **VM** → **Edit** → **SSH Keys** → **Add Item**
- Colar chave pública

### 4️⃣ **Configurar GitHub Secrets** (5 min)

**GitHub** → **stohler/analise-cartao** → **Settings** → **Secrets and Variables** → **Actions**

Adicionar secrets:

```bash
GCP_PROJECT_ID=divine-command-231619
GCP_VM_NAME=analise-carta-20250914-133510
GCP_VM_ZONE=us-east1-c
GCP_VM_USER=gcp-user
GCP_VM_IP=35.196.129.74
```

```json
GCP_SERVICE_ACCOUNT_KEY=
{
  "type": "service_account",
  "project_id": "divine-command-231619",
  ...
}
```

```bash
SSH_PRIVATE_KEY=
-----BEGIN OPENSSH PRIVATE KEY-----
(conteúdo de ~/.ssh/gcp-deploy)
-----END OPENSSH PRIVATE KEY-----
```

```bash
# Gerar chave forte
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Sua string MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### 5️⃣ **Preparar VM** (10 min)

```bash
# Conectar à VM
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Executar setup básico
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configurar swap para e2-micro
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Criar diretório
mkdir -p /home/gcp-user/analise-cartao

# Sair e reconectar (aplicar grupo docker)
exit
```

### 6️⃣ **Deploy Automático** (5 min)

```bash
# No seu computador local, no repositório
git add .
git commit -m "feat: configurar deploy automático GCP"
git push origin main
```

**Acompanhar deploy**:
- GitHub → **Actions** → Ver workflow rodando
- Deploy automático em ~3-5 minutos

## 🎯 Verificação Final

### **1. Status do Deploy**
```bash
# Verificar no GitHub Actions
https://github.com/stohler/analise-cartao/actions
```

### **2. Testar Aplicação**
```bash
# Testar endpoint
curl -f http://35.196.129.74/auth/login
```

### **3. Acessar Sistema**
- **URL**: http://35.196.129.74
- **HTTPS**: https://35.196.129.74 (certificado auto-assinado)
- **Login**: `admin` / `admin123` ⚠️ **ALTERE IMEDIATAMENTE!**

## 🔧 Comandos Úteis

```bash
# Conectar à VM
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Ver status dos containers
cd /home/gcp-user/analise-cartao
docker-compose ps

# Ver logs
docker-compose logs -f web

# Reiniciar aplicação
docker-compose restart

# Deploy local (teste)
./deploy-gcp-local.sh
```

## 🆘 Problemas Comuns

### **Deploy Falhou**
```bash
# 1. Verificar secrets GitHub
# 2. Verificar conectividade SSH
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# 3. Ver logs do workflow GitHub
```

### **VM Não Responde**
```bash
# Verificar se VM está ligada no Console GCP
# Verificar firewall rules
gcloud compute firewall-rules list
```

### **Erro de Memória**
```bash
# Na VM, verificar recursos
free -h
docker stats

# Reiniciar se necessário
sudo reboot
```

## 🎉 Sucesso!

Se tudo funcionou:

✅ **Sistema no ar** em http://35.196.129.74  
✅ **Deploy automático** configurado  
✅ **Custo**: $0/mês (Free Tier)  
✅ **Push = Deploy** automático  

### **Próximos Passos**
1. **Alterar senha padrão** imediatamente
2. **Configurar MongoDB Atlas** se ainda não fez
3. **Testar upload de PDFs**
4. **Configurar domínio próprio** (opcional)
5. **SSL com Let's Encrypt** (opcional)

---

**🚀 Em menos de 30 minutos você tem um sistema completo rodando no GCP com deploy automático!**

**Documentação completa**: [DEPLOY_GCP.md](DEPLOY_GCP.md)