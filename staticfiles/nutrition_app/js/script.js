// nutrition_app/static/nutrition_app/js/script.js

document.addEventListener("DOMContentLoaded", function () {
  // Анимация появления элементов
  const animateOnScroll = function () {
    const elements = document.querySelectorAll(".nutri-card, .recipe-card");

    elements.forEach((element) => {
      const elementTop = element.getBoundingClientRect().top;
      const elementVisible = 150;

      if (elementTop < window.innerHeight - elementVisible) {
        element.classList.add("fade-in-up");
      }
    });
  };

  // Проверяем при загрузке и при скролле
  window.addEventListener("scroll", animateOnScroll);
  animateOnScroll();

  // Подсветка активной навигации
  const currentLocation = location.href;
  const menuItems = document.querySelectorAll(".nav-link");

  menuItems.forEach((item) => {
    if (item.href === currentLocation) {
      item.classList.add("active");
    }
  });
});
