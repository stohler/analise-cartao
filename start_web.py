#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para iniciar a interface web do Analisador de PDFs
"""

import os
import sys
from web_analyzer import app

def main():
    """Inicia o servidor web"""
    print("🌐 INICIANDO INTERFACE WEB - ANALISADOR DE PDFs")
    print("="*60)
    print("📊 Sistema completo com MongoDB integrado")
    print("🔗 Interface disponível em: http://localhost:5000")
    print("📁 Upload de PDFs com análise automática")
    print("💾 Botão para gravar automaticamente no MongoDB")
    print("📈 Comparativo de 6 meses integrado")
    print("="*60)
    
    # Verificar se a pasta templates existe
    if not os.path.exists('templates'):
        print("❌ Pasta 'templates' não encontrada!")
        print("   Certifique-se de que todos os arquivos estão no lugar correto.")
        sys.exit(1)
    
    # Verificar se a pasta uploads existe
    if not os.path.exists('uploads'):
        os.makedirs('uploads', exist_ok=True)
        print("✅ Pasta 'uploads' criada")
    
    print("\n🚀 Iniciando servidor...")
    print("   Pressione Ctrl+C para parar o servidor")
    print("-"*60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    main()
