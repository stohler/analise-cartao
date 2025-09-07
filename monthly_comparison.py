#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import calendar

class MonthlyComparison:
    def __init__(self, data_handler=None, mongo_handler=None):
        """
        Inicializa o sistema de comparação mensal
        
        Args:
            data_handler: Handler para dados locais (JSON)
            mongo_handler: Handler para MongoDB (quando disponível)
        """
        self.data_handler = data_handler
        self.mongo_handler = mongo_handler
    
    def get_transactions_by_period(self, start_date: datetime, end_date: datetime, card_origin: str = None) -> List[Dict]:
        """
        Obtém transações por período
        
        Args:
            start_date: Data de início
            end_date: Data de fim
            card_origin: Origem do cartão (opcional)
            
        Returns:
            List[Dict]: Lista de transações no período
        """
        transactions = []
        
        # Tentar MongoDB primeiro
        if self.mongo_handler and self.mongo_handler.collection:
            try:
                query = {
                    "data": {
                        "$gte": start_date.strftime("%d/%m/%Y"),
                        "$lte": end_date.strftime("%d/%m/%Y")
                    }
                }
                
                if card_origin:
                    query["origem_cartao"] = card_origin
                
                cursor = self.mongo_handler.collection.find(query)
                transactions = list(cursor)
                
            except Exception as e:
                print(f"⚠️ Erro ao consultar MongoDB: {e}")
                transactions = []
        
        # Fallback para dados locais
        if not transactions and self.data_handler:
            all_transactions = self.data_handler.get_all_transactions(limit=10000)
            
            for trans in all_transactions:
                try:
                    # Converter data da transação
                    trans_date = datetime.strptime(trans['data'], "%d/%m/%Y")
                    
                    # Verificar se está no período
                    if start_date <= trans_date <= end_date:
                        # Filtrar por origem do cartão se especificado
                        if not card_origin or trans.get('origem_cartao') == card_origin:
                            transactions.append(trans)
                            
                except ValueError:
                    # Ignorar transações com data inválida
                    continue
        
        return transactions
    
    def get_last_6_months_data(self, card_origin: str = None) -> Dict[str, List[Dict]]:
        """
        Obtém dados dos últimos 6 meses
        
        Args:
            card_origin: Origem do cartão (opcional)
            
        Returns:
            Dict[str, List[Dict]]: Dados organizados por mês
        """
        today = datetime.now()
        months_data = {}
        
        for i in range(6):
            # Calcular data do mês (6 meses atrás até hoje)
            month_date = today - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Último dia do mês
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
            
            month_end = month_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Obter transações do mês
            month_transactions = self.get_transactions_by_period(month_start, month_end, card_origin)
            
            # Nome do mês
            month_name = f"{month_date.year}-{month_date.month:02d}"
            months_data[month_name] = month_transactions
        
        return months_data
    
    def calculate_monthly_statistics(self, transactions: List[Dict]) -> Dict:
        """
        Calcula estatísticas mensais
        
        Args:
            transactions: Lista de transações do mês
            
        Returns:
            Dict: Estatísticas do mês
        """
        if not transactions:
            return {
                'total_transactions': 0,
                'total_value': 0.0,
                'by_category': {},
                'by_bank': {},
                'installments': 0,
                'average_transaction': 0.0,
                'top_merchants': []
            }
        
        stats = {
            'total_transactions': len(transactions),
            'total_value': 0.0,
            'by_category': defaultdict(float),
            'by_bank': defaultdict(int),
            'installments': 0,
            'merchants': defaultdict(float)
        }
        
        for trans in transactions:
            # Valor total
            stats['total_value'] += trans.get('valor', 0)
            
            # Por categoria
            category = trans.get('categoria', 'outros')
            stats['by_category'][category] += trans.get('valor', 0)
            
            # Por banco
            bank = trans.get('banco', 'desconhecido')
            stats['by_bank'][bank] += 1
            
            # Parceladas
            if trans.get('parcelado') == 'Sim':
                stats['installments'] += 1
            
            # Merchants (primeiras palavras da descrição)
            description = trans.get('descricao', '')
            merchant = description.split()[0] if description else 'Desconhecido'
            stats['merchants'][merchant] += trans.get('valor', 0)
        
        # Calcular média
        stats['average_transaction'] = stats['total_value'] / stats['total_transactions'] if stats['total_transactions'] > 0 else 0
        
        # Top 5 merchants
        stats['top_merchants'] = sorted(stats['merchants'].items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Converter defaultdict para dict
        stats['by_category'] = dict(stats['by_category'])
        stats['by_bank'] = dict(stats['by_bank'])
        
        return stats
    
    def generate_comparison_report(self, card_origin: str = None) -> Dict:
        """
        Gera relatório comparativo dos últimos 6 meses
        
        Args:
            card_origin: Origem do cartão (opcional)
            
        Returns:
            Dict: Relatório comparativo
        """
        print("📊 Gerando relatório comparativo dos últimos 6 meses...")
        
        # Obter dados dos últimos 6 meses
        months_data = self.get_last_6_months_data(card_origin)
        
        # Calcular estatísticas para cada mês
        monthly_stats = {}
        for month, transactions in months_data.items():
            monthly_stats[month] = self.calculate_monthly_statistics(transactions)
        
        # Calcular tendências
        trends = self.calculate_trends(monthly_stats)
        
        # Gerar insights
        insights = self.generate_insights(monthly_stats, trends)
        
        report = {
            'period': 'Últimos 6 meses',
            'card_origin': card_origin or 'Todos os cartões',
            'generated_at': datetime.now().isoformat(),
            'monthly_data': monthly_stats,
            'trends': trends,
            'insights': insights,
            'summary': self.generate_summary(monthly_stats)
        }
        
        return report
    
    def calculate_trends(self, monthly_stats: Dict) -> Dict:
        """
        Calcula tendências entre os meses
        
        Args:
            monthly_stats: Estatísticas mensais
            
        Returns:
            Dict: Tendências calculadas
        """
        months = sorted(monthly_stats.keys())
        
        if len(months) < 2:
            return {'insufficient_data': True}
        
        trends = {
            'value_trend': 0,  # -1 (diminuindo), 0 (estável), 1 (aumentando)
            'transaction_count_trend': 0,
            'average_trend': 0,
            'category_trends': {},
            'monthly_changes': {}
        }
        
        # Calcular mudanças mês a mês
        for i in range(1, len(months)):
            prev_month = months[i-1]
            curr_month = months[i]
            
            prev_stats = monthly_stats[prev_month]
            curr_stats = monthly_stats[curr_month]
            
            # Mudança de valor
            if prev_stats['total_value'] > 0:
                value_change = ((curr_stats['total_value'] - prev_stats['total_value']) / prev_stats['total_value']) * 100
            else:
                value_change = 100 if curr_stats['total_value'] > 0 else 0
            
            trends['monthly_changes'][curr_month] = {
                'value_change_percent': value_change,
                'transaction_change': curr_stats['total_transactions'] - prev_stats['total_transactions'],
                'average_change_percent': 0  # Será calculado abaixo
            }
        
        # Calcular tendência geral
        if len(months) >= 3:
            recent_months = months[-3:]  # Últimos 3 meses
            older_months = months[:3]    # Primeiros 3 meses
            
            recent_avg = sum(monthly_stats[m]['total_value'] for m in recent_months) / len(recent_months)
            older_avg = sum(monthly_stats[m]['total_value'] for m in older_months) / len(older_months)
            
            if older_avg > 0:
                overall_change = ((recent_avg - older_avg) / older_avg) * 100
                if overall_change > 5:
                    trends['value_trend'] = 1  # Aumentando
                elif overall_change < -5:
                    trends['value_trend'] = -1  # Diminuindo
                else:
                    trends['value_trend'] = 0  # Estável
        
        return trends
    
    def generate_insights(self, monthly_stats: Dict, trends: Dict) -> List[str]:
        """
        Gera insights baseados nos dados
        
        Args:
            monthly_stats: Estatísticas mensais
            trends: Tendências calculadas
            
        Returns:
            List[str]: Lista de insights
        """
        insights = []
        
        # Insight sobre tendência de gastos
        if trends.get('value_trend') == 1:
            insights.append("📈 Tendência de aumento nos gastos nos últimos meses")
        elif trends.get('value_trend') == -1:
            insights.append("📉 Tendência de redução nos gastos nos últimos meses")
        else:
            insights.append("📊 Gastos relativamente estáveis nos últimos meses")
        
        # Insight sobre mês com maior gasto
        max_month = max(monthly_stats.keys(), key=lambda m: monthly_stats[m]['total_value'])
        max_value = monthly_stats[max_month]['total_value']
        if max_value > 0:
            insights.append(f"💰 Maior gasto: {max_month} (R$ {max_value:.2f})")
        
        # Insight sobre categorias
        all_categories = defaultdict(float)
        for month_stats in monthly_stats.values():
            for category, value in month_stats['by_category'].items():
                all_categories[category] += value
        
        if all_categories:
            top_category = max(all_categories.items(), key=lambda x: x[1])
            insights.append(f"🏷️ Categoria com maior gasto: {top_category[0]} (R$ {top_category[1]:.2f})")
        
        # Insight sobre parcelamentos
        total_installments = sum(stats['installments'] for stats in monthly_stats.values())
        total_transactions = sum(stats['total_transactions'] for stats in monthly_stats.values())
        
        if total_transactions > 0:
            installment_percentage = (total_installments / total_transactions) * 100
            insights.append(f"📅 {installment_percentage:.1f}% das transações são parceladas")
        
        return insights
    
    def generate_summary(self, monthly_stats: Dict) -> Dict:
        """
        Gera resumo executivo
        
        Args:
            monthly_stats: Estatísticas mensais
            
        Returns:
            Dict: Resumo executivo
        """
        total_value = sum(stats['total_value'] for stats in monthly_stats.values())
        total_transactions = sum(stats['total_transactions'] for stats in monthly_stats.values())
        total_installments = sum(stats['installments'] for stats in monthly_stats.values())
        
        # Calcular média mensal
        months_with_data = [m for m, stats in monthly_stats.items() if stats['total_transactions'] > 0]
        avg_monthly_value = total_value / len(months_with_data) if months_with_data else 0
        
        return {
            'total_value_6_months': total_value,
            'total_transactions_6_months': total_transactions,
            'total_installments_6_months': total_installments,
            'average_monthly_value': avg_monthly_value,
            'average_transaction_value': total_value / total_transactions if total_transactions > 0 else 0,
            'months_with_activity': len(months_with_data),
            'installment_percentage': (total_installments / total_transactions * 100) if total_transactions > 0 else 0
        }
    
    def export_comparison_report(self, report: Dict, filename: str = None) -> str:
        """
        Exporta relatório para arquivo JSON
        
        Args:
            report: Relatório gerado
            filename: Nome do arquivo (opcional)
            
        Returns:
            str: Caminho do arquivo gerado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_comparativo_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Relatório exportado para: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Erro ao exportar relatório: {e}")
            return None

# Exemplo de uso
if __name__ == "__main__":
    from data_handler import DataHandler
    
    # Criar handler de dados
    data_handler = DataHandler()
    
    # Criar comparador
    comparator = MonthlyComparison(data_handler=data_handler)
    
    # Gerar relatório
    report = comparator.generate_comparison_report()
    
    # Mostrar resumo
    print("\n📊 RESUMO EXECUTIVO - ÚLTIMOS 6 MESES")
    print("="*50)
    summary = report['summary']
    print(f"💰 Valor total: R$ {summary['total_value_6_months']:.2f}")
    print(f"📈 Média mensal: R$ {summary['average_monthly_value']:.2f}")
    print(f"💳 Total de transações: {summary['total_transactions_6_months']}")
    print(f"📅 Parcelamentos: {summary['total_installments_6_months']} ({summary['installment_percentage']:.1f}%)")
    
    # Mostrar insights
    print(f"\n💡 INSIGHTS:")
    for insight in report['insights']:
        print(f"   {insight}")
    
    # Exportar relatório
    comparator.export_comparison_report(report)
