// Функция для автоматического скрытия уведомлений
function initToasts() {
    const toasts = document.querySelectorAll('.toast-notification');
    
    toasts.forEach(toast => {
        // Настройка автоматического скрытия через 15 секунд
        const autoHideTimeout = setTimeout(() => {
            hideToast(toast);
        }, 15000);
        
        // Кнопка закрытия
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Предотвращаем всплытие события
                clearTimeout(autoHideTimeout);
                hideToast(toast);
            });
        }
        
        // При наведении мыши останавливаем прогресс-бар
        toast.addEventListener('mouseenter', () => {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'paused';
            }
        });
        
        // При убирании мыши возобновляем прогресс-бар
        toast.addEventListener('mouseleave', () => {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'running';
            }
        });
    });
}

// Функция скрытия уведомления
function hideToast(toast) {
    // Добавляем класс для анимации скрытия
    toast.classList.add('hide');
    
    // После завершения анимации удаляем элемент из DOM
    toast.addEventListener('animationend', () => {
        toast.remove();
        
        // Если контейнер уведомлений пуст, можно удалить его
        const container = document.querySelector('.toast-container');
        if (container && container.children.length === 0) {
            container.remove();
        }
    }, { once: true });
}

// Инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', initToasts);