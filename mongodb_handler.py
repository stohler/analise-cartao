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
    
    def convert_date_to_iso(self, date_str: str) -> datetime:
        """
        Converte data do formato DD/MM/YYYY para ISODate
        
        Args:
            date_str: Data no formato DD/MM/YYYY
            
        Returns:
            datetime: Objeto datetime para ISODate
        """
        if not date_str:
            return None
            
        try:
            day, month, year = date_str.split('/')
            return datetime(int(year), int(month), int(day))
        except:
            return None

    def add_card_origin(self, transactions: List[Dict], card_origin: str) -> List[Dict]:
        """
        Adiciona a origem do cartão às transações e converte datas para ISODate
        
        Args:
            transactions: Lista de transações
            card_origin: Origem do cartão (ex: "Cartão Principal", "Cartão Adicional")
            
        Returns:
            List[Dict]: Lista de transações com origem do cartão adicionada e datas convertidas
        """
        for transaction in transactions:
            transaction['origem_cartao'] = card_origin
            transaction['data_importacao'] = datetime.now()
            
            # Converter data para ISODate se estiver no formato DD/MM/YYYY
            if 'data' in transaction and transaction['data']:
                iso_date = self.convert_date_to_iso(transaction['data'])
                if iso_date:
                    transaction['data_iso'] = iso_date
                    # Manter a data original como string para compatibilidade
                    # transaction['data'] = transaction['data']  # Manter formato original
            
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

    def get_categories(self) -> List[Dict]:
        """
        Obtém todas as categorias disponíveis
        
        Returns:
            Lista de categorias
        """
        if not self.collection:
            return []
        
        try:
            categories_collection = self.db['categorias']
            categories = list(categories_collection.find({}, {'_id': 0}).sort('nome', 1))
            return categories
        except Exception as e:
            print(f"Erro ao obter categorias: {e}")
            return []

    def add_category(self, nome: str, descricao: str = "", cor: str = "#6c757d") -> Dict:
        """
        Adiciona uma nova categoria
        
        Args:
            nome: Nome da categoria
            descricao: Descrição da categoria
            cor: Cor da categoria (hex)
            
        Returns:
            Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            categories_collection = self.db['categorias']
            
            # Verificar se categoria já existe
            existing = categories_collection.find_one({'nome': nome.lower()})
            if existing:
                return {'success': False, 'message': 'Categoria já existe'}
            
            # Inserir nova categoria
            category_data = {
                'nome': nome.lower(),
                'nome_exibicao': nome,
                'descricao': descricao,
                'cor': cor,
                'ativo': True,
                'data_criacao': datetime.now()
            }
            
            result = categories_collection.insert_one(category_data)
            
            return {
                'success': True,
                'message': f'Categoria "{nome}" adicionada com sucesso!',
                'category_id': str(result.inserted_id)
            }
        except Exception as e:
            return {'success': False, 'message': f'Erro ao adicionar categoria: {str(e)}'}

    def update_category(self, category_id: str, nome: str = None, descricao: str = None, cor: str = None, ativo: bool = None) -> Dict:
        """
        Atualiza uma categoria existente
        
        Args:
            category_id: ID da categoria
            nome: Novo nome
            descricao: Nova descrição
            cor: Nova cor
            ativo: Status ativo/inativo
            
        Returns:
            Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            from bson import ObjectId
            categories_collection = self.db['categorias']
            
            # Construir dados de atualização
            update_data = {}
            if nome is not None:
                update_data['nome'] = nome.lower()
                update_data['nome_exibicao'] = nome
            if descricao is not None:
                update_data['descricao'] = descricao
            if cor is not None:
                update_data['cor'] = cor
            if ativo is not None:
                update_data['ativo'] = ativo
            
            update_data['data_atualizacao'] = datetime.now()
            
            result = categories_collection.update_one(
                {'_id': ObjectId(category_id)},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Categoria atualizada com sucesso!'}
            else:
                return {'success': False, 'message': 'Categoria não encontrada'}
        except Exception as e:
            return {'success': False, 'message': f'Erro ao atualizar categoria: {str(e)}'}

    def delete_category(self, category_id: str) -> Dict:
        """
        Remove uma categoria
        
        Args:
            category_id: ID da categoria
            
        Returns:
            Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            from bson import ObjectId
            categories_collection = self.db['categorias']
            
            # Verificar se há transações usando esta categoria
            transactions_count = self.collection.count_documents({'categoria': {'$regex': f'^{category_id}$', '$options': 'i'}})
            if transactions_count > 0:
                return {'success': False, 'message': f'Não é possível remover categoria com {transactions_count} transações associadas'}
            
            result = categories_collection.delete_one({'_id': ObjectId(category_id)})
            
            if result.deleted_count > 0:
                return {'success': True, 'message': 'Categoria removida com sucesso!'}
            else:
                return {'success': False, 'message': 'Categoria não encontrada'}
        except Exception as e:
            return {'success': False, 'message': f'Erro ao remover categoria: {str(e)}'}

    def update_transaction_category(self, transaction_hash: str, new_category: str) -> Dict:
        """
        Atualiza a categoria de uma transação específica
        
        Args:
            transaction_hash: Hash da transação a ser atualizada
            new_category: Nova categoria
            
        Returns:
            Dict: Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Buscar transação atual
            current_transaction = self.collection.find_one({"transaction_hash": transaction_hash})
            if not current_transaction:
                return {'success': False, 'message': 'Transação não encontrada'}
            
            old_category = current_transaction.get('categoria', 'outros')
            
            # Atualizar transação
            result = self.collection.update_one(
                {"transaction_hash": transaction_hash},
                {
                    "$set": {
                        "categoria": new_category,
                        "data_atualizacao": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': f'Categoria atualizada de "{old_category}" para "{new_category}"',
                    'old_category': old_category,
                    'new_category': new_category
                }
            else:
                return {'success': False, 'message': 'Nenhuma alteração realizada'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao atualizar categoria: {str(e)}'}
    
    def update_transaction(self, transaction_hash: str, updates: Dict) -> Dict:
        """
        Atualiza uma transação específica
        
        Args:
            transaction_hash: Hash da transação a ser atualizada
            updates: Dicionário com os campos a serem atualizados
            
        Returns:
            Dict: Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Buscar transação atual
            current_transaction = self.collection.find_one({"transaction_hash": transaction_hash})
            if not current_transaction:
                return {'success': False, 'message': 'Transação não encontrada'}
            
            # Atualizar campos permitidos
            allowed_fields = ['categoria', 'descricao', 'valor', 'origem_cartao']
            update_data = {}
            updated_fields = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    old_value = current_transaction.get(field)
                    update_data[field] = value
                    updated_fields.append(f"{field}: '{old_value}' → '{value}'")
            
            if not update_data:
                return {'success': False, 'message': 'Nenhum campo válido para atualização'}
            
            # Adicionar data de atualização
            update_data['data_atualizacao'] = datetime.now()
            
            # Recalcular hash se campos chave foram alterados
            if any(field in ['data', 'descricao', 'valor', 'banco', 'origem_cartao'] for field in updates.keys()):
                # Criar nova transação com campos atualizados
                new_transaction = current_transaction.copy()
                new_transaction.update(update_data)
                new_hash = self.generate_transaction_hash(new_transaction)
                update_data['transaction_hash'] = new_hash
            
            # Atualizar no MongoDB
            result = self.collection.update_one(
                {"transaction_hash": transaction_hash},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': f'Transação atualizada: {", ".join(updated_fields)}',
                    'updated_fields': updated_fields
                }
            else:
                return {'success': False, 'message': 'Nenhuma alteração realizada'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao atualizar transação: {str(e)}'}
    
    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict]:
        """
        Busca uma transação pelo hash
        
        Args:
            transaction_hash: Hash da transação
            
        Returns:
            Dict ou None: Transação encontrada ou None
        """
        if not self.collection:
            return None
        
        try:
            return self.collection.find_one({"transaction_hash": transaction_hash})
        except Exception as e:
            print(f"❌ Erro ao buscar transação: {e}")
            return None

    def remove_transaction(self, transaction_hash: str) -> Dict:
        """
        Remove uma transação específica pelo hash
        
        Args:
            transaction_hash: Hash da transação a ser removida
            
        Returns:
            Dict: Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Buscar transação para obter informações antes de remover
            transaction = self.collection.find_one({"transaction_hash": transaction_hash})
            if not transaction:
                return {'success': False, 'message': 'Transação não encontrada'}
            
            # Remover transação
            result = self.collection.delete_one({"transaction_hash": transaction_hash})
            
            if result.deleted_count > 0:
                return {
                    'success': True,
                    'message': f'Transação removida com sucesso: {transaction.get("descricao", "N/A")}',
                    'removed_transaction': transaction
                }
            else:
                return {'success': False, 'message': 'Erro ao remover transação'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao remover transação: {str(e)}'}
    
    def remove_all_transactions(self) -> Dict:
        """
        Remove todas as transações
        
        Returns:
            Dict: Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Contar transações antes de remover
            total_count = self.collection.count_documents({})
            
            if total_count == 0:
                return {
                    'success': True,
                    'message': 'Nenhuma transação para remover',
                    'removed_count': 0
                }
            
            # Remover todas as transações
            result = self.collection.delete_many({})
            
            if result.deleted_count > 0:
                return {
                    'success': True,
                    'message': f'Todas as {result.deleted_count} transações foram removidas com sucesso',
                    'removed_count': result.deleted_count
                }
            else:
                return {'success': False, 'message': 'Erro ao remover transações'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao remover todas as transações: {str(e)}'}
    
    def convert_date_format(self, date_str: str, from_format: str = 'YYYY-MM-DD', to_format: str = 'DD/MM/YYYY') -> str:
        """
        Converte formato de data entre YYYY-MM-DD e DD/MM/YYYY
        
        Args:
            date_str: String da data
            from_format: Formato de origem ('YYYY-MM-DD' ou 'DD/MM/YYYY')
            to_format: Formato de destino ('YYYY-MM-DD' ou 'DD/MM/YYYY')
            
        Returns:
            str: Data no formato de destino
        """
        if not date_str:
            return date_str
            
        try:
            if from_format == 'YYYY-MM-DD' and to_format == 'DD/MM/YYYY':
                # Converter de YYYY-MM-DD para DD/MM/YYYY
                year, month, day = date_str.split('-')
                return f"{day}/{month}/{year}"
            elif from_format == 'DD/MM/YYYY' and to_format == 'YYYY-MM-DD':
                # Converter de DD/MM/YYYY para YYYY-MM-DD
                day, month, year = date_str.split('/')
                return f"{year}-{month}-{day}"
            else:
                return date_str
        except:
            return date_str
    
    def parse_date_to_comparable(self, date_str: str) -> str:
        """
        Converte data no formato DD/MM/YYYY para formato comparável YYYYMMDD
        
        Args:
            date_str: Data no formato DD/MM/YYYY
            
        Returns:
            str: Data no formato YYYYMMDD para comparação
        """
        if not date_str:
            return date_str
            
        try:
            day, month, year = date_str.split('/')
            return f"{year}{month.zfill(2)}{day.zfill(2)}"
        except:
            return date_str

    def get_transactions_paginated(self, page: int = 1, per_page: int = 20, keyword: str = None, 
                                 start_date: str = None, end_date: str = None, card_origin: str = None, 
                                 banco: str = None) -> Dict:
        """
        Retorna transações paginadas com filtros opcionais
        
        Args:
            page: Número da página (começando em 1)
            per_page: Número de transações por página
            keyword: Palavra-chave para buscar na descrição
            start_date: Data de início (formato YYYY-MM-DD ou DD/MM/YYYY)
            end_date: Data de fim (formato YYYY-MM-DD ou DD/MM/YYYY)
            card_origin: Origem do cartão
            banco: Nome do banco
            
        Returns:
            Dict: Resultado com transações e metadados de paginação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Construir query de filtro
            query = {}
            
            # Filtro por palavra-chave
            if keyword:
                query['descricao'] = {'$regex': keyword, '$options': 'i'}
            
            # Filtro por data - usar campo data_iso quando disponível
            if start_date and end_date:
                # Converter datas para datetime
                start_datetime = datetime.fromisoformat(start_date)
                end_datetime = datetime.fromisoformat(end_date)
                query['data_iso'] = {'$gte': start_datetime, '$lte': end_datetime}
            elif start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query['data_iso'] = {'$gte': start_datetime}
            elif end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query['data_iso'] = {'$lte': end_datetime}
            
            # Filtro por origem do cartão
            if card_origin:
                query['origem_cartao'] = card_origin
            
            # Filtro por banco
            if banco:
                query['banco'] = banco
            
            # Calcular skip para paginação
            skip = (page - 1) * per_page
            
            # Buscar transações
            cursor = self.collection.find(query).sort("data_importacao", -1).skip(skip).limit(per_page)
            transactions = []
            for doc in cursor:
                # Converter ObjectId para string para serialização JSON
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                # Converter data_iso para string se existir
                if 'data_iso' in doc and doc['data_iso']:
                    doc['data_iso'] = doc['data_iso'].isoformat()
                transactions.append(doc)
            
            # Contar total de transações que atendem aos filtros
            total_count = self.collection.count_documents(query)
            
            # Calcular metadados de paginação
            total_pages = (total_count + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
            
            return {
                'success': True,
                'transactions': transactions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_prev': has_prev,
                    'has_next': has_next,
                    'prev_page': page - 1 if has_prev else None,
                    'next_page': page + 1 if has_next else None
                },
                'filters': {
                    'keyword': keyword,
                    'start_date': start_date,
                    'end_date': end_date,
                    'card_origin': card_origin,
                    'banco': banco
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro ao buscar transações: {str(e)}'}

    def initialize_default_categories(self) -> Dict:
        """
        Inicializa categorias padrão se não existirem
        
        Returns:
            Resultado da operação
        """
        if not self.collection:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            categories_collection = self.db['categorias']
            
            # Verificar se já existem categorias
            if categories_collection.count_documents({}) > 0:
                return {'success': True, 'message': 'Categorias já inicializadas'}
            
            # Categorias padrão
            default_categories = [
                {'nome': 'alimentacao', 'nome_exibicao': 'Alimentação', 'descricao': 'Gastos com comida e bebida', 'cor': '#28a745', 'ativo': True},
                {'nome': 'transporte', 'nome_exibicao': 'Transporte', 'descricao': 'Gastos com transporte', 'cor': '#007bff', 'ativo': True},
                {'nome': 'saude', 'nome_exibicao': 'Saúde', 'descricao': 'Gastos com saúde e medicamentos', 'cor': '#dc3545', 'ativo': True},
                {'nome': 'educacao', 'nome_exibicao': 'Educação', 'descricao': 'Gastos com educação', 'cor': '#6f42c1', 'ativo': True},
                {'nome': 'lazer', 'nome_exibicao': 'Lazer', 'descricao': 'Gastos com entretenimento', 'cor': '#fd7e14', 'ativo': True},
                {'nome': 'compras', 'nome_exibicao': 'Compras', 'descricao': 'Compras diversas', 'cor': '#20c997', 'ativo': True},
                {'nome': 'servicos', 'nome_exibicao': 'Serviços', 'descricao': 'Serviços diversos', 'cor': '#6c757d', 'ativo': True},
                {'nome': 'outros', 'nome_exibicao': 'Outros', 'descricao': 'Outros gastos', 'cor': '#6c757d', 'ativo': True}
            ]
            
            # Adicionar data de criação
            for category in default_categories:
                category['data_criacao'] = datetime.now()
            
            result = categories_collection.insert_many(default_categories)
            
            return {
                'success': True,
                'message': f'{len(result.inserted_ids)} categorias padrão criadas com sucesso!',
                'inserted_count': len(result.inserted_ids)
            }
        except Exception as e:
            return {'success': False, 'message': f'Erro ao inicializar categorias: {str(e)}'}

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
