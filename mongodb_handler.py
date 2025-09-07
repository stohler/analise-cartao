#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    pymongo = None

from datetime import datetime
import hashlib
from typing import List, Dict, Optional

class MongoDBHandler:
    def __init__(self, connection_string: str, database_name: str = "analise_cartao", collection_name: str = "transacoes"):
        """
        Inicializa o handler do MongoDB
        
        Args:
            connection_string: String de conexão do MongoDB
            database_name: Nome do banco de dados
            collection_name: Nome da coleção
        """
        if not PYMONGO_AVAILABLE:
            raise ImportError("PyMongo não está disponível. Instale com: pip install pymongo")
            
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self) -> bool:
        """
        Conecta ao MongoDB
        
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            self.client = pymongo.MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Testar a conexão
            self.client.admin.command('ping')
            print("✅ Conectado ao MongoDB com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar ao MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do MongoDB"""
        if self.client:
            self.client.close()
            print("🔌 Desconectado do MongoDB")
    
    def generate_transaction_hash(self, transaction: Dict) -> str:
        """
        Gera um hash único para a transação baseado em campos chave
        
        Args:
            transaction: Dicionário com os dados da transação
            
        Returns:
            str: Hash MD5 da transação
        """
        # Campos que identificam uma transação única
        key_fields = [
            transaction.get('data', ''),
            transaction.get('descricao', ''),
            transaction.get('valor', 0),
            transaction.get('banco', ''),
            transaction.get('origem_cartao', '')
        ]
        
        # Criar string única
        unique_string = '|'.join(str(field) for field in key_fields)
        
        # Gerar hash MD5
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, transaction: Dict) -> bool:
        """
        Verifica se a transação já existe no banco
        
        Args:
            transaction: Dicionário com os dados da transação
            
        Returns:
            bool: True se é duplicada, False caso contrário
        """
        if not self.collection:
            return False
            
        transaction_hash = self.generate_transaction_hash(transaction)
        
        # Buscar por transação com o mesmo hash
        existing = self.collection.find_one({"transaction_hash": transaction_hash})
        return existing is not None
    
    def add_card_origin(self, transactions: List[Dict], card_origin: str) -> List[Dict]:
        """
        Adiciona a origem do cartão às transações
        
        Args:
            transactions: Lista de transações
            card_origin: Origem do cartão (ex: "Cartão Principal", "Cartão Adicional")
            
        Returns:
            List[Dict]: Lista de transações com origem do cartão adicionada
        """
        for transaction in transactions:
            transaction['origem_cartao'] = card_origin
            transaction['data_importacao'] = datetime.now().isoformat()
            
        return transactions
    
    def save_transactions(self, transactions: List[Dict], card_origin: str, remove_duplicates: bool = True) -> Dict:
        """
        Salva as transações no MongoDB
        
        Args:
            transactions: Lista de transações para salvar
            card_origin: Origem do cartão
            remove_duplicates: Se deve remover duplicados
            
        Returns:
            Dict: Resultado da operação com estatísticas
        """
        if not self.collection:
            return {
                'success': False,
                'message': 'Não conectado ao MongoDB',
                'saved': 0,
                'duplicates': 0,
                'errors': 0
            }
        
        try:
            # Adicionar origem do cartão
            transactions_with_origin = self.add_card_origin(transactions.copy(), card_origin)
            
            saved_count = 0
            duplicate_count = 0
            error_count = 0
            
            for transaction in transactions_with_origin:
                try:
                    # Verificar duplicados se solicitado
                    if remove_duplicates and self.is_duplicate(transaction):
                        duplicate_count += 1
                        continue
                    
                    # Adicionar hash da transação
                    transaction['transaction_hash'] = self.generate_transaction_hash(transaction)
                    
                    # Inserir no MongoDB
                    result = self.collection.insert_one(transaction)
                    
                    if result.inserted_id:
                        saved_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"❌ Erro ao salvar transação: {e}")
                    error_count += 1
            
            return {
                'success': True,
                'message': f'Operação concluída: {saved_count} salvas, {duplicate_count} duplicadas, {error_count} erros',
                'saved': saved_count,
                'duplicates': duplicate_count,
                'errors': error_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro geral: {e}',
                'saved': 0,
                'duplicates': 0,
                'errors': len(transactions)
            }
    
    def get_transactions_count(self) -> int:
        """
        Retorna o número total de transações na coleção
        
        Returns:
            int: Número de transações
        """
        if not self.collection:
            return 0
        
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"❌ Erro ao contar transações: {e}")
            return 0
    
    def get_transactions_by_origin(self, card_origin: str) -> List[Dict]:
        """
        Retorna transações por origem do cartão
        
        Args:
            card_origin: Origem do cartão
            
        Returns:
            List[Dict]: Lista de transações
        """
        if not self.collection:
            return []
        
        try:
            cursor = self.collection.find({"origem_cartao": card_origin})
            return list(cursor)
        except Exception as e:
            print(f"❌ Erro ao buscar transações: {e}")
            return []
    
    def get_transactions_by_date_range(self, start_date: str, end_date: str, card_origin: str = None) -> List[Dict]:
        """
        Retorna transações por período
        
        Args:
            start_date: Data de início (formato DD/MM/YYYY)
            end_date: Data de fim (formato DD/MM/YYYY)
            card_origin: Origem do cartão (opcional)
            
        Returns:
            List[Dict]: Lista de transações no período
        """
        if not self.collection:
            return []
        
        try:
            query = {
                "data": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            if card_origin:
                query["origem_cartao"] = card_origin
            
            cursor = self.collection.find(query)
            return list(cursor)
        except Exception as e:
            print(f"❌ Erro ao buscar transações por período: {e}")
            return []
    
    def get_monthly_statistics(self, year: int, month: int, card_origin: str = None) -> Dict:
        """
        Retorna estatísticas mensais
        
        Args:
            year: Ano
            month: Mês (1-12)
            card_origin: Origem do cartão (opcional)
            
        Returns:
            Dict: Estatísticas do mês
        """
        if not self.collection:
            return {}
        
        try:
            # Construir query para o mês
            query = {
                "data": {
                    "$regex": f"^\\d{{2}}/{month:02d}/{year}$"
                }
            }
            
            if card_origin:
                query["origem_cartao"] = card_origin
            
            # Pipeline de agregação
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": None,
                    "total_transactions": {"$sum": 1},
                    "total_value": {"$sum": "$valor"},
                    "avg_value": {"$avg": "$valor"},
                    "installments": {
                        "$sum": {
                            "$cond": [{"$eq": ["$parcelado", "Sim"]}, 1, 0]
                        }
                    }
                }}
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                return {
                    'total_transactions': stats['total_transactions'],
                    'total_value': stats['total_value'],
                    'average_value': stats['avg_value'],
                    'installments': stats['installments']
                }
            else:
                return {
                    'total_transactions': 0,
                    'total_value': 0,
                    'average_value': 0,
                    'installments': 0
                }
                
        except Exception as e:
            print(f"❌ Erro ao calcular estatísticas mensais: {e}")
            return {}
    
    def get_all_transactions(self, limit: int = 100) -> List[Dict]:
        """
        Retorna todas as transações (limitado)
        
        Args:
            limit: Limite de transações a retornar
            
        Returns:
            List[Dict]: Lista de transações
        """
        if not self.collection:
            return []
        
        try:
            cursor = self.collection.find().limit(limit).sort("data_importacao", -1)
            return list(cursor)
        except Exception as e:
            print(f"❌ Erro ao buscar transações: {e}")
            return []
    
    def create_indexes(self):
        """
        Cria índices para melhorar a performance
        """
        if not self.collection:
            return
        
        try:
            # Índice para hash da transação (evitar duplicados)
            self.collection.create_index("transaction_hash", unique=True)
            
            # Índice para origem do cartão
            self.collection.create_index("origem_cartao")
            
            # Índice para data
            self.collection.create_index("data")
            
            # Índice para banco
            self.collection.create_index("banco")
            
            print("✅ Índices criados com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar índices: {e}")

# Exemplo de uso
if __name__ == "__main__":
    # String de conexão fornecida pelo usuário
    CONNECTION_STRING = "mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    # Criar handler
    mongo_handler = MongoDBHandler(CONNECTION_STRING)
    
    # Conectar
    if mongo_handler.connect():
        # Criar índices
        mongo_handler.create_indexes()
        
        # Exemplo de transações
        sample_transactions = [
            {
                'data': '29/06/2025',
                'descricao': 'Disal Ecommerce - Parcela 7/7',
                'valor': 51.82,
                'categoria': 'compras',
                'banco': 'nubank',
                'parcelado': 'Sim',
                'parcela_atual': 7,
                'parcela_total': 7
            }
        ]
        
        # Salvar transações
        result = mongo_handler.save_transactions(sample_transactions, "Cartão Principal")
        print(f"Resultado: {result}")
        
        # Desconectar
        mongo_handler.disconnect()
