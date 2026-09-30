//лк врача

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

  // Глобальная функция переключения
  window.switchPage = function(pageId) {
    menuItems.forEach(mi => {
      mi.classList.remove('active');
      if (mi.getAttribute('data-page') === pageId) {
        mi.classList.add('active');
      }
    });
    pages.forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    
    document.getElementById('userPanel').classList.remove('active');
    document.getElementById('notificationsPanel').classList.remove('active');
  };

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

  // Инициализация
  renderPatients();
  renderCalendar();
  renderSchedule();
});

// Функции интерфейса
function toggleUserPanel() {
  const panel = document.getElementById('userPanel');
  panel.classList.toggle('active');
  document.getElementById('notificationsPanel').classList.remove('active');
}

function toggleNotifications() {
  const panel = document.getElementById('notificationsPanel');
  panel.classList.toggle('active');
  document.getElementById('userPanel').classList.remove('active');
}

function stubAction(actionName) {
  console.log(`[Заглушка] Выполняется действие: ${actionName}`);
  alert(`⚠️ Функция "${actionName}" находится в разработке.`);
}

// Данные пациентов
const patientsData = [
  {
    id: 1,
    name: 'Барсик',
    breed: 'Кот, Британская • ♂ • 6 лет',
    owner: 'Иванова Мария Петровна',
    phone: '+7 (999) 123-45-67',
    email: 'maria.ivanova@mail.ru',
    diagnosis: 'Аллергический дерматит',
    avatarLetter: 'Б',
    avatarClass: 'pet-mini-avatar--blue'
  },
  {
    id: 2,
    name: 'Рекс',
    breed: 'Собака, Немецкая овчарка • ♂ • 3 года',
    owner: 'Петров Сергей Иванович',
    phone: '+7 (999) 234-56-78',
    email: 'petrov.s@mail.ru',
    diagnosis: 'Здоров (плановая вакцинация)',
    avatarLetter: 'Р',
    avatarClass: 'pet-mini-avatar--purple'
  },
  {
    id: 3,
    name: 'Мурка',
    breed: 'Кот, Домашняя • ♀ • 2 года',
    owner: 'Сидорова Анна Владимировна',
    phone: '+7 (999) 345-67-89',
    email: 'sidorova.a@mail.ru',
    diagnosis: 'Постоперационный период (стерилизация)',
    avatarLetter: 'М',
    avatarClass: 'pet-mini-avatar--blue'
  }
];

// Состояние
let currentPatientsView = 'grid';

// Рендер пациентов
function renderPatients() {
  const container = document.getElementById('patientsList');
  const emptyState = document.getElementById('patientsEmpty');
  const searchQuery = document.getElementById('patientsSearchInput').value.toLowerCase();
  
  const filtered = patientsData.filter(patient => {
    return patient.name.toLowerCase().includes(searchQuery) ||
           patient.owner.toLowerCase().includes(searchQuery) ||
           patient.diagnosis.toLowerCase().includes(searchQuery);
  });

  if (filtered.length === 0) {
    container.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'grid';
  emptyState.style.display = 'none';

  container.innerHTML = filtered.map(patient => `
    <div class="pet-card">
      <div class="pet-card__header">
        <div class="pet-card__avatar pet-card__avatar--letter">
          <div class="pet-mini-avatar ${patient.avatarClass}">
            <span class="pet-mini-letter">${patient.avatarLetter}</span>
          </div>
        </div>
        <div class="pet-card__info">
          <h3 class="pet-card__name">${patient.name}</h3>
          <p class="pet-card__breed">${patient.breed}</p>
        </div>
        <span class="pet-card__status status-active">Активен</span>
      </div>

      <div class="pet-card__body">
        <div class="pet-card__section">
          <h4 class="section-title"> Владелец</h4>
          <div class="info-row info-row--compact">
            <span class="info-label">ФИО:</span>
            <span class="info-value">${patient.owner}</span>
          </div>
        </div>

        <div class="pet-card__section">
          <h4 class="section-title">🩺 Медицинские данные</h4>
          <div class="info-item" style="width: 100%;">
            <span class="info-label">Текущий диагноз / Статус</span>
            <span class="info-value highlight">${patient.diagnosis}</span>
          </div>
        </div>
      </div>

      <div class="pet-card__footer">
        <button class="btn btn-secondary" onclick="stubAction('Открыть карточку ${patient.name}')">Карточка</button>
        <button class="btn btn-primary" onclick="openContactModal('${patient.owner}', '${patient.phone}', '${patient.email}')">Связаться</button>
      </div>
    </div>
  `).join('');
}

// Поиск пациентов
function filterPatients() {
  renderPatients();
}

// Переключатель вида
function setPatientsView(view, btn) {
  currentPatientsView = view;
  const container = document.getElementById('patientsList');
  
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  if (view === 'list') {
    container.classList.add('view-list');
  } else {
    container.classList.remove('view-list');
  }
}

// Модальное окно связи
function openContactModal(ownerName, phone, email) {
  document.getElementById('contactOwnerName').textContent = ownerName;
  
  const phoneEl = document.getElementById('contactPhone');
  phoneEl.querySelector('.contact-text').textContent = phone;
  phoneEl.href = `tel:${phone.replace(/\s/g, '').replace(/[()-]/g, '')}`;
  
  const emailEl = document.getElementById('contactEmail');
  emailEl.querySelector('.contact-text').textContent = email;
  emailEl.href = `mailto:${email}`;
  
  document.getElementById('contactModal').classList.add('active');
}

function closeContactModal(event) {
  if (!event || event.target.id === 'contactModal' || event.target.className === 'modal-close') {
    document.getElementById('contactModal').classList.remove('active');
  }
}

// Данные расписания
const scheduleData = [
  {
    id: 1,
    petName: 'Барсик',
    owner: 'Иванова М.П.',
    date: '2026-09-25',
    time: '14:00',
    type: 'appointment',
    description: 'Контрольный осмотр'
  },
  {
    id: 2,
    petName: 'Рекс',
    owner: 'Петров С.И.',
    date: '2026-10-05',
    time: '10:00',
    type: 'vaccination',
    description: 'Комплексная вакцинация'
  },
  {
    id: 3,
    petName: 'Мурка',
    owner: 'Сидорова А.В.',
    date: '2026-10-12',
    time: '16:00',
    type: 'appointment',
    description: 'Послеоперационный осмотр'
  },
  {
    id: 4,
    petName: 'Шарик',
    owner: 'Козлов Д.А.',
    date: '2026-10-18',
    time: '11:00',
    type: 'emergency',
    description: 'Срочный случай'
  }
];

// Состояние календаря
let currentDate = new Date();
let currentScheduleFilter = 'upcoming';

// Рендер календаря
function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  
  document.getElementById('calendarTitle').textContent = `${monthNames[month]} ${year}`;
  
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  
  let startDay = firstDay.getDay() - 1;
  if (startDay < 0) startDay = 6;
  
  const grid = document.getElementById('calendarGrid');
  grid.innerHTML = '';
  
  const today = new Date();
  const todayDate = today.getDate();
  const todayMonth = today.getMonth();
  const todayYear = today.getFullYear();
  
  const prevMonthDays = new Date(year, month, 0).getDate();
  for (let i = startDay - 1; i >= 0; i--) {
    const day = prevMonthDays - i;
    const dayEl = createDayElement(day, true, false, false);
    grid.appendChild(dayEl);
  }
  
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday = (day === todayDate && month === todayMonth && year === todayYear);
    
    const hasAppointment = scheduleData.some(s => {
      const sDate = new Date(s.date);
      return sDate.getDate() === day && sDate.getMonth() === month && sDate.getFullYear() === year;
    });
    
    const dayEl = createDayElement(day, false, isToday, hasAppointment);
    grid.appendChild(dayEl);
  }
  
  const totalCells = startDay + daysInMonth;
  const remainingCells = 42 - totalCells;
  for (let day = 1; day <= remainingCells; day++) {
    const dayEl = createDayElement(day, true, false, false);
    grid.appendChild(dayEl);
  }
}

function createDayElement(day, isOtherMonth, isToday, hasAppointment) {
  const dayEl = document.createElement('div');
  dayEl.className = 'calendar-day';
  dayEl.textContent = day;
  
  if (isOtherMonth) dayEl.classList.add('other-month');
  if (isToday) dayEl.classList.add('today');
  if (hasAppointment) dayEl.classList.add('has-reminder');
  
  return dayEl;
}

function changeMonth(delta) {
  currentDate.setMonth(currentDate.getMonth() + delta);
  renderCalendar();
}

// Рендер расписания
function renderSchedule() {
  const container = document.getElementById('scheduleItems');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  let filtered = scheduleData.filter(item => {
    const sDate = new Date(item.date);
    sDate.setHours(0, 0, 0, 0);
    
    if (currentScheduleFilter === 'upcoming') {
      return sDate >= today;
    }
    return true;
  });
  
  filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
  
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="reminders-empty">
        <div class="reminders-empty-icon">📅</div>
        <p>Нет записей</p>
      </div>
    `;
    return;
  }
  
  const monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 
                      'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  
  container.innerHTML = filtered.map(item => {
    const sDate = new Date(item.date);
    const isToday = sDate.getTime() === today.getTime();
    const isPast = sDate < today;
    
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
          <div class="reminder-date-day">${sDate.getDate()}</div>
          <div class="reminder-date-month">${monthNames[sDate.getMonth()]}</div>
        </div>
        <div class="reminder-info">
          <h4 class="reminder-title">${item.petName} — ${item.owner}</h4>
          <p class="reminder-meta">${item.time} • ${item.description}</p>
        </div>
        <span class="reminder-status ${statusClass}">${statusText}</span>
      </div>
    `;
  }).join('');
}

function filterSchedule(filter, btn) {
  currentScheduleFilter = filter;
  
  document.querySelectorAll('.reminder-filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  renderSchedule();
}