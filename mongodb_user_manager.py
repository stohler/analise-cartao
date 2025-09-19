#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de usuários com MongoDB
"""

import os
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional
from flask_login import UserMixin

try:
    from pymongo import MongoClient
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    ObjectId = None

class MongoDBUser(UserMixin):
    """Modelo de usuário para MongoDB"""
    
    def __init__(self, user_id: str, username: str, email: str, password_hash: str, 
                 is_active: bool = True, is_admin: bool = False, 
                 created_at: datetime = None, last_login: datetime = None):
        self._id = user_id  # ObjectId do MongoDB
        self.id = username  # ID para Flask-Login (username)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._is_active = is_active
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
    
    @property
    def is_active(self):
        """Propriedade is_active para Flask-Login"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """Setter para is_active"""
        self._is_active = value

class MongoDBUserManager:
    """Gerenciador de usuários com MongoDB"""
    
    def __init__(self, connection_string: str, database_name: str = "analise_cartao", collection_name: str = "users"):
        """
        Inicializa o gerenciador de usuários
        
        Args:
            connection_string: String de conexão do MongoDB
            database_name: Nome do banco de dados
            collection_name: Nome da coleção de usuários
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
        if PYMONGO_AVAILABLE:
            try:
                self.client = MongoClient(connection_string)
                self.db = self.client[database_name]
                self.collection = self.db[collection_name]
                print("✅ Gerenciador de usuários MongoDB inicializado")
            except Exception as e:
                print(f"❌ Erro ao conectar MongoDB para usuários: {e}")
                self.client = None
                self.db = None
                self.collection = None
    
    def connect(self) -> bool:
        """Conecta ao MongoDB"""
        if not PYMONGO_AVAILABLE:
            return False
            
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Criar índices
            self.create_indexes()
            
            # Criar usuário admin padrão se não existir
            self.create_default_admin()
            
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar MongoDB para usuários: {e}")
            return False
    
    def create_indexes(self):
        """Cria índices para melhor performance"""
        if self.collection is None:
            return
            
        try:
            # Índice único para username
            self.collection.create_index("username", unique=True)
            # Índice único para email
            self.collection.create_index("email", unique=True)
            print("✅ Índices de usuários criados com sucesso")
        except Exception as e:
            print(f"❌ Erro ao criar índices de usuários: {e}")
    
    def create_default_admin(self):
        """Cria usuário admin padrão se não existir"""
        if self.collection is None:
            return
            
        try:
            # Verificar se já existe um admin
            admin_exists = self.collection.find_one({"username": "admin"})
            
            if not admin_exists:
                # Criar usuário admin padrão
                admin_user = {
                    "username": "admin",
                    "email": "admin@analise-cartao.com",
                    "password_hash": self.hash_password("admin123"),
                    "is_active": True,
                    "is_admin": True,
                    "created_at": datetime.now(),
                    "last_login": None
                }
                
                result = self.collection.insert_one(admin_user)
                print(f"✅ Usuário admin padrão criado com ID: {result.inserted_id}")
            else:
                print("✅ Usuário admin já existe")
                
        except Exception as e:
            print(f"❌ Erro ao criar usuário admin padrão: {e}")
    
    def hash_password(self, password: str) -> str:
        """Gera hash da senha"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica se a senha está correta"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return password_hash_check.hex() == hash_hex
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Dict:
        """Cria um novo usuário"""
        if self.collection is None:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Verificar se username já existe
            if self.collection.find_one({"username": username}):
                return {'success': False, 'message': 'Nome de usuário já existe'}
            
            # Verificar se email já existe
            if self.collection.find_one({"email": email}):
                return {'success': False, 'message': 'Email já existe'}
            
            # Criar usuário
            user_data = {
                "username": username,
                "email": email,
                "password_hash": self.hash_password(password),
                "is_active": True,
                "is_admin": is_admin,
                "created_at": datetime.now(),
                "last_login": None
            }
            
            result = self.collection.insert_one(user_data)
            
            return {
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user_id': str(result.inserted_id)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro ao criar usuário: {str(e)}'}
    
    def get_user_by_username(self, username: str) -> Optional[MongoDBUser]:
        """Busca usuário por nome de usuário"""
        if self.collection is None:
            return None
        
        try:
            user_data = self.collection.find_one({"username": username})
            if user_data:
                return self._dict_to_user(user_data)
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar usuário: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[MongoDBUser]:
        """Busca usuário por ID (username ou ObjectId)"""
        if self.collection is None:
            return None
        
        try:
            # Primeiro tenta buscar por username (para compatibilidade com Flask-Login)
            user_data = self.collection.find_one({"username": user_id})
            if user_data:
                return self._dict_to_user(user_data)
            
            # Se não encontrou por username, tenta por ObjectId
            try:
                user_data = self.collection.find_one({"_id": ObjectId(user_id)})
                if user_data:
                    return self._dict_to_user(user_data)
            except:
                pass
                
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar usuário por ID: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[MongoDBUser]:
        """Autentica usuário"""
        user = self.get_user_by_username(username)
        if user and self.verify_password(password, user.password_hash):
            # Atualizar último login
            self.update_last_login(user.id)
            return user
        return None
    
    def update_last_login(self, user_id: str):
        """Atualiza último login do usuário"""
        if self.collection is None:
            return
        
        try:
            # user_id pode ser username ou ObjectId
            if len(user_id) == 24:  # ObjectId tem 24 caracteres
                self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"last_login": datetime.now()}}
                )
            else:  # username
                self.collection.update_one(
                    {"username": user_id},
                    {"$set": {"last_login": datetime.now()}}
                )
        except Exception as e:
            print(f"❌ Erro ao atualizar último login: {e}")
    
    def update_password(self, user_id: str, new_password: str) -> Dict:
        """Atualiza senha do usuário"""
        if self.collection is None:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # user_id pode ser username ou ObjectId
            if len(user_id) == 24:  # ObjectId tem 24 caracteres
                result = self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"password_hash": self.hash_password(new_password)}}
                )
            else:  # username
                result = self.collection.update_one(
                    {"username": user_id},
                    {"$set": {"password_hash": self.hash_password(new_password)}}
                )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Senha atualizada com sucesso'}
            else:
                return {'success': False, 'message': 'Usuário não encontrado'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao atualizar senha: {str(e)}'}
    
    def update_user(self, user_id: str, **kwargs) -> Dict:
        """Atualiza dados do usuário"""
        if self.collection is None:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Remover campos que não devem ser atualizados
            allowed_fields = ['username', 'email', 'is_active', 'is_admin']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_data:
                return {'success': False, 'message': 'Nenhum campo válido para atualizar'}
            
            # user_id pode ser username ou ObjectId
            if len(user_id) == 24:  # ObjectId tem 24 caracteres
                result = self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_data}
                )
            else:  # username
                result = self.collection.update_one(
                    {"username": user_id},
                    {"$set": update_data}
                )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'Usuário atualizado com sucesso'}
            else:
                return {'success': False, 'message': 'Usuário não encontrado ou nenhuma alteração feita'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao atualizar usuário: {str(e)}'}
    
    def delete_user(self, user_id: str) -> Dict:
        """Remove usuário"""
        if self.collection is None:
            return {'success': False, 'message': 'MongoDB não conectado'}
        
        try:
            # Não permitir deletar o admin
            user = self.get_user_by_id(user_id)
            if user and user.username == 'admin':
                return {'success': False, 'message': 'Não é possível deletar o usuário admin'}
            
            # user_id pode ser username ou ObjectId
            if len(user_id) == 24:  # ObjectId tem 24 caracteres
                result = self.collection.delete_one({"_id": ObjectId(user_id)})
            else:  # username
                result = self.collection.delete_one({"username": user_id})
            
            if result.deleted_count > 0:
                return {'success': True, 'message': 'Usuário removido com sucesso'}
            else:
                return {'success': False, 'message': 'Usuário não encontrado'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao remover usuário: {str(e)}'}
    
    def get_all_users(self) -> List[MongoDBUser]:
        """Retorna todos os usuários"""
        if self.collection is None:
            return []
        
        try:
            users_data = list(self.collection.find({}))
            return [self._dict_to_user(user_data) for user_data in users_data]
        except Exception as e:
            print(f"❌ Erro ao buscar usuários: {e}")
            return []
    
    def _dict_to_user(self, user_data: dict) -> MongoDBUser:
        """Converte dicionário para objeto MongoDBUser"""
        return MongoDBUser(
            user_id=str(user_data['_id']),
            username=user_data['username'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            is_active=user_data.get('is_active', True),
            is_admin=user_data.get('is_admin', False),
            created_at=user_data.get('created_at'),
            last_login=user_data.get('last_login')
        )
    
    def get_users_count(self) -> int:
        """Retorna número total de usuários"""
        if self.collection is None:
            return 0
        
        try:
            return self.collection.count_documents({})
        except Exception as e:
            print(f"❌ Erro ao contar usuários: {e}")
            return 0

# Exemplo de uso
if __name__ == "__main__":
    # String de conexão
    CONNECTION_STRING = "mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    # Criar gerenciador
    user_manager = MongoDBUserManager(CONNECTION_STRING)
    
    # Conectar
    if user_manager.connect():
        print("✅ Conectado ao MongoDB")
        
        # Testar autenticação
        user = user_manager.authenticate_user("admin", "admin123")
        if user:
            print(f"✅ Usuário autenticado: {user.username}")
        else:
            print("❌ Falha na autenticação")
    else:
        print("❌ Falha na conexão")
