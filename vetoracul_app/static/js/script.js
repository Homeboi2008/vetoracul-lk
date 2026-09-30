document.addEventListener('DOMContentLoaded', () => {
  // 1. Навигация между страницами
  const menuItems = document.querySelectorAll('.menu-item');
  const pages = document.querySelectorAll('.page');

  menuItems.forEach(item => {
    item.addEventListener('click', () => {
      // Убираем active у всех пунктов меню
      menuItems.forEach(mi => mi.classList.remove('active'));
      // Добавляем active на кликнутый
      item.classList.add('active');
      
      // Получаем id страницы и переключаем видимость
      const pageId = item.getAttribute('data-page');
      pages.forEach(page => page.classList.remove('active'));
      document.getElementById(pageId).classList.add('active');
    });
  });

  // 2. Закрытие панели пользователя при клике вне её области
  document.addEventListener('click', (event) => {
    const userPanel = document.getElementById('userPanel');
    const avatarWrapper = document.querySelector('.user-avatar-wrapper');
    
    if (userPanel && userPanel.classList.contains('active')) {
      if (!avatarWrapper.contains(event.target)) {
        userPanel.classList.remove('active');
      }
    }
  });
});

// ===== ФУНКЦИИ ИНТЕРФЕЙСА =====

// Переключение видимости панели пользователя
function toggleUserPanel() {
  const panel = document.getElementById('userPanel');
  panel.classList.toggle('active');
}

// Универсальная заглушка для нереализованного функционала
function stubAction(actionName) {
  console.log(`[Заглушка] Выполняется действие: ${actionName}`);
  alert(`⚠️ Функция "${actionName}" находится в разработке.\n\nЗдесь будет открываться соответствующее модальное окно или форма.`);
}

// Быстрые вызовы заглушек для кнопок карточек
function addNewPet() {
  stubAction('Добавление нового питомца');
}

// Переключение видимости панели уведомлений
function toggleNotifications() {
  const panel = document.getElementById('notificationsPanel');
  panel.classList.toggle('active');
  
  // Закрываем панель пользователя, если она открыта
  const userPanel = document.getElementById('userPanel');
  if (userPanel && userPanel.classList.contains('active')) {
    userPanel.classList.remove('active');
  }
}

// Обнови обработчик клика вне панелей
document.addEventListener('click', (event) => {
  const userPanel = document.getElementById('userPanel');
  const avatarWrapper = document.querySelector('.user-avatar-wrapper');
  const notificationsPanel = document.getElementById('notificationsPanel');
  const notificationsWrapper = document.querySelector('.notifications-wrapper');
  
  // Закрываем панель пользователя
  if (userPanel && userPanel.classList.contains('active')) {
    if (!avatarWrapper.contains(event.target)) {
      userPanel.classList.remove('active');
    }
  }
  
  // Закрываем панель уведомлений
  if (notificationsPanel && notificationsPanel.classList.contains('active')) {
    if (!notificationsWrapper.contains(event.target)) {
      notificationsPanel.classList.remove('active');
    }
  }
});

// ===== ДАННЫЕ ДОКУМЕНТОВ =====
document.addEventListener('DOMContentLoaded', () => {
  // Навигация между страницами
  const menuItems = document.querySelectorAll('.menu-item');
  const pages = document.querySelectorAll('.page');

  menuItems.forEach(item => {
    item.addEventListener('click', () => {
      menuItems.forEach(mi => mi.classList.remove('active'));
      item.classList.add('active');
      
      const pageId = item.getAttribute('data-page');
      pages.forEach(page => page.classList.remove('active'));
      document.getElementById(pageId).classList.add('active');
    });
  });

  // Закрытие панелей при клике вне их
  document.addEventListener('click', (event) => {
    const userPanel = document.getElementById('userPanel');
    const avatarWrapper = document.querySelector('.user-avatar-wrapper');
    const notificationsPanel = document.getElementById('notificationsPanel');
    const notificationsWrapper = document.querySelector('.notifications-wrapper');
    
    if (userPanel && userPanel.classList.contains('active')) {
      if (!avatarWrapper.contains(event.target)) {
        userPanel.classList.remove('active');
      }
    }
    
    if (notificationsPanel && notificationsPanel.classList.contains('active')) {
      if (!notificationsWrapper.contains(event.target)) {
        notificationsPanel.classList.remove('active');
      }
    }
  });

  // Инициализация документов
  renderDocuments();
});

// ===== ФУНКЦИИ ИНТЕРФЕЙСА =====

function toggleUserPanel() {
  const panel = document.getElementById('userPanel');
  panel.classList.toggle('active');
  
  const notificationsPanel = document.getElementById('notificationsPanel');
  if (notificationsPanel && notificationsPanel.classList.contains('active')) {
    notificationsPanel.classList.remove('active');
  }
}

function toggleNotifications() {
  const panel = document.getElementById('notificationsPanel');
  panel.classList.toggle('active');
  
  const userPanel = document.getElementById('userPanel');
  if (userPanel && userPanel.classList.contains('active')) {
    userPanel.classList.remove('active');
  }
}

function stubAction(actionName) {
  console.log(`[Заглушка] Выполняется действие: ${actionName}`);
  alert(`️ Функция "${actionName}" находится в разработке.\n\nЗдесь будет открываться соответствующее модальное окно или форма.`);
}

function addNewPet() {
  stubAction('Добавление нового питомца');
}

// ===== ДАННЫЕ ДОКУМЕНТОВ =====
const documentsData = [
  {
    id: 1,
    title: 'Анализ крови общий',
    type: 'analysis',
    petName: 'Барсик',
    petId: 'barsik',
    size: '1.2 МБ',
    date: '2026-08-12',
    dateDisplay: '12.08.2026',
    format: 'PDF'
  },
  {
    id: 2,
    title: 'Рентген передней лапы',
    type: 'xray',
    petName: 'Барсик',
    petId: 'barsik',
    size: '3.4 МБ',
    date: '2026-08-10',
    dateDisplay: '10.08.2026',
    format: 'JPG'
  },
  {
    id: 3,
    title: 'Рецепт',
    type: 'prescription',
    petName: 'Барсик',
    petId: 'barsik',
    size: '450 КБ',
    date: '2026-08-12',
    dateDisplay: '12.08.2026',
    format: 'PDF'
  },
  {
    id: 4,
    title: 'Ветеринарный паспорт',
    type: 'passport',
    petName: 'Рекс',
    petId: 'reks',
    size: '850 КБ',
    date: '2026-03-15',
    dateDisplay: '15.03.2026',
    format: 'PDF'
  },
  {
    id: 5,
    title: 'Сертификат вакцинации',
    type: 'vaccination',
    petName: 'Рекс',
    petId: 'reks',
    size: '620 КБ',
    date: '2026-07-28',
    dateDisplay: '28.07.2026',
    format: 'PDF'
  },
  {
    id: 6,
    title: 'Осмотр терапевта',
    type: 'analysis',
    petName: 'Рекс',
    petId: 'reks',
    size: '1.1 МБ',
    date: '2026-07-28',
    dateDisplay: '28.07.2026',
    format: 'PDF'
  }
];

// ===== СОСТОЯНИЕ =====
let currentFilter = 'all';
let currentView = 'grid';
let searchQuery = '';

// ===== РЕНДЕР ДОКУМЕНТОВ =====
function renderDocuments() {
  const container = document.getElementById('docsContainer');
  const emptyState = document.getElementById('docsEmpty');
  
  // Фильтрация по питомцу
  let filtered = documentsData.filter(doc => {
    const matchFilter = currentFilter === 'all' || doc.petId === currentFilter;
    const matchSearch = searchQuery === '' || 
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.petName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchFilter && matchSearch;
  });

  // Сортировка по дате (новые сверху)
  filtered.sort((a, b) => new Date(b.date) - new Date(a.date));

  // Показ пустого состояния
  if (filtered.length === 0) {
    container.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'grid';
  emptyState.style.display = 'none';

  // Рендер карточек
  container.innerHTML = filtered.map(doc => `
    <div class="doc-card" data-id="${doc.id}">
      <div class="doc-card__preview">
        <div class="doc-card__format-badge">
          <span class="doc-card__format-large">${doc.format}</span>
        </div>
      </div>
      <div class="doc-card__body">
        <h3 class="doc-card__title">${doc.title}</h3>
        <div class="doc-card__pet">
          <span>${doc.petName}</span>
        </div>
        <div class="doc-card__meta">
          <span>${doc.dateDisplay}</span>
          <span>${doc.size}</span>
        </div>
      </div>
      <div class="doc-card__footer">
        <button class="btn btn-secondary" onclick="viewDocument('${doc.title}')">
          Просмотр
        </button>
        <button class="btn btn-primary" onclick="downloadDocument('${doc.title}')">
          Скачать
        </button>
      </div>
    </div>
  `).join('');
}

// ===== УПРАВЛЕНИЕ ФИЛЬТРАМИ =====
function setFilter(filter, btn) {
  currentFilter = filter;
  
  // Обновляем активную кнопку
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  renderDocuments();
}

// ===== ПОИСК =====
function filterDocuments() {
  const input = document.getElementById('docsSearchInput');
  searchQuery = input.value;
  renderDocuments();
}

// ===== ПЕРЕКЛЮЧЕНИЕ ВИДА =====
function setView(view, btn) {
  currentView = view;
  const container = document.getElementById('docsContainer');
  
  // Обновляем активную кнопку
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  // Переключаем класс контейнера
  if (view === 'list') {
    container.classList.add('view-list');
  } else {
    container.classList.remove('view-list');
  }
}

// ===== ДЕЙСТВИЯ С ДОКУМЕНТАМИ =====
function viewDocument(title) {
  console.log('Просмотр документа:', title);
  alert(`📄 Просмотр документа: ${title}\n\nЗдесь будет открываться PDF-просмотрщик или изображение.`);
}

function downloadDocument(title) {
  console.log('Скачивание документа:', title);
  alert(`⬇️ Скачивание: ${title}\n\nЗдесь будет загрузка файла.`);
}

// ===== ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ =====
document.addEventListener('DOMContentLoaded', function() {
  renderDocuments();
});

// ===== ДАННЫЕ НАПОМИНАНИЙ =====
const remindersData = [
  {
    id: 1,
    title: 'Приём у ветеринара',
    petName: 'Барсик',
    date: '2026-09-08',
    time: '14:00',
    type: 'appointment',
    description: 'Плановый осмотр'
  },
  {
    id: 2,
    title: 'Вакцинация',
    petName: 'Рекс',
    date: '2026-09-15',
    time: '11:00',
    type: 'vaccination',
    description: 'Комплексная прививка'
  },
  {
    id: 3,
    title: 'Приём лекарств',
    petName: 'Барсик',
    date: '2026-09-10',
    time: '08:00',
    type: 'medication',
    description: 'Антигистаминные препараты'
  },
  {
    id: 4,
    title: 'Стрижка когтей',
    petName: 'Рекс',
    date: '2026-09-20',
    time: '16:00',
    type: 'grooming',
    description: 'Гигиеническая процедура'
  },
  {
    id: 5,
    title: 'Анализ крови',
    petName: 'Барсик',
    date: '2026-09-25',
    time: '10:00',
    type: 'analysis',
    description: 'Контрольный анализ'
  },
  {
    id: 6,
    title: 'Осмотр зубов',
    petName: 'Рекс',
    date: '2026-08-28',
    time: '12:00',
    type: 'appointment',
    description: 'Профилактический осмотр'
  }
];

// ===== СОСТОЯНИЕ КАЛЕНДАРЯ =====
let currentDate = new Date(); // ТЕКУЩАЯ ДАТА АВТОМАТИЧЕСКИ
let currentReminderFilter = 'upcoming';

// ===== РЕНДЕР КАЛЕНДАРЯ =====
function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  
  document.getElementById('calendarTitle').textContent = `${monthNames[month]} ${year}`;
  
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  
  // Понедельник = 0, Воскресенье = 6
  let startDay = firstDay.getDay() - 1;
  if (startDay < 0) startDay = 6;
  
  const grid = document.getElementById('calendarGrid');
  grid.innerHTML = '';
  
  // Получаем сегодняшнюю дату для выделения
  const today = new Date();
  const todayDate = today.getDate();
  const todayMonth = today.getMonth();
  const todayYear = today.getFullYear();
  
  // Дни предыдущего месяца
  const prevMonthDays = new Date(year, month, 0).getDate();
  for (let i = startDay - 1; i >= 0; i--) {
    const day = prevMonthDays - i;
    const dayEl = createDayElement(day, true, false, false);
    grid.appendChild(dayEl);
  }
  
  // Дни текущего месяца
  for (let day = 1; day <= daysInMonth; day++) {
    // Проверяем, является ли этот день "сегодня"
    const isToday = (day === todayDate && month === todayMonth && year === todayYear);
    
    // Проверяем, есть ли напоминание на этот день
    const hasReminder = remindersData.some(r => {
      const rDate = new Date(r.date);
      return rDate.getDate() === day && rDate.getMonth() === month && rDate.getFullYear() === year;
    });
    
    const dayEl = createDayElement(day, false, isToday, hasReminder);
    grid.appendChild(dayEl);
  }
  
  // Дни следующего месяца
  const totalCells = startDay + daysInMonth;
  const remainingCells = 42 - totalCells;
  for (let day = 1; day <= remainingCells; day++) {
    const dayEl = createDayElement(day, true, false, false);
    grid.appendChild(dayEl);
  }
}

function createDayElement(day, isOtherMonth, isToday, hasReminder) {
  const dayEl = document.createElement('div');
  dayEl.className = 'calendar-day';
  dayEl.textContent = day;
  
  if (isOtherMonth) dayEl.classList.add('other-month');
  if (isToday) dayEl.classList.add('today');
  if (hasReminder) dayEl.classList.add('has-reminder');
  
  return dayEl;
}

function changeMonth(delta) {
  currentDate.setMonth(currentDate.getMonth() + delta);
  renderCalendar();
}

// ===== РЕНДЕР НАПОМИНАНИЙ =====
function renderReminders() {
  const container = document.getElementById('remindersItems');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  // Фильтрация
  let filtered = remindersData.filter(reminder => {
    const rDate = new Date(reminder.date);
    rDate.setHours(0, 0, 0, 0);
    
    if (currentReminderFilter === 'upcoming') {
      return rDate >= today;
    }
    return true;
  });
  
  // Сортировка по дате
  filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
  
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="reminders-empty">
        <div class="reminders-empty-icon"></div>
        <p>Нет напоминаний</p>
      </div>
    `;
    return;
  }
  
  const monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 
                      'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  
  container.innerHTML = filtered.map(reminder => {
    const rDate = new Date(reminder.date);
    const isToday = rDate.getTime() === today.getTime();
    const isPast = rDate < today;
    
    let statusClass = 'reminder-status--upcoming';
    let statusText = 'Предстоит';
    
    if (isToday) {
      statusClass = 'reminder-status--today';
      statusText = 'Сегодня';
    } else if (isPast) {
      statusClass = 'reminder-status--past';
      statusText = 'Прошло';
    }
    
    return `
      <div class="reminder-card">
        <div class="reminder-date-box">
          <div class="reminder-date-day">${rDate.getDate()}</div>
          <div class="reminder-date-month">${monthNames[rDate.getMonth()]}</div>
        </div>
        <div class="reminder-info">
          <h4 class="reminder-title">${reminder.title}</h4>
          <p class="reminder-meta">${reminder.time} • ${reminder.petName} • ${reminder.description}</p>
        </div>
        <span class="reminder-status ${statusClass}">${statusText}</span>
      </div>
    `;
  }).join('');
}

function filterReminders(filter, btn) {
  currentReminderFilter = filter;
  
  document.querySelectorAll('.reminder-filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  renderReminders();
}

function addReminder() {
  alert('⚠️ Функция добавления напоминания находится в разработке.\n\nЗдесь будет открываться форма с полями:\n- Название\n- Питомец\n- Дата и время\n- Тип события\n- Описание');
}

// ===== ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ =====
document.addEventListener('DOMContentLoaded', function() {
  renderCalendar();
  renderReminders();
});

