/**
 * FinançasWeb - Funções JavaScript principais
 */

document.addEventListener('DOMContentLoaded', function() {

    // Inicializar todos os tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar todos os popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Função para fechar automaticamente alertas após 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Função para confirmar ações destrutivas
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Tem certeza que deseja realizar esta ação?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Formatação de campos monetários
    const moneyInputs = document.querySelectorAll('.money-input');
    moneyInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            value = (parseInt(value) / 100).toFixed(2);
            this.value = value;
        });
    });

    // Ativar o item de menu correto com base na URL atual
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // Formatação de valores monetários para exibição
    function formatMoney(value, currency = 'BRL') {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: currency
        }).format(value);
    }

    // Função para alternar entre modos claro/escuro (se implementado)
    const themeToggler = document.getElementById('theme-toggler');
    if (themeToggler) {
        themeToggler.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');

            // Salvar preferência no localStorage
            const isDarkMode = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkMode', isDarkMode);

            // Atualizar ícone
            const icon = this.querySelector('i');
            if (isDarkMode) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        });

        // Verificar preferência salva
        const savedDarkMode = localStorage.getItem('darkMode') === 'true';
        if (savedDarkMode) {
            document.body.classList.add('dark-theme');
            const icon = themeToggler.querySelector('i');
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    }

    // Função para toggle de filtros avançados
    const filterToggle = document.getElementById('toggle-advanced-filters');
    if (filterToggle) {
        filterToggle.addEventListener('click', function() {
            const advancedFilters = document.getElementById('advanced-filters');
            if (advancedFilters) {
                advancedFilters.classList.toggle('d-none');

                // Atualizar texto do botão
                if (advancedFilters.classList.contains('d-none')) {
                    this.textContent = 'Mostrar filtros avançados';
                } else {
                    this.textContent = 'Ocultar filtros avançados';
                }
            }
        });
    }

    // Exportar funções para uso global
    window.financasweb = {
        formatMoney: formatMoney
    };

});