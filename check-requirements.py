#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar se todos os pré-requisitos estão configurados
para deploy automático no GCP
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

def print_status(message, status="info"):
    """Print com cores"""
    colors = {
        "info": "\033[94m[INFO]\033[0m",
        "success": "\033[92m[SUCCESS]\033[0m", 
        "warning": "\033[93m[WARNING]\033[0m",
        "error": "\033[91m[ERROR]\033[0m"
    }
    print(f"{colors.get(status, colors['info'])} {message}")

def check_file_exists(filepath, required=True):
    """Verificar se arquivo existe"""
    if Path(filepath).exists():
        print_status(f"✅ {filepath} encontrado", "success")
        return True
    else:
        status = "error" if required else "warning"
        print_status(f"❌ {filepath} não encontrado", status)
        return False

def check_github_secrets():
    """Verificar se secrets do GitHub estão documentados"""
    required_secrets = [
        "GCP_PROJECT_ID",
        "GCP_SERVICE_ACCOUNT_KEY", 
        "GCP_VM_NAME",
        "GCP_VM_ZONE",
        "GCP_VM_USER",
        "GCP_VM_IP",
        "SSH_PRIVATE_KEY",
        "SECRET_KEY",
        "MONGODB_URI"
    ]
    
    print_status("📋 Secrets necessários no GitHub:", "info")
    for secret in required_secrets:
        print_status(f"  - {secret}", "info")
    
    print_status("⚠️ Verifique se todos os secrets estão configurados em:", "warning")
    print_status("   stohler/analise-cartao → Settings → Secrets and Variables → Actions", "warning")
    
    return True

def check_ssh_key():
    """Verificar se chave SSH existe"""
    ssh_key_path = Path.home() / ".ssh" / "gcp-deploy"
    
    if ssh_key_path.exists():
        print_status(f"✅ Chave SSH encontrada: {ssh_key_path}", "success")
        return True
    else:
        print_status(f"❌ Chave SSH não encontrada: {ssh_key_path}", "error")
        print_status("Execute: ssh-keygen -t rsa -b 4096 -C 'github-actions@analise-cartao' -f ~/.ssh/gcp-deploy", "info")
        return False

def check_vm_connectivity():
    """Verificar conectividade com a VM"""
    vm_ip = "35.196.129.74"
    
    try:
        # Tentar ping básico
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "5", vm_ip],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print_status(f"✅ VM {vm_ip} está acessível (ping)", "success")
            return True
        else:
            print_status(f"❌ VM {vm_ip} não responde ao ping", "error")
            return False
            
    except subprocess.TimeoutExpired:
        print_status(f"❌ Timeout ao tentar acessar VM {vm_ip}", "error")
        return False
    except Exception as e:
        print_status(f"❌ Erro ao verificar VM: {e}", "error")
        return False

def check_docker_files():
    """Verificar arquivos Docker otimizados"""
    files = {
        "docker-compose-gcp.yml": True,
        "Dockerfile-gcp": True,
        "nginx-gcp.conf": True,
        ".github/workflows/deploy-gcp.yml": True
    }
    
    all_ok = True
    for file, required in files.items():
        if not check_file_exists(file, required):
            all_ok = False
    
    return all_ok

def check_app_files():
    """Verificar arquivos da aplicação"""
    files = {
        "app_secure.py": True,
        "models.py": True,
        "auth.py": True,
        "forms.py": True,
        "requirements.txt": True,
        ".env.example": True,
        "templates/auth/login.html": True,
        "templates/base.html": True
    }
    
    all_ok = True
    for file, required in files.items():
        if not check_file_exists(file, required):
            all_ok = False
    
    return all_ok

def check_python_syntax():
    """Verificar sintaxe dos arquivos Python"""
    python_files = [
        "app_secure.py",
        "models.py", 
        "auth.py",
        "forms.py"
    ]
    
    all_ok = True
    for file in python_files:
        if Path(file).exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", file],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print_status(f"✅ {file} - sintaxe OK", "success")
                else:
                    print_status(f"❌ {file} - erro de sintaxe:", "error")
                    print_status(f"   {result.stderr}", "error")
                    all_ok = False
                    
            except Exception as e:
                print_status(f"❌ Erro ao verificar {file}: {e}", "error")
                all_ok = False
    
    return all_ok

def check_gcp_cli():
    """Verificar se gcloud CLI está instalado (opcional)"""
    try:
        result = subprocess.run(
            ["gcloud", "version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_status("✅ gcloud CLI instalado", "success")
            return True
        else:
            print_status("⚠️ gcloud CLI não encontrado (opcional)", "warning")
            return False
            
    except FileNotFoundError:
        print_status("⚠️ gcloud CLI não instalado (opcional)", "warning")
        print_status("   Instale em: https://cloud.google.com/sdk/docs/install", "info")
        return False

def generate_secret_key():
    """Gerar chave secreta para exemplo"""
    try:
        import secrets
        key = secrets.token_hex(32)
        print_status("🔑 Chave secreta gerada para uso:", "info")
        print_status(f"   SECRET_KEY={key}", "info")
        return key
    except Exception as e:
        print_status(f"❌ Erro ao gerar chave: {e}", "error")
        return None

def main():
    """Função principal"""
    print("🔍 VERIFICAÇÃO DE PRÉ-REQUISITOS - DEPLOY GCP")
    print("=" * 60)
    
    checks = []
    
    # Verificações básicas
    print_status("📁 Verificando arquivos da aplicação...", "info")
    checks.append(("Arquivos da aplicação", check_app_files()))
    
    print_status("\n🐳 Verificando arquivos Docker...", "info") 
    checks.append(("Arquivos Docker", check_docker_files()))
    
    print_status("\n🐍 Verificando sintaxe Python...", "info")
    checks.append(("Sintaxe Python", check_python_syntax()))
    
    print_status("\n🔐 Verificando chave SSH...", "info")
    checks.append(("Chave SSH", check_ssh_key()))
    
    print_status("\n🌐 Verificando conectividade VM...", "info")
    checks.append(("Conectividade VM", check_vm_connectivity()))
    
    print_status("\n☁️ Verificando gcloud CLI...", "info")
    checks.append(("gcloud CLI", check_gcp_cli()))
    
    print_status("\n📋 Verificando secrets GitHub...", "info")
    checks.append(("GitHub Secrets", check_github_secrets()))
    
    # Gerar chave secreta
    print_status("\n🔑 Gerando chave secreta...", "info")
    generate_secret_key()
    
    # Resumo
    print("\n" + "=" * 60)
    print_status("📊 RESUMO DA VERIFICAÇÃO", "info")
    print("=" * 60)
    
    passed = 0
    total = len(checks)
    
    for check_name, result in checks:
        if result:
            print_status(f"✅ {check_name}", "success")
            passed += 1
        else:
            print_status(f"❌ {check_name}", "error")
    
    print(f"\n📈 Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print_status("🎉 Todos os pré-requisitos estão OK!", "success")
        print_status("✅ Sistema pronto para deploy automático", "success")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Configure os GitHub Secrets (se ainda não fez)")
        print("2. Faça push para branch 'main'")
        print("3. Acompanhe o deploy em: https://github.com/stohler/analise-cartao/actions")
        print("4. Acesse: http://35.196.129.74")
        print("5. Login: admin / admin123 (altere imediatamente!)")
        return True
    else:
        print_status(f"⚠️ {total - passed} verificações falharam", "warning")
        print_status("🔧 Corrija os problemas antes do deploy", "warning")
        print("\n📖 DOCUMENTAÇÃO:")
        print("- Setup inicial: SETUP_GCP.md")
        print("- Deploy completo: DEPLOY_GCP.md") 
        print("- README: README_SECURE.md")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)