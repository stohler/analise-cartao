# 🔐 Analisador de PDFs com Autenticação

Sistema completo para análise de faturas de cartão de crédito em PDF com autenticação segura, pronto para produção no AWS Free Tier.

## ✨ Funcionalidades

### 🔒 Autenticação e Segurança
- **Sistema de login** com usuário e senha
- **Gerenciamento de usuários** com perfis e permissões
- **Proteção CSRF** em todos os formulários
- **Headers de segurança** configurados
- **Rate limiting** para prevenir ataques
- **Sessões seguras** com cookies httpOnly
- **Middleware de segurança** personalizado

### 📊 Análise de PDFs
- **Suporte a múltiplos bancos**: Nubank, Itaú, Bradesco, Santander, BTG, Unicred, C6, Caixa
- **Categorização automática** com IA
- **Análise de transações** detalhada
- **Comparativos mensais** e relatórios
- **Exportação** em CSV, Excel e JSON

### 🗄️ Armazenamento
- **MongoDB Atlas** para produção (gratuito)
- **Armazenamento local** como fallback
- **Backup automático** configurado
- **Segregação por usuário** para privacidade

### 🚀 Deploy e Produção
- **Containerização** com Docker
- **Proxy reverso** Nginx
- **SSL/HTTPS** configurado
- **Monitoramento** e logs
- **Deploy AWS Free Tier** documentado

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Flask App      │────│  MongoDB Atlas  │
│   (Port 80/443) │    │  (Port 5000)    │    │  (Cloud)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Rate Limit    │    │  Authentication │    │  User Data      │
│   SSL/TLS       │    │  CSRF Protection│    │  Transactions   │
│   Static Files  │    │  Session Mgmt   │    │  Categories     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Início Rápido

### Desenvolvimento Local

1. **Clone o repositório**:
   ```bash
   git clone <repo-url>
   cd analisador-pdfs
   ```

2. **Instale dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure ambiente**:
   ```bash
   cp .env.example .env
   # Edite .env com suas configurações
   ```

4. **Execute a aplicação**:
   ```bash
   python app_secure.py
   ```

5. **Acesse**: http://localhost:5000
   - Usuário: `admin`
   - Senha: `admin123`

### Produção com Docker

1. **Execute o script de produção**:
   ```bash
   python start_production.py
   ```

2. **Ou manualmente**:
   ```bash
   docker-compose up -d
   ```

## 📋 Configuração

### Variáveis de Ambiente (.env)

```env
# Ambiente
FLASK_ENV=production

# Segurança (OBRIGATÓRIO ALTERAR!)
SECRET_KEY=sua-chave-secreta-super-forte-aqui

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Autenticação
REGISTRATION_ENABLED=false

# Servidor
PORT=5000
HOST=0.0.0.0

# Cookies (HTTPS em produção)
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

### Gerar Chave Secreta

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 👥 Sistema de Usuários

### Usuário Padrão
- **Usuário**: `admin`
- **Senha**: `admin123`
- **Permissões**: Administrador completo

### Funcionalidades de Usuário
- **Perfil pessoal** com informações
- **Alteração de senha** segura
- **Histórico de login** rastreado
- **Isolamento de dados** por usuário
- **Gerenciamento de usuários** (admin)

### Segurança
- **Senhas hasheadas** com bcrypt
- **Validação de força** da senha
- **Recuperação de senha** com token temporário
- **Bloqueio de tentativas** de login
- **Auditoria de acesso** nos logs

## 🗄️ Banco de Dados

### Estrutura de Usuários (users.json)
```json
{
  "admin": {
    "id": "admin",
    "username": "admin",
    "email": "admin@localhost",
    "password_hash": "...",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-01-01T12:00:00"
  }
}
```

### MongoDB Collections
- **transactions**: Transações dos usuários
- **categories**: Categorias personalizadas
- **categorization_patterns**: Padrões de IA
- **users_data**: Dados complementares

## 🔒 Segurança Implementada

### Autenticação
- ✅ Flask-Login para gerenciamento de sessão
- ✅ Proteção CSRF em todos os formulários
- ✅ Validação de entrada com WTForms
- ✅ Senhas hasheadas com bcrypt
- ✅ Sessões seguras com cookies httpOnly

### Headers de Segurança
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Strict-Transport-Security (HTTPS)
- ✅ Referrer-Policy: strict-origin-when-cross-origin

### Proteção de Dados
- ✅ Isolamento de dados por usuário
- ✅ Validação de permissões em todas as rotas
- ✅ Sanitização de uploads
- ✅ Rate limiting configurado
- ✅ Logs de auditoria

## 🚀 Deploy GCP Free Tier (Recomendado)

### Recursos Utilizados
- **VM e2-micro**: Servidor principal (always free)
- **MongoDB Atlas M0**: Banco de dados (gratuito permanente)
- **GitHub Actions**: Deploy automático (gratuito)
- **Let's Encrypt**: SSL gratuito

### Passo a Passo
1. **Siga o guia completo**: [DEPLOY_GCP.md](DEPLOY_GCP.md)
2. **Configure a VM**: [SETUP_GCP.md](SETUP_GCP.md)
3. **Configure GitHub Secrets**
4. **Push para branch `main`** = Deploy automático!

### Custos Estimados
- **Always Free**: $0 permanente (e2-micro)
- **MongoDB Atlas**: $0 permanente (M0)
- **GitHub Actions**: $0 (2000 min/mês grátis)
- **Total**: **$0/mês** 🎉

## 🚀 Deploy AWS Free Tier (Alternativo)

### Recursos Utilizados
- **EC2 t2.micro**: Servidor principal (gratuito 12 meses)
- **MongoDB Atlas M0**: Banco de dados (gratuito permanente)
- **Route 53**: DNS (opcional, $0.50/mês)
- **Let's Encrypt**: SSL gratuito

### Passo a Passo
1. **Siga o guia completo**: [DEPLOY_AWS.md](DEPLOY_AWS.md)
2. **Execute o script**: `python start_production.py`
3. **Configure SSL**: Let's Encrypt gratuito
4. **Configure domínio**: Route 53 ou CloudFlare

### Custos Estimados
- **Primeiro ano**: $0 (Free Tier)
- **Após primeiro ano**: ~$10/mês (EC2 + domínio)
- **MongoDB**: Sempre gratuito (M0)

## 📊 Monitoramento

### Logs Estruturados
- **Aplicação**: `/logs/app.log`
- **Acesso**: `/logs/access.log`
- **Erro**: `/logs/error.log`
- **Auditoria**: `/logs/audit.log`

### Métricas Monitoradas
- Status dos containers
- Uso de CPU e memória
- Espaço em disco
- Tempo de resposta
- Tentativas de login

### Health Checks
- **Endpoint**: `/health`
- **Docker**: Configurado no Dockerfile
- **Nginx**: Verificação automática

## 🔄 Backup e Recuperação

### Backup Automático
```bash
# Executa diariamente às 2h
./backup.sh
```

### Itens Incluídos no Backup
- `users.json` - Banco de usuários
- `uploads/` - Arquivos enviados
- `.env` - Configurações (sem senhas)
- `logs/` - Logs históricos

### Recuperação
```bash
# Restaurar usuários
cp backup/users_YYYYMMDD.json users.json

# Restaurar uploads
tar -xzf backup/uploads_YYYYMMDD.tar.gz
```

## 🛠️ Manutenção

### Comandos Úteis
```bash
# Status dos containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Reiniciar aplicação
docker-compose restart

# Atualizar aplicação
docker-compose down
git pull
docker-compose build
docker-compose up -d

# Limpar recursos não utilizados
docker system prune -f
```

### Atualizações
1. **Backup** dos dados
2. **Pull** do código atualizado
3. **Build** das novas imagens
4. **Deploy** com zero downtime
5. **Verificação** dos serviços

## 🆘 Troubleshooting

### Problemas Comuns

**1. Não consigo fazer login**
```bash
# Verificar logs
docker-compose logs web | grep -i error

# Resetar usuário admin
python -c "
from models import UserManager
um = UserManager()
um.users['admin'].password_hash = um.users['admin'].hash_password('admin123')
um.save_users()
print('Senha resetada para admin123')
"
```

**2. MongoDB não conecta**
```bash
# Testar conexão
python -c "
from pymongo import MongoClient
client = MongoClient('sua-string-de-conexao')
print(client.server_info())
"
```

**3. Erro 502 Bad Gateway**
```bash
# Verificar Nginx
docker-compose logs nginx

# Reiniciar proxy
docker-compose restart nginx
```

**4. Espaço em disco cheio**
```bash
# Verificar uso
df -h

# Limpar Docker
docker system prune -a

# Limpar logs antigos
find /var/log -name "*.log" -mtime +30 -delete
```

## 📚 Documentação Adicional

- [DEPLOY_AWS.md](DEPLOY_AWS.md) - Guia completo de deploy
- [CONTRIBUTING.md](CONTRIBUTING.md) - Como contribuir
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças
- [API.md](API.md) - Documentação da API

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: Use o GitHub Issues para reportar bugs
- **Discussões**: Use GitHub Discussions para dúvidas
- **Email**: contato@exemplo.com

## 🎯 Roadmap

### Próximas Versões
- [ ] Integração com APIs bancárias
- [ ] Dashboard avançado com gráficos
- [ ] Notificações por email
- [ ] API REST completa
- [ ] App mobile
- [ ] Machine Learning avançado
- [ ] Integração com planilhas Google

### Melhorias de Segurança
- [ ] Autenticação 2FA
- [ ] OAuth2 (Google, Facebook)
- [ ] Audit logs avançados
- [ ] Criptografia de dados sensíveis
- [ ] Compliance LGPD/GDPR

---

**Desenvolvido com ❤️ para análise segura de PDFs financeiros**