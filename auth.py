#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Blueprint de autenticação
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm, ChangePasswordForm, ForgotPasswordForm
from models import UserManager
import secrets
import string

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Instância global do gerenciador de usuários
user_manager = UserManager()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = user_manager.authenticate_user(form.username.data, form.password.data)
        
        if user:
            login_user(user, remember=form.remember_me.data)
            flash(f'Bem-vindo, {user.username}!', 'success')
            
            # Redirecionar para a página solicitada ou página inicial
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Verificar se o registro está habilitado
    if not current_app.config.get('REGISTRATION_ENABLED', True):
        flash('Registro de novos usuários está desabilitado.', 'error')
        return redirect(url_for('auth.login'))
    
    form = RegisterForm(user_manager=user_manager)
    
    if form.validate_on_submit():
        result = user_manager.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        if result['success']:
            flash('Conta criada com sucesso! Você já pode fazer login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    username = current_user.username
    logout_user()
    flash(f'Até logo, {username}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Página de perfil do usuário"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Página para alteração de senha"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verificar senha atual
        if current_user.check_password(form.current_password.data):
            result = user_manager.update_user_password(
                current_user.id, 
                form.new_password.data
            )
            
            if result['success']:
                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash(result['message'], 'error')
        else:
            flash('Senha atual incorreta.', 'error')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Página para recuperação de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ForgotPasswordForm(user_manager=user_manager)
    
    if form.validate_on_submit():
        user = user_manager.get_user_by_email(form.email.data)
        if user:
            # Gerar nova senha temporária
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            
            result = user_manager.update_user_password(user.id, temp_password)
            
            if result['success']:
                # Em produção, você enviaria por email. Por enquanto, mostrar na tela.
                flash(f'Nova senha temporária gerada: {temp_password}. '
                      f'Faça login e altere sua senha imediatamente.', 'warning')
                return redirect(url_for('auth.login'))
            else:
                flash('Erro ao gerar nova senha.', 'error')
        else:
            # Por segurança, não revelar se o email existe ou não
            flash('Se o email estiver cadastrado, uma nova senha será enviada.', 'info')
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/users')
@login_required
def list_users():
    """Lista todos os usuários (apenas para admin)"""
    if current_user.username != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    users = user_manager.get_all_users()
    return render_template('auth/users.html', users=users)

def get_user_manager():
    """Retorna a instância do gerenciador de usuários"""
    return user_manager