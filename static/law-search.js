  function navbar() {
  const burger = document.querySelector('.menu');
  const nav = document.querySelector('.nav-link');

  burger.addEventListener('click', () => {
    nav.classList.toggle('nav-active');
  });
}
navbar();