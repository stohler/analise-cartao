#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Formulários para autenticação e gerenciamento de usuários
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import UserManager

class LoginForm(FlaskForm):
    """Formulário de login"""
    username = StringField('Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório'),
        Length(min=3, max=50, message='Nome de usuário deve ter entre 3 e 50 caracteres')
    ], render_kw={'placeholder': 'Digite seu nome de usuário'})
    
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha'})
    
    remember_me = BooleanField('Lembrar de mim')

class RegisterForm(FlaskForm):
    """Formulário de registro"""
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório'),
        Length(min=3, max=50, message='Nome de usuário deve ter entre 3 e 50 caracteres')
    ], render_kw={'placeholder': 'Escolha um nome de usuário'})
    
    email = EmailField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ], render_kw={'placeholder': 'seu@email.com'})
    
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Crie uma senha segura'})
    
    password_confirm = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('password', message='Senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a senha novamente'})
    
    def __init__(self, user_manager=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_manager = user_manager or UserManager()
    
    def validate_username(self, username):
        """Valida se o nome de usuário já existe"""
        if self.user_manager.get_user_by_username(username.data):
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, email):
        """Valida se o email já existe"""
        if self.user_manager.get_user_by_email(email.data):
            raise ValidationError('Este email já está cadastrado.')

class ChangePasswordForm(FlaskForm):
    """Formulário para alteração de senha"""
    current_password = PasswordField('Senha Atual', validators=[
        DataRequired(message='Senha atual é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha atual'})
    
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite a nova senha'})
    
    new_password_confirm = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de nova senha é obrigatória'),
        EqualTo('new_password', message='Senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a nova senha novamente'})

class ForgotPasswordForm(FlaskForm):
    """Formulário para recuperação de senha"""
    email = EmailField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ], render_kw={'placeholder': 'Digite seu email cadastrado'})
    
    def __init__(self, user_manager=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_manager = user_manager or UserManager()
    
    def validate_email(self, email):
        """Valida se o email existe no sistema"""
        if not self.user_manager.get_user_by_email(email.data):
            raise ValidationError('Email não encontrado no sistema.')