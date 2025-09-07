#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
import hashlib
from typing import List, Dict, Optional

class DataHandler:
    def __init__(self, data_file: str = "transacoes.json"):
        """
        Inicializa o handler de dados
        
        Args:
            data_file: Arquivo JSON para armazenar as transações
        """
        self.data_file = data_file
        self.transactions = []
        self.load_data()
    
    def load_data(self):
        """Carrega dados do arquivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.transactions = json.load(f)
                print(f"✅ Carregadas {len(self.transactions)} transações do arquivo")
            else:
                self.transactions = []
                print("📁 Arquivo de dados não encontrado, iniciando com lista vazia")
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            self.transactions = []
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.transactions, f, indent=2, ensure_ascii=False)
            print(f"✅ Dados salvos no arquivo {self.data_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {e}")
            return False
    
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
        transaction_hash = self.generate_transaction_hash(transaction)
        
        # Buscar por transação com o mesmo hash
        for existing in self.transactions:
            if existing.get('transaction_hash') == transaction_hash:
                return True
        
        return False
    
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
        Salva as transações no arquivo JSON
        
        Args:
            transactions: Lista de transações para salvar
            card_origin: Origem do cartão
            remove_duplicates: Se deve remover duplicados
            
        Returns:
            Dict: Resultado da operação com estatísticas
        """
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
                    
                    # Adicionar à lista
                    self.transactions.append(transaction)
                    saved_count += 1
                        
                except Exception as e:
                    print(f"❌ Erro ao processar transação: {e}")
                    error_count += 1
            
            # Salvar no arquivo
            if self.save_data():
                return {
                    'success': True,
                    'message': f'Operação concluída: {saved_count} salvas, {duplicate_count} duplicadas, {error_count} erros',
                    'saved': saved_count,
                    'duplicates': duplicate_count,
                    'errors': error_count
                }
            else:
                return {
                    'success': False,
                    'message': 'Erro ao salvar no arquivo',
                    'saved': 0,
                    'duplicates': 0,
                    'errors': len(transactions)
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
        Retorna o número total de transações
        
        Returns:
            int: Número de transações
        """
        return len(self.transactions)
    
    def get_transactions_by_origin(self, card_origin: str) -> List[Dict]:
        """
        Retorna transações por origem do cartão
        
        Args:
            card_origin: Origem do cartão
            
        Returns:
            List[Dict]: Lista de transações
        """
        return [t for t in self.transactions if t.get('origem_cartao') == card_origin]
    
    def get_all_transactions(self, limit: int = 100) -> List[Dict]:
        """
        Retorna todas as transações (limitado)
        
        Args:
            limit: Limite de transações a retornar
            
        Returns:
            List[Dict]: Lista de transações
        """
        # Ordenar por data de importação (mais recentes primeiro)
        sorted_transactions = sorted(
            self.transactions, 
            key=lambda x: x.get('data_importacao', ''), 
            reverse=True
        )
        return sorted_transactions[:limit]
    
    def export_to_mongodb_format(self) -> List[Dict]:
        """
        Exporta transações no formato para MongoDB
        
        Returns:
            List[Dict]: Lista de transações formatadas para MongoDB
        """
        return self.transactions.copy()
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas das transações
        
        Returns:
            Dict: Estatísticas das transações
        """
        if not self.transactions:
            return {
                'total': 0,
                'por_banco': {},
                'por_categoria': {},
                'por_origem': {},
                'valor_total': 0,
                'parceladas': 0
            }
        
        stats = {
            'total': len(self.transactions),
            'por_banco': {},
            'por_categoria': {},
            'por_origem': {},
            'valor_total': 0,
            'parceladas': 0
        }
        
        for transaction in self.transactions:
            # Por banco
            banco = transaction.get('banco', 'desconhecido')
            stats['por_banco'][banco] = stats['por_banco'].get(banco, 0) + 1
            
            # Por categoria
            categoria = transaction.get('categoria', 'outros')
            stats['por_categoria'][categoria] = stats['por_categoria'].get(categoria, 0) + 1
            
            # Por origem
            origem = transaction.get('origem_cartao', 'desconhecida')
            stats['por_origem'][origem] = stats['por_origem'].get(origem, 0) + 1
            
            # Valor total
            stats['valor_total'] += transaction.get('valor', 0)
            
            # Parceladas
            if transaction.get('parcelado') == 'Sim':
                stats['parceladas'] += 1
        
        return stats

# Exemplo de uso
if __name__ == "__main__":
    # Criar handler
    data_handler = DataHandler()
    
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
    result = data_handler.save_transactions(sample_transactions, "Cartão Principal")
    print(f"Resultado: {result}")
    
    # Mostrar estatísticas
    stats = data_handler.get_statistics()
    print(f"Estatísticas: {stats}")
