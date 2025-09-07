#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from pdf_analyzer import PDFAnalyzer
from data_handler import DataHandler
import threading

class PDFAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de PDFs de Cartão de Crédito")
        self.root.geometry("1000x700")
        
        # Inicializar componentes
        self.analyzer = PDFAnalyzer()
        self.data_handler = DataHandler()
        self.current_transactions = []
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Analisador de PDFs de Cartão de Crédito", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de seleção de arquivo
        file_frame = ttk.LabelFrame(main_frame, text="Seleção de Arquivo", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Arquivo PDF:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly")
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Procurar", command=self.browse_file)
        browse_btn.grid(row=0, column=2)
        
        analyze_btn = ttk.Button(file_frame, text="Analisar PDF", command=self.analyze_pdf)
        analyze_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Frame de configuração do armazenamento
        storage_frame = ttk.LabelFrame(main_frame, text="Configuração do Armazenamento", padding="10")
        storage_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        storage_frame.columnconfigure(1, weight=1)
        
        ttk.Label(storage_frame, text="Origem do Cartão:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.card_origin_var = tk.StringVar(value="Cartão Principal")
        origin_combo = ttk.Combobox(storage_frame, textvariable=self.card_origin_var, 
                                   values=["Cartão Principal", "Cartão Adicional", "Cartão Corporativo", "Outro"])
        origin_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.remove_duplicates_var = tk.BooleanVar(value=True)
        duplicates_check = ttk.Checkbutton(storage_frame, text="Remover Duplicados", 
                                         variable=self.remove_duplicates_var)
        duplicates_check.grid(row=0, column=2, padx=(10, 0))
        
        save_btn = ttk.Button(storage_frame, text="Salvar Transações", command=self.save_transactions)
        save_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Status do armazenamento
        self.storage_status_var = tk.StringVar(value="Pronto para salvar")
        status_label = ttk.Label(storage_frame, textvariable=self.storage_status_var, 
                                foreground="green")
        status_label.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        # Frame de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados da Análise", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Text widget para mostrar resultados
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de estatísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_var = tk.StringVar(value="Nenhuma análise realizada")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)
    
    def update_status(self):
        """Atualiza o status do armazenamento"""
        try:
            count = self.data_handler.get_transactions_count()
            self.storage_status_var.set(f"Pronto para salvar - {count} transações armazenadas")
        except Exception as e:
            self.storage_status_var.set(f"Erro: {e}")
    
    def browse_file(self):
        """Abre diálogo para selecionar arquivo PDF"""
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def analyze_pdf(self):
        """Analisa o PDF selecionado"""
        file_path = self.file_path_var.get()
        
        if not file_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo PDF")
            return
        
        # Limpar resultados anteriores
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Analisando PDF...\n")
        self.root.update()
        
        try:
            # Analisar PDF
            result = self.analyzer.analyze_pdf(file_path)
            
            # Armazenar transações
            self.current_transactions = result['transacoes']
            
            # Mostrar resultados
            self.display_results(result)
            
            # Atualizar estatísticas
            self.update_stats(result)
            
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"❌ Erro ao analisar PDF: {e}\n")
            messagebox.showerror("Erro", f"Erro ao analisar PDF: {e}")
    
    def display_results(self, result):
        """Exibe os resultados da análise"""
        self.results_text.delete(1.0, tk.END)
        
        # Cabeçalho
        self.results_text.insert(tk.END, f"📊 RESULTADOS DA ANÁLISE\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Informações gerais
        self.results_text.insert(tk.END, f"🏦 Banco detectado: {result['banco_detectado'].upper()}\n")
        self.results_text.insert(tk.END, f"📈 Total de transações: {result['total_transacoes']}\n\n")
        
        # Transações
        self.results_text.insert(tk.END, "💳 TRANSAÇÕES ENCONTRADAS:\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n\n")
        
        for i, trans in enumerate(result['transacoes'], 1):
            self.results_text.insert(tk.END, f"{i:2d}. {trans['data']} - {trans['descricao']}\n")
            self.results_text.insert(tk.END, f"     💰 Valor: R$ {trans['valor']:.2f}\n")
            self.results_text.insert(tk.END, f"     🏷️  Categoria: {trans['categoria']}\n")
            self.results_text.insert(tk.END, f"     🏦 Banco: {trans['banco']}\n")
            
            if trans['parcelado'] == 'Sim':
                self.results_text.insert(tk.END, f"     📅 Parcelado: {trans['parcela_atual']}/{trans['parcela_total']}\n")
            else:
                self.results_text.insert(tk.END, f"     📅 Parcelado: Não\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # JSON completo
        self.results_text.insert(tk.END, "\n" + "=" * 50 + "\n")
        self.results_text.insert(tk.END, "📋 DADOS COMPLETOS (JSON):\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n")
        self.results_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
    
    def update_stats(self, result):
        """Atualiza as estatísticas"""
        total = result['total_transacoes']
        parceladas = sum(1 for t in result['transacoes'] if t['parcelado'] == 'Sim')
        valor_total = sum(t['valor'] for t in result['transacoes'])
        
        stats_text = f"Total: {total} transações | Parceladas: {parceladas} | Valor total: R$ {valor_total:.2f}"
        self.stats_var.set(stats_text)
    
    def save_transactions(self):
        """Salva as transações no arquivo JSON"""
        if not self.current_transactions:
            messagebox.showwarning("Aviso", "Nenhuma transação para salvar. Analise um PDF primeiro.")
            return
        
        card_origin = self.card_origin_var.get()
        remove_duplicates = self.remove_duplicates_var.get()
        
        # Mostrar progresso
        self.results_text.insert(tk.END, f"\n💾 Salvando {len(self.current_transactions)} transações...\n")
        self.results_text.insert(tk.END, f"Origem do cartão: {card_origin}\n")
        self.results_text.insert(tk.END, f"Remover duplicados: {'Sim' if remove_duplicates else 'Não'}\n")
        self.root.update()
        
        def save_worker():
            try:
                result = self.data_handler.save_transactions(
                    self.current_transactions, 
                    card_origin, 
                    remove_duplicates
                )
                
                # Atualizar UI na thread principal
                self.root.after(0, lambda: self.show_save_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: self.show_save_error(e))
        
        # Executar em thread separada
        thread = threading.Thread(target=save_worker)
        thread.daemon = True
        thread.start()
    
    def show_save_result(self, result):
        """Mostra o resultado do salvamento"""
        if result['success']:
            message = f"✅ {result['message']}"
            messagebox.showinfo("Sucesso", result['message'])
        else:
            message = f"❌ {result['message']}"
            messagebox.showerror("Erro", result['message'])
        
        self.results_text.insert(tk.END, f"\n{message}\n")
        
        # Mostrar estatísticas detalhadas
        self.results_text.insert(tk.END, f"📊 Estatísticas:\n")
        self.results_text.insert(tk.END, f"   • Salvas: {result['saved']}\n")
        self.results_text.insert(tk.END, f"   • Duplicadas: {result['duplicates']}\n")
        self.results_text.insert(tk.END, f"   • Erros: {result['errors']}\n")
        
        # Atualizar status
        self.update_status()
    
    def show_save_error(self, error):
        """Mostra erro do salvamento"""
        message = f"❌ Erro ao salvar: {error}"
        self.results_text.insert(tk.END, f"\n{message}\n")
        messagebox.showerror("Erro", f"Erro ao salvar transações: {error}")

def main():
    """Função principal"""
    root = tk.Tk()
    app = PDFAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
