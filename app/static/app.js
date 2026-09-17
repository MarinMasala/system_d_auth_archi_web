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

  const forms = document.querySelectorAll('form[data-form]');

  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();

      const status = form.querySelector('.form-status');
      if (!status) return;

      const formName = form.dataset.form;
      const messageMap = {
        login: 'Connexion réussie. Vous pouvez accéder à votre espace personnel.',
        register: 'Compte créé avec succès. Vous pouvez maintenant vous connecter.',
        declaration: 'Déclaration enregistrée. Un accusé de réception a été généré.',
        mfa: 'Code de validation vérifié. Votre session est confirmée.',
        forgot: 'Demande reçue. Un email de réinitialisation a été envoyé.'
      };

      const text = messageMap[formName] || 'Formulaire soumis avec succès.';

      status.textContent = text;
      status.classList.remove('error');
      status.classList.add('visible', 'success');
      form.reset();
    });
  });

  const yearTag = document.getElementById('year');
  if (yearTag) {
    yearTag.textContent = new Date().getFullYear();
  }
});
