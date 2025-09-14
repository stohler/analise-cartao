#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar a aplicação em modo produção
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

def check_requirements():
    """Verifica se os requisitos estão atendidos"""
    print("🔍 Verificando requisitos...")
    
    # Verificar Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        return False
    
    # Verificar Docker
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        print("✅ Docker encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker não encontrado. Instale o Docker primeiro.")
        return False
    
    # Verificar Docker Compose
    try:
        subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        print("✅ Docker Compose encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose não encontrado. Instale o Docker Compose primeiro.")
        return False
    
    return True

def check_environment():
    """Verifica configurações de ambiente"""
    print("🔧 Verificando configurações de ambiente...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado. Criando a partir do exemplo...")
        example_file = Path('.env.example')
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("📋 Arquivo .env criado. EDITE-O ANTES DE CONTINUAR!")
            print("🔑 Especialmente: SECRET_KEY, MONGODB_URI")
            return False
        else:
            print("❌ Arquivo .env.example não encontrado")
            return False
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar variáveis críticas
    critical_vars = ['SECRET_KEY', 'FLASK_ENV']
    missing_vars = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente obrigatórias não definidas: {', '.join(missing_vars)}")
        return False
    
    # Verificar se é chave padrão
    if os.getenv('SECRET_KEY') in ['your-secret-key-here-change-in-production', 'dev-key-change-in-production']:
        print("⚠️  AVISO: Você está usando uma SECRET_KEY padrão!")
        print("🔐 Gere uma chave segura com: python -c \"import secrets; print(secrets.token_hex(32))\"")
        return False
    
    print("✅ Configurações de ambiente OK")
    return True

def prepare_directories():
    """Prepara diretórios necessários"""
    print("📁 Preparando diretórios...")
    
    dirs = ['uploads', 'logs', 'ssl']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Diretório {dir_name} pronto")

def check_mongodb_connection():
    """Verifica conexão com MongoDB"""
    print("🗄️  Testando conexão com MongoDB...")
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("⚠️  MONGODB_URI não definido. Funcionalidades limitadas.")
        return True
    
    try:
        from pymongo import MongoClient
        from urllib.parse import urlparse
        
        # Testar conexão
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        print("✅ Conexão com MongoDB OK")
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao conectar com MongoDB: {e}")
        print("🔄 A aplicação funcionará com armazenamento local apenas")
        return True

def build_and_start():
    """Constrói e inicia os containers"""
    print("🐳 Construindo e iniciando containers...")
    
    try:
        # Build
        print("🔨 Construindo imagens...")
        subprocess.run(['docker-compose', 'build'], check=True)
        
        # Start
        print("🚀 Iniciando serviços...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        # Verificar status
        print("📊 Verificando status dos containers...")
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao iniciar containers: {e}")
        return False

def show_status():
    """Mostra status da aplicação"""
    print("\n" + "="*60)
    print("🎉 APLICAÇÃO INICIADA COM SUCESSO!")
    print("="*60)
    
    # Obter IP público (se possível)
    try:
        import requests
        public_ip = requests.get('http://checkip.amazonaws.com', timeout=5).text.strip()
        print(f"🌐 Acesso externo: http://{public_ip}")
    except:
        print("🌐 Acesso externo: http://SEU-IP-PUBLICO")
    
    print("🏠 Acesso local: http://localhost")
    print("👤 Login padrão: admin / admin123")
    print("🔑 ALTERE A SENHA PADRÃO IMEDIATAMENTE!")
    
    print("\n📋 Comandos úteis:")
    print("  docker-compose logs -f    # Ver logs em tempo real")
    print("  docker-compose ps         # Status dos containers")
    print("  docker-compose down       # Parar aplicação")
    print("  docker-compose restart    # Reiniciar aplicação")
    
    print("\n🔧 Arquivos importantes:")
    print("  .env                      # Configurações de ambiente")
    print("  users.json                # Banco de dados de usuários")
    print("  uploads/                  # Arquivos enviados")
    print("  logs/                     # Logs da aplicação")
    
    print("="*60)

def main():
    """Função principal"""
    print("🚀 INICIANDO ANALISADOR DE PDFs - PRODUÇÃO")
    print("="*60)
    
    # Verificar requisitos
    if not check_requirements():
        print("❌ Requisitos não atendidos. Abortando.")
        sys.exit(1)
    
    # Verificar ambiente
    if not check_environment():
        print("❌ Configuração de ambiente incompleta. Configure o arquivo .env primeiro.")
        sys.exit(1)
    
    # Preparar diretórios
    prepare_directories()
    
    # Verificar MongoDB
    check_mongodb_connection()
    
    # Construir e iniciar
    if not build_and_start():
        print("❌ Falha ao iniciar aplicação.")
        sys.exit(1)
    
    # Mostrar status
    show_status()

if __name__ == '__main__':
    main()