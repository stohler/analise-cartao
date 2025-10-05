#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar o sistema de login
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_login():
    """Testa o sistema de login"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testando sistema de login...")
    
    try:
        # Testar acesso à página de login
        print("1. Testando acesso à página de login...")
        response = requests.get(f"{base_url}/auth/login", timeout=10)
        
        if response.status_code == 200:
            print("✅ Página de login acessível")
        else:
            print(f"❌ Erro ao acessar página de login: {response.status_code}")
            return False
        
        # Testar login com credenciais padrão
        print("2. Testando login com credenciais padrão...")
        
        # Primeiro, obter o CSRF token da página de login
        session = requests.Session()
        login_page = session.get(f"{base_url}/auth/login")
        csrf_token = None
        
        if 'csrf_token' in login_page.text:
            # Extrair CSRF token do HTML
            import re
            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"✅ CSRF token encontrado: {csrf_token[:20]}...")
            else:
                # Tentar outro padrão
                csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"✅ CSRF token encontrado (padrão alternativo): {csrf_token[:20]}...")
                else:
                    print("⚠️ CSRF token não encontrado no HTML")
                    print("HTML relevante:", login_page.text[login_page.text.find('csrf_token')-50:login_page.text.find('csrf_token')+100])
        else:
            print("⚠️ Página de login não contém CSRF token")
        
        # Tentar fazer login
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'remember_me': False
        }
        
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        login_response = session.post(
            f"{base_url}/auth/login",
            data=login_data,
            allow_redirects=False,
            timeout=10
        )
        
        print(f"Status do login: {login_response.status_code}")
        
        if login_response.status_code == 302:
            print("✅ Login realizado com sucesso (redirecionamento)")
            return True
        elif login_response.status_code == 200:
            if "Usuário ou senha incorretos" in login_response.text:
                print("❌ Credenciais incorretas")
            else:
                print("⚠️ Login retornou 200, mas sem redirecionamento")
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            print(f"Resposta: {login_response.text[:200]}...")
        
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão. Certifique-se de que o servidor está rodando em http://localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout na requisição")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste de login...")
    print("=" * 50)
    
    success = test_login()
    
    print("=" * 50)
    if success:
        print("✅ Teste de login concluído com sucesso!")
    else:
        print("❌ Teste de login falhou!")
        sys.exit(1)
