#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Blueprint de autenticação
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegisterForm, ChangePasswordForm, ForgotPasswordForm
from mongodb_user_manager import MongoDBUserManager
import secrets
import string
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Instância global do gerenciador de usuários MongoDB
mongo_uri = os.environ.get('MONGODB_URI', 
    "mongodb+srv://paulostohler_db_user:nO1Jn8huiAh7h3cY@cluster0.d1b6nys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
user_manager = MongoDBUserManager(mongo_uri)

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
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    users = user_manager.get_all_users()
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Cria novo usuário (apenas para admin)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        
        if not username or not email or not password:
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('auth.create_user'))
        
        result = user_manager.create_user(username, email, password, is_admin)
        
        if result['success']:
            flash(f'Usuário {username} criado com sucesso!', 'success')
        else:
            flash(f'Erro ao criar usuário: {result["message"]}', 'error')
        
        return redirect(url_for('auth.list_users'))
    
    return render_template('auth/create_user.html')

@auth_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edita usuário (apenas para admin)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    user = user_manager.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.list_users'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        is_active = request.form.get('is_active') == 'on'
        is_admin = request.form.get('is_admin') == 'on'
        
        if not username or not email:
            flash('Username e email são obrigatórios.', 'error')
            return redirect(url_for('auth.edit_user', user_id=user_id))
        
        result = user_manager.update_user(user_id, 
                                        username=username, 
                                        email=email, 
                                        is_active=is_active, 
                                        is_admin=is_admin)
        
        if result['success']:
            flash(f'Usuário {username} atualizado com sucesso!', 'success')
        else:
            flash(f'Erro ao atualizar usuário: {result["message"]}', 'error')
        
        return redirect(url_for('auth.list_users'))
    
    return render_template('auth/edit_user.html', user=user)

@auth_bp.route('/users/<user_id>/change-password', methods=['GET', 'POST'])
@login_required
def change_user_password(user_id):
    """Altera senha de usuário (apenas para admin)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    user = user_manager.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.list_users'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('auth.change_user_password', user_id=user_id))
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.change_user_password', user_id=user_id))
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return redirect(url_for('auth.change_user_password', user_id=user_id))
        
        result = user_manager.update_password(user_id, new_password)
        
        if result['success']:
            flash(f'Senha do usuário {user.username} alterada com sucesso!', 'success')
        else:
            flash(f'Erro ao alterar senha: {result["message"]}', 'error')
        
        return redirect(url_for('auth.list_users'))
    
    return render_template('auth/change_user_password.html', user=user)

@auth_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Remove usuário (apenas para admin)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    user = user_manager.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.list_users'))
    
    result = user_manager.delete_user(user_id)
    
    if result['success']:
        flash(f'Usuário {user.username} removido com sucesso!', 'success')
    else:
        flash(f'Erro ao remover usuário: {result["message"]}', 'error')
    
    return redirect(url_for('auth.list_users'))

def get_user_manager():
    """Retorna a instância do gerenciador de usuários"""
    return user_manager