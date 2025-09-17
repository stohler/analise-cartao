# 🚀 Deploy Automático no Google Cloud Platform (GCP)

Sistema completo com deploy automático via GitHub Actions para VM e2-micro do GCP Free Tier.

## 📋 Informações da Configuração

### 🖥️ **VM GCP**
- **Nome**: `analise-carta-20250914-133510`
- **Tipo**: `e2-micro` (1 vCPU, 1GB RAM, 10GB disco)
- **Zona**: `us-east1-c`
- **Projeto**: `divine-command-231619`
- **IP**: `35.196.129.74` (dinâmico)
- **SO**: Ubuntu 22.04 LTS Minimal

### 🔄 **GitHub Actions**
- **Repositório**: `stohler/analise-cartao`
- **Branch**: `main`
- **Deploy automático** a cada push
- **Testes automáticos** antes do deploy
- **Rollback** em caso de falha

## 🏗️ Arquitetura da Solução

```
GitHub Push → Actions → GCP VM e2-micro → Docker → Nginx + Flask → MongoDB Atlas
     ↓            ↓         ↓              ↓           ↓              ↓
   Testes    Deploy SSH   512MB RAM    Containers   Auth System   Cloud DB
   Validação  Automático  Otimizado    Limitados    Seguro        Gratuito
```

## ⚡ Otimizações para e2-micro

### 🧠 **Memória (1GB total)**
- **Sistema**: ~300MB
- **Docker**: ~100MB
- **Nginx**: ~50MB
- **Flask App**: ~300MB
- **Buffer**: ~250MB

### 🐳 **Docker Otimizado**
- **1 worker Gunicorn** + 2 threads
- **Limites de memória** por container
- **Health checks** otimizados
- **Imagem multi-stage** build

### 🌐 **Nginx Otimizado**
- **1 worker process** (1 vCPU)
- **512 connections** máximo
- **Buffers reduzidos** para economizar RAM
- **Gzip compressão** ativa
- **Rate limiting** configurado

## 🚀 Configuração Inicial

### Passo 1: Preparar VM GCP

Execute o guia completo: **[SETUP_GCP.md](SETUP_GCP.md)**

Resumo dos passos principais:
1. ✅ Criar Service Account
2. ✅ Configurar chaves SSH
3. ✅ Configurar firewall
4. ✅ Instalar Docker na VM
5. ✅ Configurar swap para e2-micro

### Passo 2: Configurar GitHub Secrets

No repositório `stohler/analise-cartao`, adicionar em **Settings → Secrets and Variables → Actions**:

```bash
GCP_PROJECT_ID=divine-command-231619
GCP_SERVICE_ACCOUNT_KEY={json completo da service account}
GCP_VM_NAME=analise-carta-20250914-133510
GCP_VM_ZONE=us-east1-c
GCP_VM_USER=gcp-user
GCP_VM_IP=35.196.129.74
SSH_PRIVATE_KEY={chave privada SSH completa}
SECRET_KEY={chave gerada com: python -c "import secrets; print(secrets.token_hex(32))"}
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### Passo 3: Testar Deploy Local

```bash
# Executar deploy local para testar
./deploy-gcp-local.sh
```

## 🔄 Fluxo de Deploy Automático

### 1. **Trigger**
- Push para branch `main`
- Pull Request merged para `main`

### 2. **Testes (sempre executados)**
- ✅ Validação de sintaxe Python
- ✅ Verificação de configurações Docker
- ✅ Validação de templates HTML
- ✅ Verificação de segurança (.env)

### 3. **Deploy (só se testes passaram)**
- 🔐 Autenticação GCP
- 🏥 Verificação de saúde da VM
- 🛑 Parada da aplicação atual
- 💾 Backup automático
- 📤 Sincronização de código
- ⚙️ Configuração de ambiente
- 🐳 Build otimizado para e2-micro
- 🔒 Configuração SSL automática
- 🚀 Inicialização dos serviços
- 🔍 Verificação de funcionamento

### 4. **Notificação**
- ✅ Sucesso: URL de acesso
- ❌ Falha: Logs de erro

## 📊 Monitoramento e Logs

### **Status da Aplicação**
```bash
# Conectar à VM
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Verificar containers
cd /home/gcp-user/analise-cartao
docker-compose ps

# Ver logs
docker-compose logs -f web
docker-compose logs nginx
```

### **Recursos da VM**
```bash
# Memória
free -h

# Disco
df -h

# CPU
top

# Processos Docker
docker stats
```

### **Health Checks**
- **Endpoint**: `http://35.196.129.74/health`
- **Login**: `http://35.196.129.74/auth/login`
- **Status**: `docker-compose ps`

## 🔧 Comandos Úteis

### **Deploy e Manutenção**
```bash
# Deploy local (teste)
./deploy-gcp-local.sh

# Conectar à VM
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Reiniciar aplicação
cd /home/gcp-user/analise-cartao
docker-compose restart

# Ver logs em tempo real
docker-compose logs -f

# Parar aplicação
docker-compose down

# Iniciar aplicação
docker-compose up -d

# Limpar espaço (cuidado!)
docker system prune -f
```

### **Backup e Recuperação**
```bash
# Backup manual
cd /home/gcp-user/analise-cartao
./backup.sh

# Restaurar backup
cp backups/users_YYYYMMDD.json users.json
tar -xzf backups/uploads_YYYYMMDD.tar.gz
```

### **SSL/HTTPS**
```bash
# Certificado auto-assinado (padrão)
# Já configurado automaticamente

# Let's Encrypt (para domínio real)
sudo certbot certonly --standalone -d seu-dominio.com
sudo cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem ssl/key.pem
sudo chown gcp-user:gcp-user ssl/*
docker-compose restart nginx
```

## 🔍 Troubleshooting

### **Deploy Falhou**
1. **Verificar logs do GitHub Actions**
2. **Conectar à VM e verificar**:
   ```bash
   ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74
   cd /home/gcp-user/analise-cartao
   docker-compose logs
   ```

### **Aplicação Não Responde**
```bash
# Verificar containers
docker-compose ps

# Reiniciar se necessário
docker-compose restart

# Verificar recursos
free -h
df -h
```

### **Pouca Memória**
```bash
# Verificar uso
docker stats

# Limpar cache
docker system prune -f

# Reiniciar VM (último recurso)
sudo reboot
```

### **Erro de SSH**
```bash
# Testar conexão
ssh -i ~/.ssh/gcp-deploy gcp-user@35.196.129.74

# Verificar chave no GCP Console
# Compute Engine → VM → Edit → SSH Keys
```

### **Erro de Firewall**
```bash
# Verificar regras
gcloud compute firewall-rules list

# Adicionar se necessário
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 --source-ranges 0.0.0.0/0 --target-tags http-server

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 --source-ranges 0.0.0.0/0 --target-tags https-server
```

## 💰 Custos GCP Free Tier

### **Always Free (permanente)**
- ✅ **e2-micro VM**: 1 instância por mês
- ✅ **30GB disco**: SSD persistente
- ✅ **1GB tráfego**: América do Norte/mês
- ✅ **MongoDB Atlas M0**: 512MB (separado)

### **Custos Adicionais (se exceder)**
- **VM e2-micro**: ~$6/mês (após free tier)
- **Disco adicional**: ~$0.04/GB/mês
- **Tráfego**: ~$0.12/GB (após 1GB)
- **IP estático**: ~$1.46/mês (opcional)

### **Dicas para Economizar**
- ✅ Parar VM quando não usar
- ✅ Usar MongoDB Atlas (gratuito)
- ✅ Configurar alertas de budget
- ✅ Monitorar uso no Console GCP

## 🔐 Checklist de Segurança

- ✅ **Autenticação** obrigatória em todas as rotas
- ✅ **HTTPS** configurado (auto-assinado)
- ✅ **Firewall** configurado (apenas 22, 80, 443)
- ✅ **Rate limiting** ativo no Nginx
- ✅ **Headers de segurança** configurados
- ✅ **Usuário não-root** no Docker
- ✅ **Service Account** com permissões mínimas
- ✅ **SSH com chave** (sem senha)
- ✅ **Secrets** protegidos no GitHub
- ✅ **Logs** de auditoria ativos

## 📈 Performance e Otimizações

### **Configurações Aplicadas**
- ✅ **Swap 1GB** para e2-micro
- ✅ **Gunicorn 1 worker + 2 threads**
- ✅ **Nginx 1 worker, 512 connections**
- ✅ **Gzip compression** ativo
- ✅ **Docker memory limits** configurados
- ✅ **Health checks** otimizados
- ✅ **Cache estático** 7 dias

### **Métricas Esperadas**
- **Tempo de resposta**: < 2s
- **Uso de memória**: ~70% (700MB/1GB)
- **Uso de CPU**: < 50% (normal)
- **Concurrent users**: ~10-15
- **Uptime**: > 99%

## 🎯 Próximos Passos

### **Melhorias Futuras**
- [ ] **Domínio personalizado** + Let's Encrypt
- [ ] **Load balancer** (se necessário)
- [ ] **CDN** para arquivos estáticos
- [ ] **Backup automático** para Cloud Storage
- [ ] **Monitoring** com Cloud Logging
- [ ] **Alertas** de performance
- [ ] **Blue-green deployment**

### **Escalabilidade**
- [ ] **Cloud Run** (serverless)
- [ ] **GKE Autopilot** (Kubernetes)
- [ ] **Cloud SQL** (PostgreSQL)
- [ ] **Cloud Storage** (uploads)
- [ ] **Cloud CDN** (performance)

## 🆘 Suporte e Documentação

### **Links Úteis**
- [GCP Free Tier](https://cloud.google.com/free)
- [Compute Engine Docs](https://cloud.google.com/compute/docs)
- [GitHub Actions](https://docs.github.com/actions)
- [Docker Compose](https://docs.docker.com/compose/)

### **Arquivos Importantes**
- `SETUP_GCP.md` - Configuração inicial detalhada
- `.github/workflows/deploy-gcp.yml` - Pipeline de deploy
- `docker-compose-gcp.yml` - Configuração otimizada
- `Dockerfile-gcp` - Imagem otimizada
- `nginx-gcp.conf` - Proxy otimizado
- `deploy-gcp-local.sh` - Deploy local para testes

---

## 🎉 Resumo

✅ **Sistema completo** com autenticação segura  
✅ **Deploy automático** via GitHub Actions  
✅ **Otimizado para e2-micro** (512MB RAM)  
✅ **Free Tier GCP** (custo zero)  
✅ **SSL/HTTPS** configurado  
✅ **Monitoramento** e logs  
✅ **Backup automático**  
✅ **Documentação completa**  

**Acesso**: http://35.196.129.74  
**Login**: admin / admin123 ⚠️ (altere imediatamente!)

**🚀 Push para `main` = Deploy automático!**