document.addEventListener('DOMContentLoaded', () => {
  const passwordToggles = document.querySelectorAll('.password-toggle');

  passwordToggles.forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.closest('.password-wrap')?.querySelector('input');
      if (!input) return;

      const shouldShow = input.type === 'password';
      input.type = shouldShow ? 'text' : 'password';
      button.textContent = shouldShow ? 'Masquer' : 'Afficher';
    });
  });

  function showStatus(status, message, isError) {
    if (!status) return;
    status.textContent = message;
    status.classList.remove('error', 'success');
    status.classList.add('visible', isError ? 'error' : 'success');
  }

  function extractErrorMessage(data, fallback) {
    if (!data || !data.detail) return fallback;
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    return fallback;
  }

  async function postJSON(url, body) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(body),
    });
    let data = null;
    try {
      data = await response.json();
    } catch (err) {
      data = null;
    }
    return { ok: response.ok, data };
  }

  // --- Connexion : POST /login, puis redirection vers /mfa si un 2e facteur est requis ---
  const loginForm = document.querySelector('form[data-form="login"]');
  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = loginForm.querySelector('.form-status');

      const { ok, data } = await postJSON('/login', {
        email: loginForm.email.value.trim(),
        password: loginForm.password.value,
      });

      if (ok && data?.mfa_token) {
        sessionStorage.setItem('mfa_token', data.mfa_token);
        window.location.href = '/mfa';
        return;
      }
      showStatus(status, extractErrorMessage(data, 'Email ou mot de passe incorrect.'), true);
    });
  }

  // --- Inscription : POST /register ---
  const registerForm = document.querySelector('form[data-form="register"]');
  if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = registerForm.querySelector('.form-status');
      const password = registerForm.password.value;

      if (password !== registerForm.confirm_password.value) {
        showStatus(status, 'Les mots de passe ne correspondent pas.', true);
        return;
      }

      const { ok, data } = await postJSON('/register', {
        email: registerForm.email.value.trim(),
        password,
        first_name: registerForm.first_name.value.trim(),
        last_name: registerForm.last_name.value.trim(),
      });

      if (ok) {
        showStatus(status, 'Compte créé. Vérifiez vos emails pour activer votre compte avant de vous connecter.', false);
        registerForm.reset();
        return;
      }
      showStatus(status, extractErrorMessage(data, 'Impossible de créer le compte.'), true);
    });
  }

  // --- MFA : les 6 cases se comportent comme un seul champ, POST /mfa/verify-otp ---
  const mfaForm = document.querySelector('form[data-form="mfa"]');
  if (mfaForm) {
    const otpInputs = Array.from(mfaForm.querySelectorAll('.otp-box input'));

    otpInputs.forEach((input, index) => {
      input.addEventListener('input', () => {
        input.value = input.value.replace(/\D/g, '').slice(0, 1);
        if (input.value && otpInputs[index + 1]) {
          otpInputs[index + 1].focus();
        }
      });
      input.addEventListener('keydown', (event) => {
        if (event.key === 'Backspace' && !input.value && otpInputs[index - 1]) {
          otpInputs[index - 1].focus();
        }
      });
    });

    mfaForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = mfaForm.querySelector('.form-status');
      const mfaToken = sessionStorage.getItem('mfa_token');
      const code = otpInputs.map((input) => input.value).join('');

      if (!mfaToken) {
        showStatus(status, 'Session expirée, reconnectez-vous.', true);
        return;
      }
      if (code.length !== 6) {
        showStatus(status, 'Entrez les 6 chiffres du code.', true);
        return;
      }

      const { ok, data } = await postJSON('/mfa/verify-otp', { mfa_token: mfaToken, code });
      if (ok) {
        sessionStorage.removeItem('mfa_token');
        window.location.href = '/dashboard';
        return;
      }
      showStatus(status, extractErrorMessage(data, 'Code invalide ou expiré.'), true);
    });
  }

  // --- Déclaration : POST /declaration ---
  const declarationForm = document.querySelector('form[data-form="declaration"]');
  if (declarationForm) {
    declarationForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = declarationForm.querySelector('.form-status');

      const { ok, data } = await postJSON('/declaration', {
        fiscal_id: declarationForm.fiscal_id.value.trim(),
        year: declarationForm.year.value,
        income_type: declarationForm.income_type.value,
        amount: parseFloat(declarationForm.amount.value),
        comments: declarationForm.comments.value.trim() || null,
      });

      if (ok) {
        showStatus(status, 'Déclaration enregistrée. Un accusé de réception a été généré.', false);
        declarationForm.reset();
        return;
      }
      showStatus(status, extractErrorMessage(data, 'Impossible d\'enregistrer la déclaration.'), true);
    });
  }

  // --- Demande d'email de réinitialisation : POST /forgot-password ---
  const forgotForm = document.querySelector('form[data-form="forgot"]');
  if (forgotForm) {
    forgotForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = forgotForm.querySelector('.form-status');
      try {
        const { ok, data } = await postJSON('/forgot-password', {
          email: forgotForm.reset_email.value.trim(),
        });
        if (ok) {
          showStatus(status, data?.detail || 'Si un compte correspond à cette adresse, un email lui a été envoyé.', false);
          forgotForm.reset();
          return;
        }
        showStatus(status, extractErrorMessage(data, 'Impossible de traiter la demande.'), true);
      } catch (err) {
        showStatus(status, 'Service momentanément indisponible. Réessayez plus tard.', true);
      }
    });
  }

  // --- Confirmation du nouveau mot de passe : POST /reset-password/{token} ---
  const resetForm = document.querySelector('form[data-form="reset-password"]');
  if (resetForm) {
    resetForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = resetForm.querySelector('.form-status');
      const password = resetForm.new_password.value;
      if (password !== resetForm.confirm_new_password.value) {
        showStatus(status, 'Les mots de passe ne correspondent pas.', true);
        return;
      }

      try {
        const token = resetForm.dataset.token;
        const { ok, data } = await postJSON(`/reset-password/${encodeURIComponent(token)}`, { password });
        if (ok) {
          showStatus(status, data?.detail || 'Mot de passe modifié. Vous pouvez maintenant vous connecter.', false);
          resetForm.reset();
          return;
        }
        showStatus(status, extractErrorMessage(data, 'Impossible de modifier le mot de passe.'), true);
      } catch (err) {
        showStatus(status, 'Service momentanément indisponible. Réessayez plus tard.', true);
      }
    });
  }

  // --- Déconnexion ---
  const logoutButton = document.querySelector('[data-action="logout"]');
  if (logoutButton) {
    logoutButton.addEventListener('click', async () => {
      await fetch('/logout', { method: 'POST', credentials: 'same-origin' });
      window.location.href = '/home';
    });
  }

  const yearTag = document.getElementById('footer-year');
  if (yearTag) {
    yearTag.textContent = new Date().getFullYear();
  }
});