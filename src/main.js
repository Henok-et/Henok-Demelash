import './style.css'

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const gsap = window.gsap
const ScrollTrigger = window.ScrollTrigger
const Lenis = window.Lenis

document.addEventListener('DOMContentLoaded', () => {
  if (gsap && ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger)
  }

  const preloader = document.querySelector('.preloader');
  const preloaderText = document.querySelector('.preloader-text');
  
  if (preloader && preloaderText && gsap) {
    const greetings = ["Hello", "Bonjour", "Hola", "Ciao", "Olá", "Hallo", "Привет", "こんにちは", "你好", "ሰላም"];
    let tl = gsap.timeline();
    
    document.body.style.overflow = 'hidden';

    greetings.forEach((greeting, index) => {
      tl.to(preloaderText, {
        duration: 0.15,
        onStart: () => preloaderText.textContent = greeting,
      }, index * 0.18);
    });
    
    tl.to(preloader, {
      yPercent: -100,
      duration: 0.8,
      ease: "power4.inOut",
      delay: 0.2,
      onComplete: () => {
        preloader.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
  }

  let lenis = null

  const scrollToTarget = (target) => {
    if (!target) return
    if (lenis) {
      lenis.scrollTo(target, { offset: 0 })
      return
    }
    target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' })
  }

  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    const hash = link.getAttribute('href')
    if (!hash || hash === '#') return
    link.addEventListener('click', (event) => {
      const target = document.querySelector(hash)
      if (!target) return
      event.preventDefault()
      scrollToTarget(target)
      history.pushState(null, '', hash)
    })
  })

  if (!reduceMotion && typeof Lenis === 'function') {
    lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      smoothWheel: true,
    })

    if (gsap && ScrollTrigger) {
      lenis.on('scroll', ScrollTrigger.update)
      gsap.ticker.add((time) => {
        lenis.raf(time * 1000)
      })
      gsap.ticker.lagSmoothing(0)
    } else {
      const raf = (time) => {
        lenis.raf(time)
        requestAnimationFrame(raf)
      }
      requestAnimationFrame(raf)
    }
  }

  if (window.location.hash) {
    const initial = document.querySelector(window.location.hash)
    if (initial) {
      requestAnimationFrame(() => scrollToTarget(initial))
    }
  }

  if (reduceMotion || !gsap || !ScrollTrigger) return

  document.querySelectorAll('.gs-fade-up').forEach((el) => {
    gsap.fromTo(el,
      { opacity: 0, y: 50 },
      {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: el,
          start: 'clamp(top 90%)',
          toggleActions: 'play none none none',
        },
      }
    )
  })

  const heroCopy = document.querySelectorAll('.hero-section .hero-quote, .hero-section .hero-intro')
  const heroFigure = document.querySelectorAll('.hero-section .hero-portrait, .hero-section .hero-name')
  if (heroCopy.length) {
    gsap.from(heroCopy, {
      opacity: 0,
      y: 20,
      duration: 1.1,
      stagger: 0.12,
      ease: 'power3.out',
      delay: 0.15,
    })
  }
  if (heroFigure.length) {
    gsap.from(heroFigure, {
      opacity: 0,
      duration: 1.25,
      stagger: 0.08,
      ease: 'power3.out',
      delay: 0.1,
    })
  }

  const capStage = document.querySelector('.cap-stage')
  const capPanels = document.querySelectorAll('.cap-panel')
  const capReel = document.querySelector('.cap-reel')
  const setCapIndex = (index) => {
    capPanels.forEach((panel, i) => {
      panel.classList.toggle('is-active', i === index)
    })
    if (capReel && !reduceMotion && gsap) {
      gsap.to(capReel, {
        yPercent: -(index * (100 / capPanels.length)),
        duration: 0.85,
        ease: 'power3.inOut',
        overwrite: 'auto',
      })
    } else if (capReel) {
      capReel.style.transform = `translateY(-${index * (100 / capPanels.length)}%)`
    }
  }

  if (capStage && capPanels.length) {
    if (!reduceMotion && gsap && ScrollTrigger && window.matchMedia('(min-width: 960px)').matches) {
      capPanels.forEach((panel, index) => {
        ScrollTrigger.create({
          trigger: panel,
          start: 'top 58%',
          end: 'bottom 42%',
          onEnter: () => setCapIndex(index),
          onEnterBack: () => setCapIndex(index),
        })
      })
    } else {
      capPanels.forEach((panel) => panel.classList.add('is-active'))
    }
  }

  document.querySelectorAll('.editorial-composition').forEach((comp) => {
    const media = comp.querySelector('.comp-media')
    const texts = comp.querySelectorAll('.gs-comp-text')

    if (media) {
      gsap.fromTo(media,
        { scale: 0.94, yPercent: 5 },
        {
          scale: 1,
          yPercent: 0,
          ease: 'none',
          scrollTrigger: {
            trigger: comp,
            start: 'clamp(top 90%)',
            end: 'center center',
            scrub: true,
          },
        }
      )
    }

    if (texts.length) {
      gsap.fromTo(texts,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: comp,
            start: 'clamp(top 75%)',
            toggleActions: 'play none none none',
          },
        }
      )
    }
  })

  document.querySelectorAll('.case-study-media img').forEach((img) => {
    gsap.fromTo(img,
      { scale: 1.15, yPercent: 10 },
      {
        scale: 1,
        yPercent: -10,
        ease: 'none',
        scrollTrigger: {
          trigger: img.parentElement,
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      }
    )
  })

  const timelineViewport = document.querySelector('.timeline-viewport')
  if (timelineViewport && !reduceMotion) {
    const rows = document.querySelectorAll('.marquee-row')
    
    gsap.fromTo(rows, 
      { opacity: 0, y: 30 },
      {
        opacity: 1,
        y: 0,
        duration: 1,
        stagger: 0.15,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: timelineViewport,
          start: 'clamp(top 85%)',
          toggleActions: 'play none none none',
        }
      }
    )

    rows.forEach((row, index) => {
      const isTop = index === 0;
      
      // Clone items to ensure enough content for scrolling
      const items = Array.from(row.querySelectorAll('.timeline-item'));
      for (let i = 0; i < 2; i++) {
        items.forEach(item => {
          row.appendChild(item.cloneNode(true));
        });
      }

      // Top row starts at 0 and moves left (-25%)
      // Bottom row starts left (-25%) and moves right (to 0)
      if (isTop) {
        gsap.fromTo(row, 
          { xPercent: 0 },
          {
            xPercent: -25,
            ease: 'none',
            scrollTrigger: {
              trigger: ".experiences-section",
              start: "top bottom",
              end: "bottom top",
              scrub: 1.5
            }
          }
        );
      } else {
        gsap.fromTo(row, 
          { xPercent: -25 },
          {
            xPercent: 0,
            ease: 'none',
            scrollTrigger: {
              trigger: ".experiences-section",
              start: "top bottom",
              end: "bottom top",
              scrub: 1.5
            }
          }
        );
      }
    })

    document.querySelectorAll('.timeline-item').forEach((item, index) => {
      gsap.to(item, {
        y: index % 2 === 0 ? -8 : 8,
        duration: 2.5 + (index % 3),
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: 0.5
      })
    })
  }

  document.querySelectorAll('.gs-exp-row').forEach((row) => {
    const imgWrap = row.querySelector('.exp-img-wrap')
    const textEls = row.querySelectorAll('.exp-period, .exp-role, .exp-org, .exp-desc, .exp-tag')

    if (imgWrap) {
      gsap.fromTo(imgWrap,
        { scale: 0.96 },
        {
          scale: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: row,
            start: 'clamp(top 90%)',
            end: 'center center',
            scrub: true,
          },
        }
      )
    }

    if (textEls.length) {
      gsap.fromTo(textEls,
        { opacity: 0, y: 24 },
        {
          opacity: 1,
          y: 0,
          duration: 0.7,
          stagger: 0.08,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: row,
            start: 'clamp(top 80%)',
            toggleActions: 'play none none none',
          },
        }
      )
    }
  })

  // Contact Overlay Logic
  const burgerBtn = document.querySelector('.burger-btn');
  const closeBtn = document.querySelector('.close-btn');
  const contactOverlay = document.querySelector('.contact-overlay');
  const contactElems = document.querySelectorAll('.gs-contact-elem');
  let overlayTl = null;

  if (burgerBtn && closeBtn && contactOverlay && gsap) {
    overlayTl = gsap.timeline({ paused: true });
    
    overlayTl.fromTo(contactOverlay, 
      { yPercent: -100, autoAlpha: 0 },
      { yPercent: 0, autoAlpha: 1, duration: 0.6, ease: "power3.inOut" }
    );
    
    if (contactElems.length) {
      overlayTl.fromTo(contactElems,
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, stagger: 0.1, ease: "power2.out" },
        "-=0.2"
      );
    }

    const openMenu = () => {
      contactOverlay.classList.add('is-active');
      document.body.style.overflow = 'hidden';
      burgerBtn.setAttribute('aria-expanded', 'true');
      overlayTl.timeScale(1).play();
    };

    const closeMenu = () => {
      burgerBtn.setAttribute('aria-expanded', 'false');
      overlayTl.timeScale(1.5).reverse().then(() => {
        contactOverlay.classList.remove('is-active');
        document.body.style.overflow = '';
      });
    };

    burgerBtn.addEventListener('click', openMenu);
    closeBtn.addEventListener('click', closeMenu);
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && contactOverlay.classList.contains('is-active')) {
        closeMenu();
      }
    });

    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
      contactForm.addEventListener('submit', (e) => {
        // Optional: you can add AJAX submission here instead of redirecting
        const btn = contactForm.querySelector('.submit-btn');
        if(btn) {
          btn.textContent = 'Sending...';
        }
      });
    }
  }

  // --- INTERACTIVE SLIDER LOGIC ---
  const sliderContainer = document.querySelector('.work-slider-container');
  const sliderPointer = document.querySelector('.work-slider-pointer');
  const slides = document.querySelectorAll('.work-slide');
  const dots = document.querySelectorAll('.progress-dot');

  if (sliderContainer && sliderPointer && slides.length > 0) {
    let currentSlide = 0;
    const totalSlides = slides.length;

    // Track mouse movement
    sliderContainer.addEventListener('mousemove', (e) => {
      const rect = sliderContainer.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Move pointer
      gsap.to(sliderPointer, {
        x: x,
        y: y,
        duration: 0.1,
        ease: 'power2.out',
      });

      // Check left/right half for cursor state
      if (x < rect.width / 2) {
        sliderContainer.classList.add('cursor-prev');
        sliderContainer.classList.remove('cursor-next');
      } else {
        sliderContainer.classList.add('cursor-next');
        sliderContainer.classList.remove('cursor-prev');
      }
    });

    // Handle clicks
    sliderContainer.addEventListener('click', (e) => {
      const rect = sliderContainer.getBoundingClientRect();
      const x = e.clientX - rect.left;

      if (x < rect.width / 2) {
        // Previous slide
        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
      } else {
        // Next slide
        currentSlide = (currentSlide + 1) % totalSlides;
      }

      // Update active classes
      slides.forEach((slide, index) => {
        slide.classList.toggle('is-active', index === currentSlide);
      });
      if (dots.length > 0) {
        dots.forEach((dot, index) => {
          dot.classList.toggle('is-active', index === currentSlide);
        });
      }
    });
    
    // Hide pointer when leaving
    sliderContainer.addEventListener('mouseleave', () => {
      sliderContainer.classList.remove('cursor-prev', 'cursor-next');
    });
  }

  // --- EVENTS & SPEAKING SECTION (Vertical Parallax) ---
  const eventsSection = document.querySelector('.events-section');
  
  if (eventsSection && !reduceMotion) {
    const floatingImgs = eventsSection.querySelectorAll('.floating-img');

    // Each floating image drifts upward at a different speed as you scroll
    floatingImgs.forEach((img, i) => {
      const speed = 30 + (i % 3) * 25; // Vary parallax speed per image
      const rotation = (i % 2 === 0) ? 2 : -2;

      gsap.fromTo(img,
        { 
          yPercent: speed, 
          opacity: 0,
          rotation: rotation * 2 
        },
        {
          yPercent: -speed * 0.5,
          opacity: 1,
          rotation: 0,
          ease: 'none',
          scrollTrigger: {
            trigger: img.closest('.events-group'),
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1.2,
          },
        }
      );
    });
  }

  // --- FOOTER REVEAL PARALLAX ---
  const footerRevealContainer = document.querySelector('.footer-reveal-container');
  const finalSection = document.querySelector('.final-section');
  if (footerRevealContainer && finalSection && !reduceMotion) {
    gsap.fromTo(finalSection, 
      { yPercent: -50 }, // Footer starts "pulled up" under the previous section
      {
        yPercent: 0,
        ease: "none",
        scrollTrigger: {
          trigger: footerRevealContainer,
          start: "top bottom", // Starts when the top of the container enters the bottom of the viewport
          end: "bottom bottom", // Ends when the bottom of the container reaches the bottom
          scrub: true
        }
      }
    );
  }
})
