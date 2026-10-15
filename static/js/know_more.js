/* MAHAKAL BUILDCON - About page interactions (vanilla JS) */
document.documentElement.classList.add('js');
const $ = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* Accessible mobile menu */
const burger = $('#burger'), menu = $('#menu');
function setMenu(open) {
  menu.classList.toggle('open', open);
  burger.setAttribute('aria-expanded', open);
  burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
}
burger.addEventListener('click', () => setMenu(!menu.classList.contains('open')));
$$('a', menu).forEach(a => a.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && menu.classList.contains('open')) { setMenu(false); burger.focus(); }
});
addEventListener('resize', () => { if (innerWidth > 820) setMenu(false); });

/* Smooth scroll for in-page links (#expertise, #team ...) */
$$('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
  const id = a.getAttribute('href');
  const target = id.length > 1 && $(id);
  if (!target) return;
  e.preventDefault();
  target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
  history.pushState(null, '', id);
}));

/* Header shadow + back-to-top button */
const nav = $('#nav'), top = $('#top');
function onScroll() {
  nav.classList.toggle('sc', scrollY > 10);
  top.hidden = scrollY < 600;
}
addEventListener('scroll', onScroll, { passive: true });
onScroll();
top.addEventListener('click', () => scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }));

/* Scroll reveal */
const items = $$('.rv');
if (reduce || !('IntersectionObserver' in window)) {
  items.forEach(el => el.classList.add('show'));
} else {
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('show'); io.unobserve(e.target); } });
  }, { threshold: .12 });
  items.forEach((el, i) => { el.style.transitionDelay = (i % 3) * 80 + 'ms'; io.observe(el); });
}