# 🚀 Guia de Deploy no AWS Free Tier

Este guia detalha como fazer o deploy do Analisador de PDFs com autenticação no AWS Free Tier usando EC2, com todas as configurações de segurança e produção.

## 📋 Pré-requisitos

- Conta AWS (Free Tier)
- MongoDB Atlas (gratuito) ou MongoDB local
- Domínio (opcional, mas recomendado para HTTPS)
- Conhecimentos básicos de Linux e AWS

## 🏗️ Arquitetura da Solução

```
Internet → Route 53 (DNS) → EC2 (Nginx + Docker) → MongoDB Atlas
                                    ↓
                               Aplicação Flask
                                    ↓
                               Armazenamento Local
```

## 🎯 Passo 1: Configurar EC2 Instance

### 1.1 Criar Instância EC2

1. **Acesse o Console AWS EC2**
2. **Launch Instance**:
   - **AMI**: Ubuntu Server 22.04 LTS (Free Tier)
   - **Instance Type**: t2.micro (Free Tier)
   - **Key Pair**: Crie ou use uma existente
   - **Security Group**: Configure as portas:
     - SSH (22) - Seu IP
     - HTTP (80) - 0.0.0.0/0
     - HTTPS (443) - 0.0.0.0/0
     - Custom (5000) - Apenas para testes iniciais

### 1.2 Conectar à Instância

```bash
# Conectar via SSH
ssh -i sua-chave.pem ubuntu@seu-ip-publico

# Atualizar sistema
sudo apt update && sudo apt upgrade -y
```

## 🐳 Passo 2: Instalar Docker e Docker Compose

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar sessão para aplicar mudanças
exit
# Conectar novamente via SSH
```

## 📁 Passo 3: Preparar Aplicação

### 3.1 Clonar/Transferir Código

```bash
# Opção 1: Se usando Git
git clone https://github.com/seu-usuario/analisador-pdfs.git
cd analisador-pdfs

# Opção 2: Transferir arquivos via SCP
# No seu computador local:
scp -i sua-chave.pem -r . ubuntu@seu-ip-publico:~/analisador-pdfs/
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

**Configurações importantes para produção:**

```env
# Ambiente de execução
FLASK_ENV=production

# Chave secreta (GERE UMA CHAVE FORTE!)
SECRET_KEY=sua-chave-secreta-super-forte-aqui

# MongoDB Atlas
MONGODB_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/?retryWrites=true&w=majority&appName=AppName

# Configurações de segurança
SESSION_COOKIE_SECURE=true
REGISTRATION_ENABLED=false  # Desabilitar registro em produção

# Servidor
PORT=5000
HOST=0.0.0.0
```

### 3.3 Gerar Chave Secreta Forte

```bash
# Gerar chave secreta
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 🗄️ Passo 4: Configurar MongoDB Atlas

### 4.1 Criar Cluster MongoDB Atlas

1. **Acesse**: https://www.mongodb.com/atlas
2. **Crie conta gratuita**
3. **Crie cluster M0 (Free Tier)**
4. **Configure Network Access**:
   - Adicione IP da EC2: `seu-ip-ec2/32`
   - Ou temporariamente: `0.0.0.0/0` (menos seguro)
5. **Crie usuário do banco**
6. **Obtenha string de conexão**

### 4.2 Testar Conectividade

```bash
# Instalar MongoDB tools para teste
sudo apt install -y mongodb-clients

# Testar conexão (opcional)
mongosh "sua-string-de-conexao"
```

## 🔧 Passo 5: Configurar SSL/HTTPS (Opcional mas Recomendado)

### 5.1 Usando Let's Encrypt (Gratuito)

```bash
# Instalar Certbot
sudo apt install -y certbot

# Parar serviços temporariamente
sudo docker-compose down

# Gerar certificado (substitua seu-dominio.com)
sudo certbot certonly --standalone -d seu-dominio.com

# Copiar certificados
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem ssl/key.pem
sudo chown -R ubuntu:ubuntu ssl/
```

### 5.2 Configurar Nginx para HTTPS

Edite `nginx.conf` e descomente a seção HTTPS:

```bash
nano nginx.conf
```

## 🚀 Passo 6: Deploy da Aplicação

### 6.1 Construir e Executar

```bash
# Construir imagens
docker-compose build

# Executar em segundo plano
docker-compose up -d

# Verificar status
docker-compose ps
```

### 6.2 Verificar Logs

```bash
# Ver logs da aplicação
docker-compose logs web

# Ver logs do Nginx
docker-compose logs nginx

# Acompanhar logs em tempo real
docker-compose logs -f
```

## 🔍 Passo 7: Testes e Verificação

### 7.1 Testes Básicos

```bash
# Teste local
curl http://localhost/health

# Teste externo (substitua o IP)
curl http://seu-ip-publico/health
```

### 7.2 Acesso à Aplicação

1. **Abra o navegador**: `http://seu-ip-publico`
2. **Login padrão**:
   - Usuário: `admin`
   - Senha: `admin123`
3. **Altere a senha imediatamente**

## 🔒 Passo 8: Configurações de Segurança

### 8.1 Configurar Firewall UFW

```bash
# Instalar e configurar UFW
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

### 8.2 Configurar Fail2Ban

```bash
# Instalar Fail2Ban
sudo apt install -y fail2ban

# Configurar
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 8.3 Configurar Backup Automático

```bash
# Criar script de backup
nano backup.sh
```

```bash
#!/bin/bash
# Script de backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
APP_DIR="/home/ubuntu/analisador-pdfs"

mkdir -p $BACKUP_DIR

# Backup dos dados de usuários
cp $APP_DIR/users.json $BACKUP_DIR/users_$DATE.json

# Backup dos uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $APP_DIR uploads/

# Backup das configurações
cp $APP_DIR/.env $BACKUP_DIR/env_$DATE.backup

# Limpar backups antigos (manter 7 dias)
find $BACKUP_DIR -name "*.json" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

```bash
# Tornar executável
chmod +x backup.sh

# Adicionar ao cron (backup diário às 2h)
crontab -e
# Adicionar linha:
0 2 * * * /home/ubuntu/analisador-pdfs/backup.sh >> /var/log/backup.log 2>&1
```

## 📊 Passo 9: Monitoramento

### 9.1 Configurar Logs

```bash
# Criar diretório de logs
mkdir -p logs

# Configurar logrotate
sudo nano /etc/logrotate.d/analisador-pdfs
```

```
/home/ubuntu/analisador-pdfs/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 ubuntu ubuntu
}
```

### 9.2 Script de Monitoramento

```bash
# Criar script de monitoramento
nano monitor.sh
```

```bash
#!/bin/bash
# Script de monitoramento

# Verificar se containers estão rodando
if ! docker-compose ps | grep -q "Up"; then
    echo "ALERTA: Containers não estão rodando!"
    docker-compose up -d
fi

# Verificar espaço em disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERTA: Uso de disco alto: ${DISK_USAGE}%"
fi

# Verificar memória
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "ALERTA: Uso de memória alto: ${MEM_USAGE}%"
fi
```

```bash
# Tornar executável
chmod +x monitor.sh

# Executar a cada 5 minutos
crontab -e
# Adicionar linha:
*/5 * * * * /home/ubuntu/analisador-pdfs/monitor.sh >> /var/log/monitor.log 2>&1
```

## 🔄 Passo 10: Atualizações e Manutenção

### 10.1 Atualizar Aplicação

```bash
# Fazer backup antes
./backup.sh

# Parar aplicação
docker-compose down

# Atualizar código (se usando Git)
git pull origin main

# Reconstruir e executar
docker-compose build
docker-compose up -d

# Verificar status
docker-compose ps
```

### 10.2 Renovar Certificados SSL

```bash
# Renovar certificados Let's Encrypt
sudo certbot renew --dry-run

# Automatizar renovação
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet --post-hook "docker-compose restart nginx"
```

## 📈 Passo 11: Otimizações de Performance

### 11.1 Configurar Swap (para t2.micro)

```bash
# Criar arquivo swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 11.2 Otimizar Docker

```bash
# Limpar imagens não utilizadas
docker system prune -f

# Configurar limpeza automática
echo '0 3 * * 0 docker system prune -f' | crontab -
```

## 🆘 Troubleshooting

### Problemas Comuns

1. **Aplicação não responde**:
   ```bash
   docker-compose logs web
   docker-compose restart
   ```

2. **Erro de conexão MongoDB**:
   - Verificar string de conexão
   - Verificar Network Access no Atlas
   - Testar conectividade

3. **Erro 502 Bad Gateway**:
   ```bash
   docker-compose logs nginx
   docker-compose restart nginx
   ```

4. **Espaço em disco insuficiente**:
   ```bash
   df -h
   docker system prune -a
   sudo apt autoremove
   ```

## 💰 Custos Estimados (Free Tier)

- **EC2 t2.micro**: Gratuito por 12 meses (750h/mês)
- **MongoDB Atlas M0**: Gratuito permanentemente
- **Tráfego**: 15GB gratuitos/mês
- **EBS**: 30GB gratuitos/mês
- **Route 53**: $0.50/mês por hosted zone (opcional)

## 🔐 Checklist de Segurança

- [ ] Senha padrão alterada
- [ ] Firewall configurado
- [ ] Fail2Ban instalado
- [ ] HTTPS configurado
- [ ] Backup automático configurado
- [ ] Monitoramento ativo
- [ ] Logs configurados
- [ ] Variáveis de ambiente seguras
- [ ] Registro de usuários desabilitado
- [ ] MongoDB com autenticação

## 📞 Suporte

Para problemas específicos:

1. Verifique os logs: `docker-compose logs`
2. Consulte a documentação do AWS
3. Verifique status dos serviços: `docker-compose ps`

## 🎉 Conclusão

Sua aplicação agora está rodando em produção no AWS Free Tier com:

- ✅ Autenticação segura
- ✅ HTTPS (opcional)
- ✅ Proxy reverso Nginx
- ✅ Containerização Docker
- ✅ Backup automático
- ✅ Monitoramento
- ✅ Logs estruturados

**Acesse**: `https://seu-dominio.com` ou `http://seu-ip-publico`

**Login inicial**: admin / admin123 (altere imediatamente!)