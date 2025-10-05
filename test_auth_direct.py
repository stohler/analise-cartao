#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar autenticação diretamente no MongoDB
"""

import os
from dotenv import load_dotenv
from mongodb_user_manager import MongoDBUserManager

# Carregar variáveis de ambiente
load_dotenv()

def test_auth_direct():
    """Testa autenticação diretamente no MongoDB"""
    print("🔍 Testando autenticação diretamente no MongoDB...")
    
    # String de conexão
    mongo_uri = os.environ.get('MONGODB_URI', 
        "mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
    # Criar gerenciador
    user_manager = MongoDBUserManager(mongo_uri)
    
    # Conectar
    if not user_manager.connect():
        print("❌ Falha na conexão com MongoDB")
        return False
    
    print("✅ Conectado ao MongoDB")
    
    # Verificar se usuário admin existe
    print("1. Verificando se usuário admin existe...")
    admin_user = user_manager.get_user_by_username("admin")
    
    if admin_user:
        print(f"✅ Usuário admin encontrado: {admin_user.username}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - Ativo: {admin_user.is_active}")
        print(f"   - Admin: {admin_user.is_admin}")
        print(f"   - Criado em: {admin_user.created_at}")
    else:
        print("❌ Usuário admin não encontrado")
        return False
    
    # Testar autenticação
    print("2. Testando autenticação com admin/admin123...")
    auth_user = user_manager.authenticate_user("admin", "admin123")
    
    if auth_user:
        print(f"✅ Autenticação bem-sucedida: {auth_user.username}")
        return True
    else:
        print("❌ Falha na autenticação")
        
        # Tentar criar usuário admin se não existir
        print("3. Tentando criar usuário admin...")
        result = user_manager.create_user(
            username="admin",
            email="admin@analise-cartao.com",
            password="admin123",
            is_admin=True
        )
        
        if result['success']:
            print("✅ Usuário admin criado com sucesso!")
            
            # Testar autenticação novamente
            auth_user = user_manager.authenticate_user("admin", "admin123")
            if auth_user:
                print("✅ Autenticação bem-sucedida após criação!")
                return True
            else:
                print("❌ Ainda falha na autenticação após criação")
        else:
            print(f"❌ Erro ao criar usuário admin: {result['message']}")
        
        return False

if __name__ == "__main__":
    print("🚀 Testando autenticação direta...")
    print("=" * 50)
    
    success = test_auth_direct()
    
    print("=" * 50)
    if success:
        print("✅ Teste de autenticação concluído com sucesso!")
    else:
        print("❌ Teste de autenticação falhou!")
