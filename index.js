// REVEAL ANIMATION

const reveals = document.querySelectorAll(".reveal");

const observer = new IntersectionObserver(entries => {

  entries.forEach(entry => {

    if(entry.isIntersecting){
      entry.target.classList.add("active");
    }

  });

},{
  threshold:0.2
});

reveals.forEach(el => {
  observer.observe(el);
});


// CONTACT FORM

const form = document.getElementById("contactForm");
const success = document.getElementById("formSuccess");

form.addEventListener("submit", function(e){

  e.preventDefault();

  success.style.display = "block";

  form.reset();

});


// NAVBAR SHADOW

const navbar = document.getElementById("navbar");

window.addEventListener("scroll", () => {

  if(window.scrollY > 50){

    navbar.style.boxShadow = "0 5px 20px rgba(0,0,0,0.4)";

  }else{

    navbar.style.boxShadow = "none";

  }

});