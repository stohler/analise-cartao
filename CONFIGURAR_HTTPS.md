# 🔒 Configuração HTTPS com Let's Encrypt

## 📋 Pré-requisitos

Para usar HTTPS com Let's Encrypt, você precisa:

1. **Domínio configurado** apontando para o IP da VM GCP
2. **Secret `DOMAIN`** configurado no GitHub

## ⚙️ Configuração

### 1. Configurar DNS

Apontar seu domínio para o IP da VM GCP:
```
A    seu-dominio.com    -> 35.196.129.74
A    www.seu-dominio.com -> 35.196.129.74
```

### 2. Configurar Secret no GitHub

1. Vá para **Settings** > **Secrets and variables** > **Actions**
2. Adicione um novo secret:
   - **Name**: `DOMAIN`
   - **Value**: `seu-dominio.com`

### 3. Deploy Automático

Após configurar o domínio e o secret, faça commit das alterações:

```bash
git add .
git commit -m "feat: implementar HTTPS com Let's Encrypt"
git push origin main
```

## 🔄 Como Funciona

1. **GitHub Actions** executa o deploy
2. **Certbot** tenta obter certificado Let's Encrypt para o domínio
3. Se bem-sucedido:
   - ✅ Certificado válido instalado
   - ✅ Nginx configurado para HTTPS
   - ✅ Redirecionamento HTTP → HTTPS
   - ✅ Renovação automática configurada
4. Se falhar:
   - ⚠️ Certificado auto-assinado como fallback
   - ⚠️ Aplicação funciona em HTTP

## 🌐 Acesso

Após o deploy bem-sucedido:

- **HTTPS**: `https://seu-dominio.com`
- **HTTP**: `http://seu-dominio.com` (redireciona para HTTPS)

## 🔧 Troubleshooting

### Certificado não é obtido

1. Verifique se o domínio aponta para o IP correto:
   ```bash
   nslookup seu-dominio.com
   ```

2. Verifique se a porta 80 está aberta no firewall GCP

3. Verifique logs do Certbot:
   ```bash
   sudo certbot logs
   ```

### Renovação automática

O certificado é renovado automaticamente via cron:
```bash
# Verificar cron job
sudo crontab -l

# Testar renovação manual
sudo certbot renew --dry-run
```

## 📊 Status

- ✅ Let's Encrypt configurado
- ✅ Nginx com HTTPS ativo
- ✅ Redirecionamento HTTP → HTTPS
- ✅ Renovação automática
- ✅ Configurações de sessão seguras
- ✅ CSRF token funcionando com HTTPS
