#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de Transações - Permite editar transações já salvas
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from data_handler import DataHandler
from mongodb_handler import MongoDBHandler

class TransactionManager:
    def __init__(self, use_mongodb: bool = False, connection_string: str = None):
        """
        Inicializa o gerenciador de transações
        
        Args:
            use_mongodb: Se deve usar MongoDB ao invés de arquivo local
            connection_string: String de conexão do MongoDB (se use_mongodb=True)
        """
        self.use_mongodb = use_mongodb
        
        if use_mongodb and connection_string:
            self.mongo_handler = MongoDBHandler(connection_string)
            self.data_handler = None
            if not self.mongo_handler.connect():
                print("❌ Erro ao conectar ao MongoDB, usando arquivo local")
                self.use_mongodb = False
                self.data_handler = DataHandler()
        else:
            self.data_handler = DataHandler()
            self.mongo_handler = None
    
    def get_handler(self):
        """Retorna o handler apropriado (MongoDB ou local)"""
        return self.mongo_handler if self.use_mongodb else self.data_handler
    
    def list_transactions(self, limit: int = 50, card_origin: str = None) -> List[Dict]:
        """
        Lista transações salvas
        
        Args:
            limit: Limite de transações a retornar
            card_origin: Filtrar por origem do cartão (opcional)
            
        Returns:
            Lista de transações
        """
        handler = self.get_handler()
        
        if self.use_mongodb:
            if card_origin:
                return handler.get_transactions_by_origin(card_origin)
            else:
                return handler.get_all_transactions(limit)
        else:
            if card_origin:
                return handler.get_transactions_by_origin(card_origin)
            else:
                return handler.get_all_transactions(limit)
    
    def search_transactions(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Busca transações por descrição
        
        Args:
            search_term: Termo de busca
            limit: Limite de resultados
            
        Returns:
            Lista de transações encontradas
        """
        handler = self.get_handler()
        all_transactions = handler.get_all_transactions(limit * 2)  # Buscar mais para filtrar
        
        search_lower = search_term.lower()
        filtered = []
        
        for transaction in all_transactions:
            if (search_lower in transaction.get('descricao', '').lower() or
                search_lower in transaction.get('categoria', '').lower() or
                search_lower in transaction.get('banco', '').lower()):
                filtered.append(transaction)
                
                if len(filtered) >= limit:
                    break
        
        return filtered
    
    def update_transaction_category(self, transaction_hash: str, new_category: str) -> Dict:
        """
        Atualiza a categoria de uma transação
        
        Args:
            transaction_hash: Hash da transação
            new_category: Nova categoria
            
        Returns:
            Resultado da operação
        """
        handler = self.get_handler()
        return handler.update_transaction_category(transaction_hash, new_category)
    
    def update_transaction(self, transaction_hash: str, updates: Dict) -> Dict:
        """
        Atualiza uma transação
        
        Args:
            transaction_hash: Hash da transação
            updates: Campos a serem atualizados
            
        Returns:
            Resultado da operação
        """
        handler = self.get_handler()
        return handler.update_transaction(transaction_hash, updates)
    
    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict]:
        """
        Busca uma transação pelo hash
        
        Args:
            transaction_hash: Hash da transação
            
        Returns:
            Transação encontrada ou None
        """
        handler = self.get_handler()
        return handler.get_transaction_by_hash(transaction_hash)
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas das transações
        
        Returns:
            Estatísticas
        """
        handler = self.get_handler()
        return handler.get_statistics()
    
    def export_transactions(self, filename: str = None) -> str:
        """
        Exporta transações para arquivo JSON
        
        Args:
            filename: Nome do arquivo (opcional)
            
        Returns:
            Caminho do arquivo exportado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transacoes_export_{timestamp}.json"
        
        handler = self.get_handler()
        transactions = handler.get_all_transactions(10000)  # Exportar todas
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'total_transactions': len(transactions),
            'transactions': transactions
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exportadas {len(transactions)} transações para {filename}")
        return filename

def main():
    """Interface de linha de comando para gerenciar transações"""
    print("🏦 Gerenciador de Transações")
    print("=" * 50)
    
    # Perguntar se quer usar MongoDB
    use_mongo = input("Usar MongoDB? (s/n): ").lower().strip() == 's'
    
    connection_string = None
    if use_mongo:
        connection_string = input("String de conexão MongoDB: ").strip()
        if not connection_string:
            print("❌ String de conexão necessária para MongoDB")
            return
    
    # Inicializar gerenciador
    manager = TransactionManager(use_mongodb=use_mongo, connection_string=connection_string)
    
    while True:
        print("\n📋 Menu Principal:")
        print("1. Listar transações")
        print("2. Buscar transações")
        print("3. Atualizar categoria de transação")
        print("4. Editar transação")
        print("5. Ver estatísticas")
        print("6. Exportar transações")
        print("7. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '1':
            # Listar transações
            limit = input("Limite de transações (padrão 50): ").strip()
            limit = int(limit) if limit.isdigit() else 50
            
            card_origin = input("Filtrar por origem do cartão (opcional): ").strip()
            card_origin = card_origin if card_origin else None
            
            transactions = manager.list_transactions(limit, card_origin)
            
            if not transactions:
                print("❌ Nenhuma transação encontrada")
                continue
            
            print(f"\n📊 {len(transactions)} transações encontradas:")
            print("-" * 80)
            
            for i, transaction in enumerate(transactions, 1):
                print(f"{i:2d}. {transaction.get('data', 'N/A')} | "
                      f"{transaction.get('descricao', 'N/A')[:40]:<40} | "
                      f"R$ {transaction.get('valor', 0):>8.2f} | "
                      f"{transaction.get('categoria', 'N/A'):<12} | "
                      f"Hash: {transaction.get('transaction_hash', 'N/A')[:8]}...")
        
        elif choice == '2':
            # Buscar transações
            search_term = input("Termo de busca: ").strip()
            if not search_term:
                print("❌ Termo de busca necessário")
                continue
            
            transactions = manager.search_transactions(search_term)
            
            if not transactions:
                print("❌ Nenhuma transação encontrada")
                continue
            
            print(f"\n🔍 {len(transactions)} transações encontradas para '{search_term}':")
            print("-" * 80)
            
            for i, transaction in enumerate(transactions, 1):
                print(f"{i:2d}. {transaction.get('data', 'N/A')} | "
                      f"{transaction.get('descricao', 'N/A')[:40]:<40} | "
                      f"R$ {transaction.get('valor', 0):>8.2f} | "
                      f"{transaction.get('categoria', 'N/A'):<12} | "
                      f"Hash: {transaction.get('transaction_hash', 'N/A')[:8]}...")
        
        elif choice == '3':
            # Atualizar categoria
            transaction_hash = input("Hash da transação: ").strip()
            if not transaction_hash:
                print("❌ Hash da transação necessário")
                continue
            
            # Buscar transação
            transaction = manager.get_transaction_by_hash(transaction_hash)
            if not transaction:
                print("❌ Transação não encontrada")
                continue
            
            print(f"\n📄 Transação encontrada:")
            print(f"Data: {transaction.get('data', 'N/A')}")
            print(f"Descrição: {transaction.get('descricao', 'N/A')}")
            print(f"Valor: R$ {transaction.get('valor', 0):.2f}")
            print(f"Categoria atual: {transaction.get('categoria', 'N/A')}")
            
            # Listar categorias disponíveis
            categories = ['alimentacao', 'transporte', 'saude', 'compras', 'servicos', 'outros']
            print(f"\nCategorias disponíveis: {', '.join(categories)}")
            
            new_category = input("Nova categoria: ").strip().lower()
            if new_category not in categories:
                print("❌ Categoria inválida")
                continue
            
            result = manager.update_transaction_category(transaction_hash, new_category)
            if result['success']:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
        
        elif choice == '4':
            # Editar transação
            transaction_hash = input("Hash da transação: ").strip()
            if not transaction_hash:
                print("❌ Hash da transação necessário")
                continue
            
            # Buscar transação
            transaction = manager.get_transaction_by_hash(transaction_hash)
            if not transaction:
                print("❌ Transação não encontrada")
                continue
            
            print(f"\n📄 Transação encontrada:")
            print(f"Data: {transaction.get('data', 'N/A')}")
            print(f"Descrição: {transaction.get('descricao', 'N/A')}")
            print(f"Valor: R$ {transaction.get('valor', 0):.2f}")
            print(f"Categoria: {transaction.get('categoria', 'N/A')}")
            print(f"Origem: {transaction.get('origem_cartao', 'N/A')}")
            
            updates = {}
            
            # Perguntar campos para atualizar
            new_desc = input("Nova descrição (Enter para manter): ").strip()
            if new_desc:
                updates['descricao'] = new_desc
            
            new_value = input("Novo valor (Enter para manter): ").strip()
            if new_value:
                try:
                    updates['valor'] = float(new_value)
                except ValueError:
                    print("❌ Valor inválido")
                    continue
            
            categories = ['alimentacao', 'transporte', 'saude', 'compras', 'servicos', 'outros']
            print(f"Categorias disponíveis: {', '.join(categories)}")
            new_category = input("Nova categoria (Enter para manter): ").strip().lower()
            if new_category:
                if new_category in categories:
                    updates['categoria'] = new_category
                else:
                    print("❌ Categoria inválida")
                    continue
            
            new_origin = input("Nova origem do cartão (Enter para manter): ").strip()
            if new_origin:
                updates['origem_cartao'] = new_origin
            
            if not updates:
                print("❌ Nenhuma alteração solicitada")
                continue
            
            result = manager.update_transaction(transaction_hash, updates)
            if result['success']:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
        
        elif choice == '5':
            # Ver estatísticas
            stats = manager.get_statistics()
            
            print(f"\n📊 Estatísticas:")
            print(f"Total de transações: {stats.get('total', 0)}")
            print(f"Valor total: R$ {stats.get('valor_total', 0):.2f}")
            print(f"Transações parceladas: {stats.get('parceladas', 0)}")
            
            print(f"\nPor banco:")
            for banco, count in stats.get('por_banco', {}).items():
                print(f"  {banco}: {count}")
            
            print(f"\nPor categoria:")
            for categoria, count in stats.get('por_categoria', {}).items():
                print(f"  {categoria}: {count}")
            
            print(f"\nPor origem:")
            for origem, count in stats.get('por_origem', {}).items():
                print(f"  {origem}: {count}")
        
        elif choice == '6':
            # Exportar transações
            filename = input("Nome do arquivo (Enter para automático): ").strip()
            filename = filename if filename else None
            
            try:
                exported_file = manager.export_transactions(filename)
                print(f"✅ Transações exportadas para: {exported_file}")
            except Exception as e:
                print(f"❌ Erro ao exportar: {e}")
        
        elif choice == '7':
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()
