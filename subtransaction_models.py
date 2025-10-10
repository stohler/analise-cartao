#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modelos de dados para subtransações (itens de compras)
"""

from datetime import datetime
from typing import List, Dict, Optional
import json
import hashlib

class SubTransaction:
    """Modelo para uma subtransação (item de compra)"""
    
    def __init__(self, item_id: str, description: str, quantity: float, unit_value: float, 
                 total_value: float, category: str = 'outros', subcategory: str = 'outros',
                 xml_id: str = None, reconciled: bool = False, transaction_id: str = None):
        self.item_id = item_id
        self.description = description
        self.quantity = quantity
        self.unit_value = unit_value
        self.total_value = total_value
        self.category = category
        self.subcategory = subcategory
        self.xml_id = xml_id  # ID do XML de origem
        self.reconciled = reconciled
        self.transaction_id = transaction_id  # ID da transação principal quando conciliada
        self.created_at = datetime.now()
        self.reconciled_at = None
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'item_id': self.item_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_value': self.unit_value,
            'total_value': self.total_value,
            'category': self.category,
            'subcategory': self.subcategory,
            'xml_id': self.xml_id,
            'reconciled': self.reconciled,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'reconciled_at': self.reconciled_at.isoformat() if isinstance(self.reconciled_at, datetime) else self.reconciled_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria instância a partir de dicionário"""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        reconciled_at = data.get('reconciled_at')
        if isinstance(reconciled_at, str):
            reconciled_at = datetime.fromisoformat(reconciled_at)
        
        instance = cls(
            item_id=data['item_id'],
            description=data['description'],
            quantity=data['quantity'],
            unit_value=data['unit_value'],
            total_value=data['total_value'],
            category=data.get('category', 'outros'),
            subcategory=data.get('subcategory', 'outros'),
            xml_id=data.get('xml_id'),
            reconciled=data.get('reconciled', False),
            transaction_id=data.get('transaction_id')
        )
        instance.created_at = created_at
        instance.reconciled_at = reconciled_at
        return instance

class SubTransactionXML:
    """Modelo para um XML de subtransações"""
    
    def __init__(self, xml_id: str, filename: str, total_value: float, 
                 emission_date: datetime, establishment_name: str = None):
        self.xml_id = xml_id
        self.filename = filename
        self.total_value = total_value
        self.emission_date = emission_date
        self.establishment_name = establishment_name
        self.subtransactions: List[SubTransaction] = []
        self.reconciled = False
        self.transaction_id = None
        self.created_at = datetime.now()
        self.reconciled_at = None
    
    def add_subtransaction(self, subtransaction: SubTransaction):
        """Adiciona uma subtransação ao XML"""
        subtransaction.xml_id = self.xml_id
        self.subtransactions.append(subtransaction)
    
    def get_total_items(self) -> int:
        """Retorna total de itens"""
        return len(self.subtransactions)
    
    def get_categories_summary(self) -> Dict[str, float]:
        """Retorna resumo por categoria"""
        summary = {}
        for sub in self.subtransactions:
            if sub.category not in summary:
                summary[sub.category] = 0
            summary[sub.category] += sub.total_value
        return summary
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'xml_id': self.xml_id,
            'filename': self.filename,
            'total_value': self.total_value,
            'emission_date': self.emission_date.isoformat() if isinstance(self.emission_date, datetime) else self.emission_date,
            'establishment_name': self.establishment_name,
            'subtransactions': [st.to_dict() for st in self.subtransactions],
            'reconciled': self.reconciled,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'reconciled_at': self.reconciled_at.isoformat() if isinstance(self.reconciled_at, datetime) else self.reconciled_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Cria instância a partir de dicionário"""
        emission_date = data.get('emission_date')
        if isinstance(emission_date, str):
            emission_date = datetime.fromisoformat(emission_date)
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        reconciled_at = data.get('reconciled_at')
        if isinstance(reconciled_at, str):
            reconciled_at = datetime.fromisoformat(reconciled_at)
        
        instance = cls(
            xml_id=data['xml_id'],
            filename=data['filename'],
            total_value=data['total_value'],
            emission_date=emission_date,
            establishment_name=data.get('establishment_name')
        )
        instance.subtransactions = [SubTransaction.from_dict(st) for st in data.get('subtransactions', [])]
        instance.reconciled = data.get('reconciled', False)
        instance.transaction_id = data.get('transaction_id')
        instance.created_at = created_at
        instance.reconciled_at = reconciled_at
        return instance

class SubTransactionManager:
    """Gerenciador de subtransações"""
    
    def __init__(self, data_file='subtransactions.json'):
        self.data_file = data_file
        self.xmls: Dict[str, SubTransactionXML] = {}
        self.subtransactions: Dict[str, SubTransaction] = {}
        self.load_data()
    
    def load_data(self):
        """Carrega dados do arquivo"""
        import os
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Carregar XMLs
                    for xml_id, xml_data in data.get('xmls', {}).items():
                        self.xmls[xml_id] = SubTransactionXML.from_dict(xml_data)
                    
                    # Carregar subtransações
                    for item_id, sub_data in data.get('subtransactions', {}).items():
                        self.subtransactions[item_id] = SubTransaction.from_dict(sub_data)
        except Exception as e:
            print(f"Erro ao carregar dados de subtransações: {e}")
            self.xmls = {}
            self.subtransactions = {}
    
    def save_data(self):
        """Salva dados no arquivo"""
        try:
            data = {
                'xmls': {xml_id: xml.to_dict() for xml_id, xml in self.xmls.items()},
                'subtransactions': {item_id: st.to_dict() for item_id, st in self.subtransactions.items()}
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados de subtransações: {e}")
    
    def add_xml(self, xml: SubTransactionXML):
        """Adiciona um XML de subtransações"""
        self.xmls[xml.xml_id] = xml
        for sub in xml.subtransactions:
            self.subtransactions[sub.item_id] = sub
        self.save_data()
    
    def get_unreconciled_xmls(self) -> List[SubTransactionXML]:
        """Retorna XMLs não conciliados"""
        return [xml for xml in self.xmls.values() if not xml.reconciled]
    
    def get_unreconciled_subtransactions(self) -> List[SubTransaction]:
        """Retorna subtransações não conciliadas"""
        return [st for st in self.subtransactions.values() if not st.reconciled]
    
    def reconcile_xml_with_transaction(self, xml_id: str, transaction_id: str):
        """Concilia um XML com uma transação principal"""
        if xml_id in self.xmls:
            xml = self.xmls[xml_id]
            xml.reconciled = True
            xml.transaction_id = transaction_id
            xml.reconciled_at = datetime.now()
            
            for sub in xml.subtransactions:
                sub.reconciled = True
                sub.transaction_id = transaction_id
                sub.reconciled_at = datetime.now()
            
            self.save_data()
            return True
        return False
    
    def get_reconciliation_suggestions(self, target_date: datetime, target_value: float, 
                                     tolerance_days: int = 3, tolerance_percent: float = 0.05) -> List[SubTransactionXML]:
        """Sugere XMLs para conciliação baseado em data e valor"""
        suggestions = []
        unreconciled_xmls = self.get_unreconciled_xmls()
        
        for xml in unreconciled_xmls:
            # Verificar proximidade da data
            date_diff = abs((xml.emission_date - target_date).days)
            
            # Verificar proximidade do valor
            value_diff = abs(xml.total_value - target_value)
            value_tolerance = target_value * tolerance_percent
            
            if date_diff <= tolerance_days and value_diff <= value_tolerance:
                suggestions.append(xml)
        
        # Ordenar por proximidade (data + valor)
        suggestions.sort(key=lambda x: (
            abs((x.emission_date - target_date).days),
            abs(x.total_value - target_value)
        ))
        
        return suggestions

# Categorias específicas para supermercado
SUPERMARKET_CATEGORIES = {
    'laticinios': {
        'keywords': ['leite', 'queijo', 'iogurte', 'requeijão', 'manteiga', 'creme', 'laticínio'],
        'subcategories': {
            'leite_derivados': ['leite', 'iogurte', 'creme'],
            'queijos': ['queijo', 'requeijão', 'ricota'],
            'manteiga_creme': ['manteiga', 'creme', 'margarina']
        }
    },
    'carnes': {
        'keywords': ['carne', 'frango', 'porco', 'peixe', 'salsicha', 'linguiça', 'bacon', 'hambúrguer'],
        'subcategories': {
            'carnes_vermelhas': ['carne bovina', 'carne suína', 'bacon'],
            'aves': ['frango', 'galinha', 'peru'],
            'embutidos': ['salsicha', 'linguiça', 'hambúrguer', 'nuggets']
        }
    },
    'frutas_verduras': {
        'keywords': ['banana', 'maçã', 'laranja', 'tomate', 'cebola', 'alho', 'batata', 'cenoura', 'alface'],
        'subcategories': {
            'frutas': ['banana', 'maçã', 'laranja', 'uva', 'mamão'],
            'verduras': ['alface', 'couve', 'espinafre', 'rúcula'],
            'legumes': ['tomate', 'cebola', 'alho', 'batata', 'cenoura']
        }
    },
    'bebidas': {
        'keywords': ['água', 'refrigerante', 'suco', 'cerveja', 'vinho', 'café', 'chá'],
        'subcategories': {
            'agua_sucos': ['água', 'suco', 'refresco'],
            'bebidas_alcoolicas': ['cerveja', 'vinho', 'vodka'],
            'cafe_cha': ['café', 'chá', 'achocolatado']
        }
    },
    'limpeza': {
        'keywords': ['detergente', 'sabão', 'desinfetante', 'papel', 'esponja', 'vassoura'],
        'subcategories': {
            'produtos_limpeza': ['detergente', 'sabão', 'desinfetante'],
            'papelaria': ['papel', 'papel higiênico', 'guardanapo'],
            'utensilios': ['esponja', 'vassoura', 'pá']
        }
    },
    'higiene': {
        'keywords': ['shampoo', 'sabonete', 'creme dental', 'desodorante', 'fralda'],
        'subcategories': {
            'cuidados_corpo': ['shampoo', 'sabonete', 'condicionador'],
            'higiene_bucal': ['creme dental', 'escova', 'enxaguante'],
            'cuidados_bebe': ['fralda', 'lenço umedecido']
        }
    },
    'padaria': {
        'keywords': ['pão', 'bolo', 'biscoito', 'torta', 'sanduíche'],
        'subcategories': {
            'paes': ['pão', 'pão de forma', 'pão francês'],
            'doces': ['bolo', 'torta', 'biscoito', 'balas'],
            'salgados': ['sanduíche', 'coxinha', 'pastel']
        }
    },
    'outros': {
        'keywords': [],
        'subcategories': {
            'outros': ['outros']
        }
    }
}

def categorize_supermarket_item(description: str) -> tuple:
    """Categoriza um item de supermercado"""
    description_lower = description.lower()
    
    for category, data in SUPERMARKET_CATEGORIES.items():
        for keyword in data['keywords']:
            if keyword in description_lower:
                # Encontrar subcategoria
                for subcategory, sub_keywords in data['subcategories'].items():
                    for sub_keyword in sub_keywords:
                        if sub_keyword in description_lower:
                            return category, subcategory
                # Se não encontrou subcategoria específica, usar a primeira
                first_subcategory = list(data['subcategories'].keys())[0]
                return category, first_subcategory
    
    return 'outros', 'outros'
