document.addEventListener('DOMContentLoaded', () => {
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

  window.switchPage = function(pageId) {
    menuItems.forEach(mi => {
      mi.classList.remove('active');
      if (mi.getAttribute('data-page') === pageId) mi.classList.add('active');
    });
    pages.forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    document.getElementById('userPanel').classList.remove('active');
    document.getElementById('notificationsPanel').classList.remove('active');
  };

  document.addEventListener('click', (event) => {
    const userPanel = document.getElementById('userPanel');
    const avatarWrapper = document.querySelector('.user-avatar-wrapper');
    const notificationsPanel = document.getElementById('notificationsPanel');
    const notificationsWrapper = document.querySelector('.notifications-wrapper');
    
    if (userPanel && userPanel.classList.contains('active')) {
      if (!avatarWrapper.contains(event.target)) userPanel.classList.remove('active');
    }
    if (notificationsPanel && notificationsPanel.classList.contains('active')) {
      if (!notificationsWrapper.contains(event.target)) notificationsPanel.classList.remove('active');
    }
  });

  renderStaff();
  renderUsers();
  renderPets();
  renderCalendar();
  renderSchedule();
});

function toggleUserPanel() {
  document.getElementById('userPanel').classList.toggle('active');
  document.getElementById('notificationsPanel').classList.remove('active');
}

function toggleNotifications() {
  document.getElementById('notificationsPanel').classList.toggle('active');
  document.getElementById('userPanel').classList.remove('active');
}

function stubAction(actionName) {
  console.log(`[Заглушка] ${actionName}`);
  alert(`️ Функция "${actionName}" находится в разработке.`);
}

// ===== ПЕРСОНАЛ =====
let staffData = [
  { id: 1, firstName: 'Алексей', lastName: 'Борисов', middleName: 'Иванович', role: 'doctor', specialty: 'Терапевт', phone: '+7 (999) 123-45-67', email: 'borisov@vetoracul.ru', status: 'active' },
  { id: 2, firstName: 'Елена', lastName: 'Смирнова', middleName: 'Петровна', role: 'doctor', specialty: 'Хирург', phone: '+7 (999) 234-56-78', email: 'smirnova@vetoracul.ru', status: 'active' },
  { id: 3, firstName: 'Дмитрий', lastName: 'Козлов', middleName: 'Александрович', role: 'doctor', specialty: 'Кардиолог', phone: '+7 (999) 345-67-89', email: 'kozlov@vetoracul.ru', status: 'inactive' },
  { id: 4, firstName: 'Анна', lastName: 'Петрова', middleName: 'Сергеевна', role: 'admin', specialty: '', phone: '+7 (999) 456-78-90', email: 'petrova@vetoracul.ru', status: 'active' },
  { id: 5, firstName: 'Иван', lastName: 'Сидоров', middleName: 'Петрович', role: 'doctor', specialty: 'Дерматолог', phone: '+7 (999) 567-89-01', email: 'sidorov@vetoracul.ru', status: 'blocked' }
];

let currentStaffFilter = 'all';

function renderStaff() {
  const container = document.getElementById('staffList');
  const emptyState = document.getElementById('staffEmpty');
  const searchQuery = document.getElementById('staffSearchInput').value.toLowerCase();
  
  const filtered = staffData.filter(staff => {
    const fullName = `${staff.lastName} ${staff.firstName} ${staff.middleName}`.toLowerCase();
    const matchSearch = fullName.includes(searchQuery) || staff.specialty.toLowerCase().includes(searchQuery);
    const matchFilter = currentStaffFilter === 'all' || staff.role === currentStaffFilter;
    return matchSearch && matchFilter;
  });

  if (filtered.length === 0) {
    container.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'grid';
  emptyState.style.display = 'none';

  container.innerHTML = filtered.map(staff => {
    const initials = `${staff.lastName[0]}${staff.firstName[0]}`;
    const fullName = `${staff.lastName} ${staff.firstName} ${staff.middleName}`;
    const roleLabel = staff.role === 'doctor' ? 'Врач' : 'Администратор';
    const roleClass = staff.role === 'doctor' ? 'staff-role--doctor' : 'staff-role--admin';
    
    let statusClass = 'status-active';
    let statusLabel = 'Активен';
    if (staff.status === 'inactive') { statusClass = 'status-inactive'; statusLabel = 'Неактивен'; }
    if (staff.status === 'blocked') { statusClass = 'status-blocked'; statusLabel = 'Заблокирован'; }
    
    return `
      <div class="staff-card">
        <div class="staff-card__header">
          <div class="staff-card__avatar">
            <span class="staff-card__initials">${initials}</span>
          </div>
          <div class="staff-card__info">
            <h3 class="staff-card__name">${fullName}</h3>
            <div class="staff-card__meta">
              <span class="staff-role ${roleClass}">${roleLabel}</span>
              ${staff.specialty ? `<span class="staff-specialty">${staff.specialty}</span>` : ''}
            </div>
          </div>
          <span class="staff-card__status ${statusClass}">${statusLabel}</span>
        </div>

        <div class="staff-card__body">
          <div class="staff-info-row">
            <span class="staff-info-label">📱 Телефон:</span>
            <a href="tel:${staff.phone.replace(/\s/g, '')}" class="staff-info-link">${staff.phone}</a>
          </div>
          <div class="staff-info-row">
            <span class="staff-info-label">✉️ Email:</span>
            <a href="mailto:${staff.email}" class="staff-info-link">${staff.email}</a>
          </div>
        </div>

        <div class="staff-card__footer">
          <button class="btn btn-secondary" onclick="editStaff(${staff.id})">✏️ Редактировать</button>
          ${staff.status !== 'blocked' 
            ? `<button class="btn btn-warning" onclick="blockStaff(${staff.id})">🔒 Заблокировать</button>`
            : `<button class="btn btn-primary" onclick="unblockStaff(${staff.id})">🔓 Разблокировать</button>`
          }
        </div>
      </div>
    `;
  }).join('');
}

function filterStaff() { renderStaff(); }

function setStaffFilter(filter, btn) {
  currentStaffFilter = filter;
  document.querySelectorAll('#staff .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderStaff();
}

function openAddStaffModal() {
  document.getElementById('staffModalTitle').textContent = 'Добавить сотрудника';
  document.getElementById('staffForm').reset();
  document.getElementById('staffId').value = '';
  document.getElementById('staffModal').classList.add('active');
}

function editStaff(id) {
  const staff = staffData.find(s => s.id === id);
  if (!staff) return;
  
  document.getElementById('staffModalTitle').textContent = 'Редактировать сотрудника';
  document.getElementById('staffId').value = staff.id;
  document.getElementById('staffFirstName').value = staff.firstName;
  document.getElementById('staffLastName').value = staff.lastName;
  document.getElementById('staffMiddleName').value = staff.middleName;
  document.getElementById('staffRole').value = staff.role;
  document.getElementById('staffSpecialty').value = staff.specialty;
  document.getElementById('staffPhone').value = staff.phone;
  document.getElementById('staffEmail').value = staff.email;
  document.getElementById('staffStatus').value = staff.status;
  
  document.getElementById('staffModal').classList.add('active');
}

function blockStaff(id) {
  const staff = staffData.find(s => s.id === id);
  if (!staff) return;
  const fullName = `${staff.lastName} ${staff.firstName} ${staff.middleName}`;
  
  if (confirm(`Заблокировать сотрудника "${fullName}"?\n\nСотрудник не сможет войти в систему.`)) {
    staff.status = 'blocked';
    renderStaff();
    alert(`🔒 Сотрудник "${fullName}" заблокирован.`);
  }
}

function unblockStaff(id) {
  const staff = staffData.find(s => s.id === id);
  if (!staff) return;
  const fullName = `${staff.lastName} ${staff.firstName} ${staff.middleName}`;
  
  if (confirm(`Разблокировать сотрудника "${fullName}"?`)) {
    staff.status = 'active';
    renderStaff();
    alert(`🔓 Сотрудник "${fullName}" разблокирован.`);
  }
}

function handleStaffSubmit(event) {
  event.preventDefault();
  
  const id = document.getElementById('staffId').value;
  const newStaff = {
    id: id ? parseInt(id) : Date.now(),
    firstName: document.getElementById('staffFirstName').value,
    lastName: document.getElementById('staffLastName').value,
    middleName: document.getElementById('staffMiddleName').value,
    role: document.getElementById('staffRole').value,
    specialty: document.getElementById('staffSpecialty').value,
    phone: document.getElementById('staffPhone').value,
    email: document.getElementById('staffEmail').value,
    status: document.getElementById('staffStatus').value
  };
  
  if (id) {
    const index = staffData.findIndex(s => s.id === parseInt(id));
    if (index !== -1) staffData[index] = newStaff;
    alert(`✅ Данные сотрудника обновлены.`);
  } else {
    staffData.push(newStaff);
    alert(`✅ Сотрудник добавлен.`);
  }
  
  closeStaffModal();
  renderStaff();
}

function closeStaffModal(event) {
  if (!event || event.target.id === 'staffModal' || event.target.className === 'modal-close') {
    document.getElementById('staffModal').classList.remove('active');
  }
}

// ===== ПОЛЬЗОВАТЕЛИ =====
let usersData = [
  { id: 1, firstName: 'Мария', lastName: 'Иванова', email: 'maria.ivanova@mail.ru', phone: '+7 (999) 123-45-67', pets: 1, status: 'active', registered: '15.03.2026' },
  { id: 2, firstName: 'Сергей', lastName: 'Петров', email: 'petrov.s@mail.ru', phone: '+7 (999) 234-56-78', pets: 1, status: 'active', registered: '20.04.2026' },
  { id: 3, firstName: 'Анна', lastName: 'Сидорова', email: 'sidorova.a@mail.ru', phone: '+7 (999) 345-67-89', pets: 1, status: 'active', registered: '10.05.2026' },
  { id: 4, firstName: 'Дмитрий', lastName: 'Козлов', email: 'kozlov.d@mail.ru', phone: '+7 (999) 456-78-90', pets: 1, status: 'blocked', registered: '05.06.2026' },
  { id: 5, firstName: 'Ольга', lastName: 'Новикова', email: 'novikova.o@mail.ru', phone: '+7 (999) 567-89-01', pets: 1, status: 'active', registered: '12.07.2026' }
];

let currentUsersFilter = 'all';

function renderUsers() {
  const container = document.getElementById('usersList');
  const emptyState = document.getElementById('usersEmpty');
  const searchQuery = document.getElementById('usersSearchInput').value.toLowerCase();
  
  const filtered = usersData.filter(user => {
    const fullName = `${user.lastName} ${user.firstName}`.toLowerCase();
    const matchSearch = fullName.includes(searchQuery) || user.email.toLowerCase().includes(searchQuery);
    const matchFilter = currentUsersFilter === 'all' || user.status === currentUsersFilter;
    return matchSearch && matchFilter;
  });

  if (filtered.length === 0) {
    container.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'grid';
  emptyState.style.display = 'none';

  container.innerHTML = filtered.map(user => {
    const initials = `${user.lastName[0]}${user.firstName[0]}`;
    const fullName = `${user.lastName} ${user.firstName}`;
    
    let statusClass = 'status-active';
    let statusLabel = 'Активен';
    if (user.status === 'blocked') { statusClass = 'status-blocked'; statusLabel = 'Заблокирован'; }
    
    return `
      <div class="user-card">
        <div class="user-card__header">
          <div class="user-card__avatar">
            <span class="user-card__initials">${initials}</span>
          </div>
          <div class="user-card__info">
            <h3 class="user-card__name">${fullName}</h3>
            <div class="user-card__meta">
              <span class="user-pets">🐾 Питомцев: ${user.pets}</span>
              <span class="user-registered"> ${user.registered}</span>
            </div>
          </div>
          <span class="user-card__status ${statusClass}">${statusLabel}</span>
        </div>

        <div class="user-card__body">
          <div class="user-info-row">
            <span class="user-info-label">✉️ Email:</span>
            <a href="mailto:${user.email}" class="user-info-link">${user.email}</a>
          </div>
          <div class="user-info-row">
            <span class="user-info-label">📱 Телефон:</span>
            <a href="tel:${user.phone.replace(/\s/g, '')}" class="user-info-link">${user.phone}</a>
          </div>
        </div>

        <div class="user-card__footer">
          ${user.status !== 'blocked' 
            ? `<button class="btn btn-warning" onclick="blockUser(${user.id})">🔒 Заблокировать</button>`
            : `<button class="btn btn-primary" onclick="unblockUser(${user.id})">🔓 Разблокировать</button>`
          }
        </div>
      </div>
    `;
  }).join('');
}

function filterUsers() { renderUsers(); }

function setUsersFilter(filter, btn) {
  currentUsersFilter = filter;
  document.querySelectorAll('#users .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderUsers();
}

function blockUser(id) {
  const user = usersData.find(u => u.id === id);
  if (!user) return;
  const fullName = `${user.lastName} ${user.firstName}`;
  
  if (confirm(`Заблокировать пользователя "${fullName}"?\n\nПользователь не сможет войти в систему.`)) {
    user.status = 'blocked';
    renderUsers();
    alert(`🔒 Пользователь "${fullName}" заблокирован.`);
  }
}

function unblockUser(id) {
  const user = usersData.find(u => u.id === id);
  if (!user) return;
  const fullName = `${user.lastName} ${user.firstName}`;
  
  if (confirm(`Разблокировать пользователя "${fullName}"?`)) {
    user.status = 'active';
    renderUsers();
    alert(` Пользователь "${fullName}" разблокирован.`);
  }
}

// ===== ПОИСК ПИТОМЦЕВ =====
let petsData = [
  { id: 1, name: 'Барсик', type: 'cat', breed: 'Британская', age: '6 лет', owner: 'Иванова Мария Петровна', ownerId: 1, phone: '+7 (999) 123-45-67', diagnosis: 'Аллергический дерматит', letter: 'Б', color: 'pet-mini-avatar--blue' },
  { id: 2, name: 'Рекс', type: 'dog', breed: 'Немецкая овчарка', age: '3 года', owner: 'Петров Сергей Иванович', ownerId: 2, phone: '+7 (999) 234-56-78', diagnosis: 'Здоров', letter: 'Р', color: 'pet-mini-avatar--purple' },
  { id: 3, name: 'Мурка', type: 'cat', breed: 'Домашняя', age: '2 года', owner: 'Сидорова Анна Владимировна', ownerId: 3, phone: '+7 (999) 345-67-89', diagnosis: 'Стерилизация', letter: 'М', color: 'pet-mini-avatar--blue' },
  { id: 4, name: 'Шарик', type: 'dog', breed: 'Дворняжка', age: '4 года', owner: 'Козлов Дмитрий Алексеевич', ownerId: 4, phone: '+7 (999) 456-78-90', diagnosis: 'Отравление', letter: 'Ш', color: 'pet-mini-avatar--purple' },
  { id: 5, name: 'Кеша', type: 'other', breed: 'Волнистый попугай', age: '1 год', owner: 'Новикова Ольга Сергеевна', ownerId: 5, phone: '+7 (999) 567-89-01', diagnosis: 'Здоров', letter: 'К', color: 'pet-mini-avatar--blue' },
  { id: 6, name: 'Бобик', type: 'dog', breed: 'Лабрадор', age: '5 лет', owner: 'Морозов Иван Петрович', ownerId: 6, phone: '+7 (999) 678-90-12', diagnosis: 'Хромота', letter: 'Б', color: 'pet-mini-avatar--purple' }
];

let currentPetsFilter = 'all';

function renderPets() {
  const container = document.getElementById('petsList');
  const emptyState = document.getElementById('petsEmpty');
  const searchQuery = document.getElementById('petsSearchInput').value.toLowerCase();
  
  const filtered = petsData.filter(pet => {
    const matchSearch = pet.name.toLowerCase().includes(searchQuery) ||
                       pet.breed.toLowerCase().includes(searchQuery) ||
                       pet.owner.toLowerCase().includes(searchQuery) ||
                       pet.diagnosis.toLowerCase().includes(searchQuery);
    const matchFilter = currentPetsFilter === 'all' || pet.type === currentPetsFilter;
    return matchSearch && matchFilter;
  });

  if (filtered.length === 0) {
    container.style.display = 'none';
    emptyState.style.display = 'block';
    return;
  }

  container.style.display = 'grid';
  emptyState.style.display = 'none';

  container.innerHTML = filtered.map(pet => `
    <div class="pet-card">
      <div class="pet-card__header">
        <div class="pet-card__avatar pet-card__avatar--letter">
          <div class="pet-mini-avatar ${pet.color}">
            <span class="pet-mini-letter">${pet.letter}</span>
          </div>
        </div>
        <div class="pet-card__info">
          <h3 class="pet-card__name">${pet.name}</h3>
          <p class="pet-card__breed">${pet.breed} • ${pet.age}</p>
        </div>
        <span class="pet-card__status status-active">Активен</span>
      </div>

      <div class="pet-card__body">
        <div class="pet-card__section">
          <h4 class="section-title">👤 Владелец</h4>
          <div class="info-row info-row--compact">
            <span class="info-label">ФИО:</span>
            <span class="info-value">${pet.owner}</span>
          </div>
          <div class="info-row info-row--compact">
            <span class="info-label">Телефон:</span>
            <a href="tel:${pet.phone.replace(/\s/g, '')}" class="info-value" style="color: var(--color-accent); text-decoration: none;">${pet.phone}</a>
          </div>
        </div>

        <div class="pet-card__section">
          <h4 class="section-title">🩺 Диагноз</h4>
          <div class="info-item" style="width: 100%;">
            <span class="info-label">Текущий статус</span>
            <span class="info-value highlight">${pet.diagnosis}</span>
          </div>
        </div>
      </div>

      <div class="pet-card__footer">
        <button class="btn btn-secondary" onclick="stubAction('Открыть карточку ${pet.name}')">Карточка</button>
        <button class="btn btn-danger" onclick="deletePet(${pet.id})">🗑️ Удалить</button>
      </div>
    </div>
  `).join('');
}

function filterPets() { renderPets(); }

function setPetsFilter(filter, btn) {
  currentPetsFilter = filter;
  document.querySelectorAll('#pets-search .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderPets();
}

function deletePet(id) {
  const pet = petsData.find(p => p.id === id);
  if (!pet) return;
  
  if (confirm(`Удалить питомца "${pet.name}"?\n\nЭто действие необратимо. Все данные питомца будут удалены.`)) {
    petsData = petsData.filter(p => p.id !== id);
    renderPets();
    alert(`🗑️ Питомец "${pet.name}" удалён.`);
  }
}

// ===== РАСПИСАНИЕ =====
const scheduleData = [
  { id: 1, petName: 'Барсик', owner: 'Иванова М.П.', doctor: 'Борисов А.И.', date: '2026-09-25', time: '14:00', type: 'appointment', description: 'Контрольный осмотр' },
  { id: 2, petName: 'Рекс', owner: 'Петров С.И.', doctor: 'Смирнова Е.П.', date: '2026-10-05', time: '10:00', type: 'vaccination', description: 'Комплексная вакцинация' },
  { id: 3, petName: 'Мурка', owner: 'Сидорова А.В.', doctor: 'Борисов А.И.', date: '2026-10-12', time: '16:00', type: 'appointment', description: 'Послеоперационный осмотр' },
  { id: 4, petName: 'Шарик', owner: 'Козлов Д.А.', doctor: 'Козлов Д.А.', date: '2026-10-18', time: '11:00', type: 'emergency', description: 'Срочный случай' },
  { id: 5, petName: 'Бобик', owner: 'Морозов И.П.', doctor: 'Смирнова Е.П.', date: '2026-10-22', time: '15:00', type: 'appointment', description: 'Хромота передней лапы' }
];

let currentDate = new Date();
let currentScheduleFilter = 'upcoming';

function renderCalendar() {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
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
    grid.appendChild(createDayElement(prevMonthDays - i, true, false, false));
  }
  
  for (let day = 1; day <= daysInMonth; day++) {
    const isToday = (day === todayDate && month === todayMonth && year === todayYear);
    const hasAppointment = scheduleData.some(s => {
      const sDate = new Date(s.date);
      return sDate.getDate() === day && sDate.getMonth() === month && sDate.getFullYear() === year;
    });
    grid.appendChild(createDayElement(day, false, isToday, hasAppointment));
  }
  
  const totalCells = startDay + daysInMonth;
  const remainingCells = 42 - totalCells;
  for (let day = 1; day <= remainingCells; day++) {
    grid.appendChild(createDayElement(day, true, false, false));
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

function renderSchedule() {
  const container = document.getElementById('scheduleItems');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  let filtered = scheduleData.filter(item => {
    const sDate = new Date(item.date);
    sDate.setHours(0, 0, 0, 0);
    if (currentScheduleFilter === 'upcoming') return sDate >= today;
    return true;
  });
  
  filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
  
  if (filtered.length === 0) {
    container.innerHTML = `<div class="reminders-empty"><div class="reminders-empty-icon">📅</div><p>Нет записей</p></div>`;
    return;
  }
  
  const monthNames = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  
  container.innerHTML = filtered.map(item => {
    const sDate = new Date(item.date);
    const isToday = sDate.getTime() === today.getTime();
    const isPast = sDate < today;
    
    let statusClass = 'reminder-status--upcoming';
    let statusText = 'Предстоит';
    if (isToday) { statusClass = 'reminder-status--today'; statusText = 'Сегодня'; }
    else if (isPast) { statusClass = 'reminder-status--past'; statusText = 'Прошло'; }
    
    return `
      <div class="reminder-card">
        <div class="reminder-date-box">
          <div class="reminder-date-day">${sDate.getDate()}</div>
          <div class="reminder-date-month">${monthNames[sDate.getMonth()]}</div>
        </div>
        <div class="reminder-info">
          <h4 class="reminder-title">${item.petName} — ${item.owner}</h4>
          <p class="reminder-meta">${item.time} • ${item.doctor} • ${item.description}</p>
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