#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validador de Arquivos - Verifica se arquivos PDF existem e são válidos
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

class FileValidator:
    def __init__(self):
        self.supported_extensions = ['.pdf']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def validate_file_path(self, file_path: str) -> Dict:
        """
        Valida se um arquivo existe e é acessível
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com resultado da validação
        """
        try:
            # Converter para Path object
            path = Path(file_path)
            
            # Verificar se o arquivo existe
            if not path.exists():
                return {
                    'valid': False,
                    'error': f'Arquivo não encontrado: {file_path}',
                    'suggestions': self._get_suggestions(file_path)
                }
            
            # Verificar se é um arquivo (não diretório)
            if not path.is_file():
                return {
                    'valid': False,
                    'error': f'Caminho não é um arquivo: {file_path}',
                    'suggestions': []
                }
            
            # Verificar extensão
            if path.suffix.lower() not in self.supported_extensions:
                return {
                    'valid': False,
                    'error': f'Extensão não suportada: {path.suffix}. Suportadas: {", ".join(self.supported_extensions)}',
                    'suggestions': []
                }
            
            # Verificar tamanho do arquivo
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'Arquivo muito grande: {file_size / (1024*1024):.1f}MB. Máximo: {self.max_file_size / (1024*1024):.1f}MB',
                    'suggestions': []
                }
            
            # Verificar se o arquivo está vazio
            if file_size == 0:
                return {
                    'valid': False,
                    'error': 'Arquivo está vazio',
                    'suggestions': []
                }
            
            # Verificar permissões de leitura
            if not os.access(path, os.R_OK):
                return {
                    'valid': False,
                    'error': 'Sem permissão de leitura para o arquivo',
                    'suggestions': ['Verifique as permissões do arquivo']
                }
            
            return {
                'valid': True,
                'file_path': str(path.absolute()),
                'file_size': file_size,
                'file_name': path.name
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro ao validar arquivo: {str(e)}',
                'suggestions': []
            }
    
    def _get_suggestions(self, file_path: str) -> List[str]:
        """
        Gera sugestões para arquivo não encontrado
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de sugestões
        """
        suggestions = []
        path = Path(file_path)
        
        # Verificar se existe no diretório atual
        current_dir = Path.cwd()
        if (current_dir / path.name).exists():
            suggestions.append(f"Arquivo encontrado no diretório atual: {current_dir / path.name}")
        
        # Verificar se existe na pasta uploads
        uploads_dir = current_dir / 'uploads'
        if uploads_dir.exists() and (uploads_dir / path.name).exists():
            suggestions.append(f"Arquivo encontrado na pasta uploads: {uploads_dir / path.name}")
        
        # Verificar se existe na pasta pdfs
        pdfs_dir = current_dir / 'pdfs'
        if pdfs_dir.exists() and (pdfs_dir / path.name).exists():
            suggestions.append(f"Arquivo encontrado na pasta pdfs: {pdfs_dir / path.name}")
        
        # Buscar arquivos similares
        similar_files = self._find_similar_files(path.name)
        if similar_files:
            suggestions.append("Arquivos similares encontrados:")
            suggestions.extend([f"  - {f}" for f in similar_files[:5]])  # Máximo 5 sugestões
        
        # Sugestões gerais
        suggestions.extend([
            "Verifique se o caminho está correto",
            "Use caminho absoluto se necessário",
            "Verifique se o arquivo foi movido ou renomeado"
        ])
        
        return suggestions
    
    def _find_similar_files(self, filename: str) -> List[str]:
        """
        Busca arquivos com nomes similares
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Lista de arquivos similares
        """
        similar_files = []
        current_dir = Path.cwd()
        
        # Buscar em diretórios comuns
        search_dirs = [current_dir, current_dir / 'uploads', current_dir / 'pdfs']
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            try:
                for file_path in search_dir.rglob('*.pdf'):
                    if filename.lower() in file_path.name.lower() or file_path.name.lower() in filename.lower():
                        similar_files.append(str(file_path.relative_to(current_dir)))
            except Exception:
                continue
        
        return similar_files
    
    def list_available_pdfs(self, directory: str = None) -> List[Dict]:
        """
        Lista todos os PDFs disponíveis em um diretório
        
        Args:
            directory: Diretório para buscar (padrão: diretório atual)
            
        Returns:
            Lista de arquivos PDF encontrados
        """
        if directory is None:
            directory = Path.cwd()
        
        pdf_files = []
        search_path = Path(directory)
        
        if not search_path.exists():
            return pdf_files
        
        try:
            for file_path in search_path.rglob('*.pdf'):
                if file_path.is_file():
                    file_info = {
                        'name': file_path.name,
                        'path': str(file_path.absolute()),
                        'relative_path': str(file_path.relative_to(Path.cwd())),
                        'size': file_path.stat().st_size,
                        'size_mb': file_path.stat().st_size / (1024 * 1024)
                    }
                    pdf_files.append(file_info)
        except Exception as e:
            print(f"❌ Erro ao listar PDFs: {e}")
        
        return sorted(pdf_files, key=lambda x: x['name'])
    
    def interactive_file_selection(self) -> Optional[str]:
        """
        Interface interativa para seleção de arquivo
        
        Returns:
            Caminho do arquivo selecionado ou None
        """
        print("📁 Seleção de Arquivo PDF")
        print("=" * 40)
        
        # Listar PDFs disponíveis
        pdf_files = self.list_available_pdfs()
        
        if not pdf_files:
            print("❌ Nenhum arquivo PDF encontrado no diretório atual")
            return None
        
        print(f"\n📄 {len(pdf_files)} arquivos PDF encontrados:")
        print("-" * 60)
        
        for i, file_info in enumerate(pdf_files, 1):
            print(f"{i:2d}. {file_info['name']:<30} ({file_info['size_mb']:.1f}MB)")
        
        print(f"{len(pdf_files) + 1:2d}. Digitar caminho manualmente")
        print(f"{len(pdf_files) + 2:2d}. Cancelar")
        
        while True:
            try:
                choice = input(f"\nEscolha um arquivo (1-{len(pdf_files) + 2}): ").strip()
                
                if not choice.isdigit():
                    print("❌ Digite um número válido")
                    continue
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(pdf_files):
                    selected_file = pdf_files[choice_num - 1]
                    print(f"✅ Arquivo selecionado: {selected_file['name']}")
                    return selected_file['path']
                
                elif choice_num == len(pdf_files) + 1:
                    # Digitar caminho manualmente
                    manual_path = input("Digite o caminho do arquivo: ").strip()
                    if manual_path:
                        validation = self.validate_file_path(manual_path)
                        if validation['valid']:
                            return validation['file_path']
                        else:
                            print(f"❌ {validation['error']}")
                            if validation['suggestions']:
                                print("💡 Sugestões:")
                                for suggestion in validation['suggestions']:
                                    print(f"   - {suggestion}")
                    continue
                
                elif choice_num == len(pdf_files) + 2:
                    print("❌ Operação cancelada")
                    return None
                
                else:
                    print(f"❌ Opção inválida. Escolha entre 1 e {len(pdf_files) + 2}")
                    continue
                    
            except KeyboardInterrupt:
                print("\n❌ Operação cancelada")
                return None
            except Exception as e:
                print(f"❌ Erro: {e}")
                continue

def main():
    """Interface de linha de comando para validação de arquivos"""
    validator = FileValidator()
    
    print("🔍 Validador de Arquivos PDF")
    print("=" * 40)
    
    while True:
        print("\n📋 Menu:")
        print("1. Validar arquivo específico")
        print("2. Listar PDFs disponíveis")
        print("3. Seleção interativa de arquivo")
        print("4. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '1':
            file_path = input("Caminho do arquivo: ").strip()
            if not file_path:
                print("❌ Caminho necessário")
                continue
            
            validation = validator.validate_file_path(file_path)
            
            if validation['valid']:
                print(f"✅ Arquivo válido!")
                print(f"   Nome: {validation['file_name']}")
                print(f"   Tamanho: {validation['file_size'] / (1024*1024):.1f}MB")
                print(f"   Caminho: {validation['file_path']}")
            else:
                print(f"❌ {validation['error']}")
                if validation['suggestions']:
                    print("💡 Sugestões:")
                    for suggestion in validation['suggestions']:
                        print(f"   - {suggestion}")
        
        elif choice == '2':
            pdf_files = validator.list_available_pdfs()
            
            if not pdf_files:
                print("❌ Nenhum arquivo PDF encontrado")
                continue
            
            print(f"\n📄 {len(pdf_files)} arquivos PDF encontrados:")
            print("-" * 60)
            
            for file_info in pdf_files:
                print(f"📄 {file_info['name']:<30} ({file_info['size_mb']:.1f}MB)")
                print(f"   Caminho: {file_info['relative_path']}")
                print()
        
        elif choice == '3':
            selected_file = validator.interactive_file_selection()
            if selected_file:
                print(f"✅ Arquivo selecionado: {selected_file}")
        
        elif choice == '4':
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()
