#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelos de dados para o sistema de autenticação
"""

from datetime import datetime
from flask_login import UserMixin
import bcrypt
import hashlib
import os
import json

class User(UserMixin):
    """Modelo de usuário para autenticação"""
    
    def __init__(self, user_id, username, email, password_hash, is_active=True, created_at=None, last_login=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @staticmethod
    def hash_password(password):
        """Gera hash da senha"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def get_id(self):
        """Retorna o ID do usuário para Flask-Login"""
        return str(self.id)
    
    def to_dict(self):
        """Converte o usuário para dicionário"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'last_login': self.last_login.isoformat() if isinstance(self.last_login, datetime) else self.last_login
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria usuário a partir de dicionário"""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        last_login = data.get('last_login')
        if isinstance(last_login, str):
            last_login = datetime.fromisoformat(last_login)
        
        return cls(
            user_id=data['id'],
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            is_active=data.get('is_active', True),
            created_at=created_at,
            last_login=last_login
        )

class UserManager:
    """Gerenciador de usuários com armazenamento em arquivo JSON"""
    
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = {}
        self.load_users()
    
    def load_users(self):
        """Carrega usuários do arquivo"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    self.users = {
                        user_id: User.from_dict(data) 
                        for user_id, data in users_data.items()
                    }
            except Exception as e:
                print(f"Erro ao carregar usuários: {e}")
                self.users = {}
        else:
            self.users = {}
            self.create_default_user()
    
    def save_users(self):
        """Salva usuários no arquivo"""
        try:
            users_data = {
                user_id: user.to_dict() 
                for user_id, user in self.users.items()
            }
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar usuários: {e}")
    
    def create_default_user(self):
        """Cria usuário padrão admin"""
        default_password = "admin123"
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@localhost",
            password_hash=User.hash_password(default_password),
            is_active=True,
            created_at=datetime.now()
        )
        self.users["admin"] = admin_user
        self.save_users()
        print(f"✅ Usuário padrão criado: admin / {default_password}")
    
    def get_user(self, user_id):
        """Busca usuário por ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        """Busca usuário por nome de usuário"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email):
        """Busca usuário por email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, username, email, password):
        """Cria novo usuário"""
        # Verificar se usuário já existe
        if self.get_user_by_username(username):
            return {'success': False, 'message': 'Nome de usuário já existe'}
        
        if self.get_user_by_email(email):
            return {'success': False, 'message': 'Email já está em uso'}
        
        # Gerar ID único
        user_id = hashlib.md5(f"{username}{email}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Criar usuário
        new_user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=User.hash_password(password),
            is_active=True,
            created_at=datetime.now()
        )
        
        self.users[user_id] = new_user
        self.save_users()
        
        return {'success': True, 'message': 'Usuário criado com sucesso', 'user_id': user_id}
    
    def authenticate_user(self, username, password):
        """Autentica usuário"""
        user = self.get_user_by_username(username)
        if user and user.check_password(password) and user.is_active:
            # Atualizar último login
            user.last_login = datetime.now()
            self.save_users()
            return user
        return None
    
    def update_user_password(self, user_id, new_password):
        """Atualiza senha do usuário"""
        user = self.get_user(user_id)
        if user:
            user.password_hash = User.hash_password(new_password)
            self.save_users()
            return {'success': True, 'message': 'Senha atualizada com sucesso'}
        return {'success': False, 'message': 'Usuário não encontrado'}
    
    def deactivate_user(self, user_id):
        """Desativa usuário"""
        user = self.get_user(user_id)
        if user:
            user.is_active = False
            self.save_users()
            return {'success': True, 'message': 'Usuário desativado'}
        return {'success': False, 'message': 'Usuário não encontrado'}
    
    def get_all_users(self):
        """Retorna todos os usuários"""
        return list(self.users.values())