/* MAHAKAL BUILDCON - frontend interactions (vanilla JS) */
document.documentElement.classList.add('js');

const $ = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];

/* Mobile menu */
const burger = $('#burger'), menu = $('#menu');
const closeMenu = () => { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); };
burger.addEventListener('click', () => {
  const open = menu.classList.toggle('open');
  burger.setAttribute('aria-expanded', open);
});
$$('a', menu).forEach(a => a.addEventListener('click', closeMenu));
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeMenu(); closeLb(); } });

/* Navbar shadow on scroll */
const nav = $('#nav');
addEventListener('scroll', () => nav.classList.toggle('sc', scrollY > 10), { passive: true });

/* Active nav link */
const links = $$('.menu a:not(.btn)');
const secs = links.map(a => $(a.getAttribute('href'))).filter(Boolean);
const spy = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) links.forEach(a => a.classList.toggle('act', a.getAttribute('href') === '#' + e.target.id));
  });
}, { rootMargin: '-45% 0px -50% 0px' });
secs.forEach(s => spy.observe(s));

/* Scroll reveal */
const rv = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('show'); rv.unobserve(e.target); } });
}, { threshold: .12 });
$$('.rv').forEach((el, i) => { el.style.transitionDelay = (i % 3) * 80 + 'ms'; rv.observe(el); });

/* Gallery filter */
const chips = $$('.chip'), figs = $$('.ggrid figure');
chips.forEach(c => c.addEventListener('click', () => {
  chips.forEach(x => x.classList.toggle('on', x === c));
  figs.forEach(f => f.hidden = c.dataset.f !== 'all' && f.dataset.c !== c.dataset.f);
}));

/* Gallery lightbox */
const lb = $('#lb'), lbImg = $('img', lb);
function closeLb() { lb.hidden = true; }
figs.forEach(f => {
  f.tabIndex = 0;
  const open = () => { const i = $('img', f); lbImg.src = i.src; lbImg.alt = i.alt; lb.hidden = false; };
  f.addEventListener('click', open);
  f.addEventListener('keydown', e => { if (e.key === 'Enter') open(); });
});
lb.addEventListener('click', e => { if (e.target !== lbImg) closeLb(); });

/* Enquiry form validation (frontend only - no data is sent anywhere) */
const form = $('#form'), ok = $('#ok');
const rules = {
  name: v => v.trim().length >= 2 || 'Please enter your name.',
  phone: v => /^[+]?[0-9\s-]{10,15}$/.test(v.trim()) || 'Enter a valid phone number (10-15 digits).',
  email: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) || 'Enter a valid email address.',
  type: v => v !== '' || 'Please select a project type.',
  msg: v => v.trim().length >= 10 || 'Please write at least 10 characters.'
};
function check(field) {
  const rule = rules[field.name]; if (!rule) return true;
  const res = rule(field.value);
  const bad = res !== true;
  field.classList.toggle('bad', bad);
  field.setAttribute('aria-invalid', bad);
  field.parentElement.querySelector('em').textContent = bad ? res : '';
  return !bad;
}
$$('input,select,textarea', form).forEach(f => f.addEventListener('blur', () => check(f)));
form.addEventListener('submit', e => {
  e.preventDefault();
  const valid = $$('input,select,textarea', form).map(check).every(Boolean);
  if (!valid) { $('.bad', form).focus(); return; }
  fetch(form.action, { method: 'POST', body: new FormData(form) })
    .then(r => { if (!r.ok) throw new Error(); form.reset(); ok.textContent = 'Thank you! Your enquiry is noted. We will contact you soon.'; })
    .catch(() => { ok.textContent = 'Sorry, something went wrong. Please call us directly.'; })
    .finally(() => { ok.hidden = false; setTimeout(() => ok.hidden = true, 7000); });
});