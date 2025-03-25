// Arquivo com funções JavaScript personalizadas

// Formatar números para moeda brasileira (R$)
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Código a ser executado quando a página carregar completamente
    console.log('FinançasWeb - JavaScript carregado');

    // Definir o ano atual no rodapé
    if (document.querySelector('#current-year')) {
        const yearElement = document.querySelector('#current-year');
        const currentYear = new Date().getFullYear();
        yearElement.textContent = currentYear;
    }
});