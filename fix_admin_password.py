#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir a senha do usuário admin
"""

import os
from dotenv import load_dotenv
from mongodb_user_manager import MongoDBUserManager

# Carregar variáveis de ambiente
load_dotenv()

def fix_admin_password():
    """Corrige a senha do usuário admin"""
    print("🔧 Corrigindo senha do usuário admin...")
    
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
    
    # Atualizar senha do admin
    print("1. Atualizando senha do usuário admin...")
    result = user_manager.update_password("admin", "admin123")
    
    if result['success']:
        print("✅ Senha do usuário admin atualizada com sucesso!")
        
        # Testar autenticação
        print("2. Testando autenticação com nova senha...")
        auth_user = user_manager.authenticate_user("admin", "admin123")
        
        if auth_user:
            print("✅ Autenticação bem-sucedida com nova senha!")
            return True
        else:
            print("❌ Ainda falha na autenticação")
            return False
    else:
        print(f"❌ Erro ao atualizar senha: {result['message']}")
        return False

if __name__ == "__main__":
    print("🚀 Corrigindo senha do admin...")
    print("=" * 50)
    
    success = fix_admin_password()
    
    print("=" * 50)
    if success:
        print("✅ Senha do admin corrigida com sucesso!")
    else:
        print("❌ Falha ao corrigir senha do admin!")
