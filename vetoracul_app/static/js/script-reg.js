// ===== ПЕРЕКЛЮЧЕНИЕ ВИДИМОСТИ ПАРОЛЯ =====
function togglePassword(inputId, button) {
  const input = document.getElementById(inputId);
  const eyeIcon = button.querySelector('.eye-icon');
  
  if (input.type === 'password') {
    input.type = 'text';
    eyeIcon.textContent = '🙈';
  } else {
    input.type = 'password';
    eyeIcon.textContent = '👁️';
  }
}

// ===== ПРОВЕРКА СЛОЖНОСТИ ПАРОЛЯ =====
const passwordInput = document.getElementById('password');
const strengthIndicator = document.getElementById('passwordStrength');

passwordInput.addEventListener('input', function() {
  const password = this.value;
  let strength = 0;
  
  if (password.length >= 8) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;
  
  strengthIndicator.className = 'password-strength';
  
  if (password.length === 0) {
    // ничего не показываем
  } else if (strength <= 1) {
    strengthIndicator.classList.add('weak');
  } else if (strength === 2) {
    strengthIndicator.classList.add('medium');
  } else if (strength === 3) {
    strengthIndicator.classList.add('strong');
  } else {
    strengthIndicator.classList.add('very-strong');
  }
  
  checkPasswordMatch();
});

// ===== ПРОВЕРКА СОВПАДЕНИЯ ПАРОЛЕЙ =====
const confirmPasswordInput = document.getElementById('confirmPassword');
const passwordMatchHint = document.getElementById('passwordMatch');

confirmPasswordInput.addEventListener('input', checkPasswordMatch);

function checkPasswordMatch() {
  const password = passwordInput.value;
  const confirmPassword = confirmPasswordInput.value;
  
  if (confirmPassword.length === 0) {
    passwordMatchHint.textContent = '';
    confirmPasswordInput.classList.remove('error', 'success');
    return;
  }
  
  if (password === confirmPassword) {
    passwordMatchHint.textContent = '✓ Пароли совпадают';
    passwordMatchHint.className = 'form-hint success';
    confirmPasswordInput.classList.remove('error');
    confirmPasswordInput.classList.add('success');
  } else {
    passwordMatchHint.textContent = '✗ Пароли не совпадают';
    passwordMatchHint.className = 'form-hint error';
    confirmPasswordInput.classList.remove('success');
    confirmPasswordInput.classList.add('error');
  }
}

// ===== ОБРАБОТКА ОТПРАВКИ ФОРМЫ =====
function handleRegistration(event) {
  event.preventDefault();
  
  const password = passwordInput.value;
  const confirmPassword = confirmPasswordInput.value;
  
  if (password !== confirmPassword) {
    alert('Пароли не совпадают!');
    return;
  }
  
  if (password.length < 8) {
    alert('Пароль должен содержать минимум 8 символов!');
    return;
  }
  
  const formData = {
    firstName: document.getElementById('firstName').value,
    lastName: document.getElementById('lastName').value,
    email: document.getElementById('email').value,
    phone: document.getElementById('phone').value,
    password: password
  };
  
  console.log('Данные регистрации:', formData);
  
  alert(`✅ Регистрация успешна!\n\nДобро пожаловать, ${formData.firstName} ${formData.lastName}!\n\nНа email ${formData.email} отправлено письмо с подтверждением.`);
}

// ===== МАСКА ДЛЯ ТЕЛЕФОНА =====
const phoneInput = document.getElementById('phone');

phoneInput.addEventListener('input', function(e) {
  let value = e.target.value.replace(/\D/g, '');
  
  if (value.length > 0) {
    if (value[0] === '7' || value[0] === '8') {
      value = value.substring(1);
    }
    
    let formatted = '+7';
    
    if (value.length > 0) {
      formatted += ' (' + value.substring(0, 3);
    }
    if (value.length >= 3) {
      formatted += ') ' + value.substring(3, 6);
    }
    if (value.length >= 6) {
      formatted += '-' + value.substring(6, 8);
    }
    if (value.length >= 8) {
      formatted += '-' + value.substring(8, 10);
    }
    
    e.target.value = formatted;
  }
});