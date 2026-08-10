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


// NAVBAR SHADOW

const nav = document.querySelector(".nav");

window.addEventListener("scroll", () => {

  if(window.scrollY > 50){

    nav.style.boxShadow = "0 5px 20px rgba(0,0,0,0.4)";

  }else{

    nav.style.boxShadow = "none";

  }

});