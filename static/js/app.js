// Global variables
let currentData = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const resultsContent = document.getElementById('resultsContent');
const exportButtons = document.getElementById('exportButtons');
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
});

function initializeUpload() {
    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
}

function handleFileSelect() {
    const file = fileInput.files[0];
    if (!file) return;
    
    if (!file.type.includes('pdf')) {
        showError('Por favor, selecione apenas arquivos PDF.');
        return;
    }
    
    if (file.size > 16 * 1024 * 1024) {
        showError('O arquivo é muito grande. Máximo permitido: 16MB.');
        return;
    }
    
    uploadFile(file);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading modal
    loadingModal.show();
    
    // Show progress bar
    uploadProgress.classList.remove('d-none');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    
    // Simulate progress (since we don't have real progress from server)
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        progressBar.style.width = progress + '%';
    }, 200);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        
        setTimeout(() => {
            loadingModal.hide();
            uploadProgress.classList.add('d-none');
            progressBar.style.width = '0%';
            
            if (data.success) {
                currentData = data.data;
                displayResults(data.data, data.filename);
                exportButtons.classList.remove('d-none');
            } else {
                showError(data.error || 'Erro desconhecido ao processar arquivo.');
            }
        }, 500);
    })
    .catch(error => {
        clearInterval(progressInterval);
        loadingModal.hide();
        uploadProgress.classList.add('d-none');
        progressBar.style.width = '0%';
        showError('Erro de conexão. Tente novamente.');
        console.error('Error:', error);
    });
}

function displayResults(data, filename) {
    const { banco_detectado, total_transacoes, transacoes } = data;
    
    // Calculate summary statistics
    const totalAmount = transacoes.reduce((sum, t) => sum + t.valor, 0);
    const installmentCount = transacoes.filter(t => t.parcelado === 'Sim').length;
    const categories = {};
    
    transacoes.forEach(t => {
        categories[t.categoria] = (categories[t.categoria] || 0) + 1;
    });
    
    const html = `
        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card summary-card">
                    <div class="card-body text-center">
                        <div class="summary-number">${total_transacoes}</div>
                        <div>Transações</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <div class="summary-number">R$ ${totalAmount.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div>Total Gasto</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <div class="summary-number">${installmentCount}</div>
                        <div>Parceladas</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <div class="summary-number">${banco_detectado.toUpperCase()}</div>
                        <div>Banco Detectado</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- File Info -->
        <div class="alert alert-info mb-3">
            <i class="fas fa-info-circle me-2"></i>
            <strong>Arquivo:</strong> ${filename} | 
            <strong>Banco:</strong> ${banco_detectado.toUpperCase()} | 
            <strong>Transações encontradas:</strong> ${total_transacoes}
        </div>
        
        <!-- Categories Distribution -->
        <div class="row mb-4">
            <div class="col-12">
                <h5>Distribuição por Categoria</h5>
                <div class="row">
                    ${Object.entries(categories).map(([cat, count]) => `
                        <div class="col-md-2 col-sm-4 col-6 mb-2">
                            <span class="badge category-${cat} w-100 py-2">
                                ${cat.charAt(0).toUpperCase() + cat.slice(1)} (${count})
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
        
        <!-- Transactions Table -->
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                        <th>Valor</th>
                        <th>Parcelado</th>
                        <th>Parcela</th>
                        <th>Categoria</th>
                    </tr>
                </thead>
                <tbody>
                    ${transacoes.map(transaction => `
                        <tr>
                            <td>${transaction.data}</td>
                            <td>${transaction.descricao}</td>
                            <td class="text-end">R$ ${transaction.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                            <td>
                                <span class="badge ${transaction.parcelado === 'Sim' ? 'badge-installment' : 'badge-single'}">
                                    ${transaction.parcelado}
                                </span>
                            </td>
                            <td>
                                ${transaction.parcelado === 'Sim' ? 
                                    `${transaction.parcela_atual}/${transaction.parcela_total}` : 
                                    '-'
                                }
                            </td>
                            <td>
                                <span class="badge category-${transaction.categoria}">
                                    ${transaction.categoria.charAt(0).toUpperCase() + transaction.categoria.slice(1)}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

function exportData(format) {
    if (!currentData || !currentData.transacoes) {
        showError('Nenhum dado para exportar.');
        return;
    }
    
    const data = encodeURIComponent(JSON.stringify(currentData.transacoes));
    const url = `/export/${format}?data=${data}`;
    
    // Create temporary link and click it
    const link = document.createElement('a');
    link.href = url;
    link.download = `faturas_analisadas.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    errorModal.show();
}

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}