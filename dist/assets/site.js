document.querySelectorAll('[data-showcase]').forEach((showcase) => {
  const tabs = [...showcase.querySelectorAll('[role="tab"]')];
  const panels = [...showcase.querySelectorAll('[role="tabpanel"]')];
  function select(tab) {
    tabs.forEach((item) => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
    });
    panels.forEach((panel) => { panel.hidden = panel.id !== tab.getAttribute('aria-controls'); });
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', (event) => {
      let next;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      select(tabs[next]);
      tabs[next].focus();
    });
  });
  showcase.classList.add('is-enhanced');
  select(tabs[0]);
});

document.querySelectorAll('[data-copy-feedback]').forEach((button) => {
  button.addEventListener('click', async () => {
    const text = document.getElementById('feedback-template').innerText;
    const status = document.getElementById('copy-status');
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = button.dataset.success;
    } catch {
      status.textContent = button.dataset.failure;
    }
  });
});

const navigationMenus = [...document.querySelectorAll('.mobile-nav, .language-picker')];
navigationMenus.forEach((menu) => {
  menu.addEventListener('toggle', () => {
    if (menu.open) navigationMenus.forEach((other) => { if (other !== menu) other.open = false; });
  });
  menu.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
});
document.addEventListener('pointerdown', (event) => {
  navigationMenus.forEach((menu) => { if (!menu.contains(event.target)) menu.open = false; });
});

function updateLanguageLinks() {
  document.querySelectorAll('[data-language-link]').forEach((link) => {
    const destination = new URL(link.href);
    destination.hash = location.hash;
    link.href = destination.href;
  });
}
window.addEventListener('hashchange', updateLanguageLinks);
updateLanguageLinks();

function revealLinkedAnswer() {
  let target;
  try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
  catch { return; }
  if (target instanceof HTMLDetailsElement) target.open = true;
}
window.addEventListener('hashchange', revealLinkedAnswer);
revealLinkedAnswer();
