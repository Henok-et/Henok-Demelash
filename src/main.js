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
  const hasLoadedBefore = sessionStorage.getItem('siteLoaded');
  
  if (preloader && preloaderText && gsap && !hasLoadedBefore) {
    // Mark session as loaded immediately so it never replays
    sessionStorage.setItem('siteLoaded', 'true');

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

        const newsModal = document.querySelector('.news-modal');
        const newsBox = document.querySelector('.news-modal-box');

        if (newsModal && newsBox) {
          gsap.set(newsModal, { visibility: 'visible' });

          let newsTl = gsap.timeline();
          newsTl.to(newsModal, { opacity: 1, duration: 0.5, ease: "power2.out" })
                .fromTo(newsBox, { scale: 0.9, y: 30, opacity: 0 }, { scale: 1, y: 0, opacity: 1, duration: 0.7, ease: "back.out(1.5)" }, "-=0.2");

          const closeBtn = document.querySelector('.news-close');
          if (closeBtn) {
            closeBtn.addEventListener('click', () => {
              gsap.to(newsBox, { scale: 0.9, y: 20, opacity: 0, duration: 0.4, ease: "power2.in" });
              gsap.to(newsModal, { opacity: 0, duration: 0.4, delay: 0.2, onComplete: () => {
                newsModal.style.display = 'none';
                document.body.style.overflow = '';
              }});
            });
          }
        } else {
          document.body.style.overflow = '';
        }
      }
    });
  } else if (preloader) {
    // Already loaded before in this session — skip everything instantly
    preloader.style.display = 'none';
    const newsModal = document.querySelector('.news-modal');
    if (newsModal) newsModal.style.display = 'none';
    document.body.style.overflow = '';
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

  const isExperiencePage = Boolean(document.querySelector('.page-header-spacing'))

  document.querySelectorAll(isExperiencePage ? '.gs-fade-up:not(.exp-heading)' : '.gs-fade-up').forEach((el) => {
    gsap.fromTo(el,
      { opacity: 0, y: 42, clipPath: 'inset(0 0 100% 0)' },
      {
        opacity: 1,
        y: 0,
        clipPath: 'inset(0 0 0% 0)',
        duration: 1,
        ease: 'power4.out',
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
      y: 18,
      clipPath: 'inset(0 0 12% 0)',
      duration: 1.25,
      stagger: 0.08,
      ease: 'power4.out',
      delay: 0.1,
    })
  }

  const capStage = document.querySelector('.cap-stage')
  const capPanelsContainer = document.querySelector('.cap-panels')
  const capPanels = document.querySelectorAll('.cap-panel')
  const capReel = document.querySelector('.cap-reel')
  const setCapIndex = (index) => {
    capPanels.forEach((panel, i) => {
      panel.classList.toggle('is-active', i === index)
    })
  }

  if (capStage && capPanels.length) {
    if (!reduceMotion && gsap && ScrollTrigger && window.matchMedia('(min-width: 960px)').matches) {

      // Continuous scrub for the numbers reel
      if (capReel) {
        gsap.to(capReel, {
          yPercent: -((capPanels.length - 1) * (100 / capPanels.length)),
          ease: 'none',
          scrollTrigger: {
            trigger: capPanelsContainer,
            start: 'top top',
            end: 'bottom bottom',
            scrub: 1.1
          }
        })
      }

      // Discrete triggers for text panel active states + auto-scroll
      capPanels.forEach((panel, index) => {
        // Active state toggling
        ScrollTrigger.create({
          trigger: panel,
          start: 'top 50%',
          end: 'bottom 50%',
          onEnter: () => setCapIndex(index),
          onEnterBack: () => setCapIndex(index),
        });

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
    const isClosingRow = row.classList.contains('exp-closing')

    if (imgWrap) {
      if (isClosingRow) {
        gsap.fromTo(imgWrap,
          { y: 90, opacity: 0, scale: 0.94 },
          {
            y: 0,
            opacity: 1,
            scale: 1,
            duration: 1,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: row,
              start: 'top 88%',
              toggleActions: 'play none none none',
              once: true,
            },
          }
        )
      } else {
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
    }

    if (textEls.length) {
      gsap.fromTo(textEls,
        { opacity: 0, y: isClosingRow ? 90 : 24 },
        {
          opacity: 1,
          y: 0,
          duration: isClosingRow ? 1 : 0.7,
          stagger: 0.08,
          ease: isClosingRow ? 'power3.out' : 'power2.out',
          scrollTrigger: {
            trigger: row,
            start: isClosingRow ? 'top 88%' : 'clamp(top 72%)',
            toggleActions: 'play none none none',
            once: true,
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

    const conversationTrigger = document.querySelector('.conversation-link');
    const conversationForm = document.querySelector('.conversation-form');
    if (conversationTrigger && conversationForm) {
      conversationTrigger.addEventListener('click', () => {
        conversationForm.hidden = false;
        conversationTrigger.setAttribute('aria-expanded', 'true');
        conversationTrigger.style.display = 'none';
        conversationForm.querySelector('input:not([type="hidden"])')?.focus();
      });

      conversationForm.addEventListener('submit', () => {
        const submitButton = conversationForm.querySelector('.conversation-submit');
        if (submitButton) submitButton.textContent = 'Sending...';
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

  // ─── EVENTS: STICKY CANVAS SCROLL ───────────────────────────────────────────
  const eventsScroller = document.getElementById('events-scroller');
  const editorialGallery = document.getElementById('editorial-gallery');

  if (eventsScroller && editorialGallery) {

    // Art-directed compositions — each is one "viewport scene"
    // type: 'duo' | 'trio' | 'quad'
    // Each item: { src, color, shape: 'landscape'|'portrait'|'square', offset: 'top'|'mid'|'bot' }
    const compositions = [

      // ── COMPOSITION 1: DUO — big landscape left, small portrait right ──
      {
        type: 'duo',
        items: [
          { src: '/assets/events/1.png', color: 'field-navy',    shape: 'landscape', offset: 'mid' },
          { src: '/assets/events/4.jpg', color: 'field-terrace', shape: 'portrait',  offset: 'bot', fit: 'cover' },
        ]
      },

      // ── COMPOSITION 2: TRIO — landscape + portrait + portrait ──
      {
        type: 'trio',
        items: [
          { src: '/assets/events/6.jpg', color: 'field-sage',    shape: 'portrait',  offset: 'bot', fit: 'cover' },
          { src: '/assets/events/1.png', color: 'field-blush',   shape: 'portrait',  offset: 'bot' },
          { src: '/assets/events/5.jpg', color: 'field-ink',     shape: 'portrait',  offset: 'mid', fit: 'cover' },
        ]
      },

      // ── COMPOSITION 3: DUO — small portrait left, big portrait right ──
      {
        type: 'duo',
        items: [
          { src: '/assets/events/2.png', color: 'field-violet',  shape: 'portrait',  offset: 'top' },
          { src: '/assets/events/7.jpg', color: 'field-rust',    shape: 'portrait',  offset: 'bot', fit: 'cover' },
        ]
      },

      // ── COMPOSITION 4: QUAD — four images, two sizes ──
      {
        type: 'quad',
        items: [
          { src: '/assets/events/9.jpg', color: 'field-terrace', shape: 'portrait',  offset: 'bot', fit: 'cover' },
          { src: '/assets/events/3.png', color: 'field-navy',    shape: 'square',    offset: 'bot' },
          { src: '/assets/events/10.jpg', color: 'field-sage',   shape: 'square',    offset: 'mid', fit: 'cover' },
          { src: '/assets/events/1.png', color: 'field-chalk',   shape: 'portrait',  offset: 'top' },
        ]
      },

      // ── COMPOSITION 5: TRIO — portrait + landscape + portrait ──
      {
        type: 'trio',
        items: [
          { src: '/assets/events/2.png', color: 'field-ink',     shape: 'portrait',  offset: 'mid' },
          { src: '/assets/events/11.jpg', color: 'field-blush',  shape: 'portrait',  offset: 'bot', fit: 'cover' },
          { src: '/assets/events/3.png', color: 'field-rust',    shape: 'landscape', offset: 'bot' },
        ]
      },

      // ── COMPOSITION 6: TRIO — conference portrait + wide group + portrait ──
      {
        type: 'trio',
        items: [
          { src: '/assets/events/4.jpg', color: 'field-terrace', shape: 'portrait',  offset: 'bot', fit: 'cover' },
          { src: '/assets/events/3.png', color: 'field-navy',    shape: 'landscape', offset: 'bot' },
          { src: '/assets/events/8.jpg', color: 'field-sage',    shape: 'portrait',  offset: 'mid', fit: 'cover' },
        ]
      },

      // ── COMPOSITION 7: DUO — stage portrait pair ──
      {
        type: 'duo',
        items: [
          { src: '/assets/events/7.jpg', color: 'field-blush',   shape: 'portrait',  offset: 'top', fit: 'cover' },
          { src: '/assets/events/2.png', color: 'field-violet',  shape: 'portrait',  offset: 'bot' },
        ]
      },

      // ── COMPOSITION 8: QUAD — formal portraits and international settings ──
      {
        type: 'quad',
        items: [
          { src: '/assets/events/9.jpg',  color: 'field-rust',    shape: 'portrait',  offset: 'bot', fit: 'cover' },
          { src: '/assets/events/10.jpg', color: 'field-ink',     shape: 'square',    offset: 'top', fit: 'cover' },
          { src: '/assets/events/3.png',  color: 'field-sage',    shape: 'square',    offset: 'bot' },
          { src: '/assets/events/6.jpg',  color: 'field-navy',    shape: 'portrait',  offset: 'top', fit: 'cover' },
        ]
      },
    ];

    // Build HTML from compositions
    let html = '';
    compositions.forEach((comp) => {
      html += `<div class="comp-scene comp-${comp.type}">`;
      comp.items.forEach((item) => {
        html += `
          <div class="img-field ${item.color} shape-${item.shape} offset-${item.offset}${item.fit ? ` fit-${item.fit}` : ''}${item.fit ? ` photo-${item.src.split('/').pop().replace('.jpg', '')}` : ''}${item.src.endsWith('/3.png') ? ' asset-speaker' : ''}">
            <img src="${item.src}" alt="Speaking and Events — Henok Demelash" loading="eager" decoding="async" draggable="false">
          </div>`;
      });
      html += `</div>`;
    });
    editorialGallery.innerHTML = html;

    // Each composition is a document-flow card. Its transform is calculated
    // from its viewport position on one shared animation frame per scroll.
    window.setTimeout(() => {
      const canvas = document.querySelector('.events-sticky-canvas');
      if (!canvas) return;

      const scenes = Array.from(editorialGallery.querySelectorAll('.comp-scene'));
      const canvasH = canvas.offsetHeight;
      const sceneDistance = canvasH * 0.92;
      const entryStrength = 0.68;
      let frameId = 0;

      eventsScroller.style.height = 'auto';

      const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
      const cubicEase = (progress) => progress + (progress ** 3 - progress) * entryStrength;
      const updateScenes = () => {
        frameId = 0;
        const viewportHeight = window.innerHeight;

        scenes.forEach((scene) => {
          const rect = scene.getBoundingClientRect();
          const entryDistance = Math.min(rect.height * 0.8, viewportHeight * 0.45) * 0.97;
          const exitDistance = Math.min(rect.height * 0.32, viewportHeight * 0.18) * 0.5;
          const entryProgress = clamp((viewportHeight - rect.top + entryDistance) / entryDistance);
          // Let the card travel naturally; only ease it out once it is nearly
          // finished leaving through the top of the viewport.
          const exitProgress = clamp((exitDistance - rect.bottom) / exitDistance);
          const entryOffset = (1 - cubicEase(entryProgress)) * entryDistance;
          const exitOffset = cubicEase(exitProgress) * exitDistance;

          scene.style.transform = `translate3d(0, ${entryOffset - exitOffset}px, 0)`;
        });
      };

      const requestSceneUpdate = () => {
        if (!frameId) frameId = requestAnimationFrame(updateScenes);
      };

      window.addEventListener('scroll', requestSceneUpdate, { passive: true });
      window.addEventListener('resize', requestSceneUpdate, { passive: true });
      updateScenes();
      if (ScrollTrigger) {
        requestAnimationFrame(() => ScrollTrigger.refresh());
      }
    }, 0);
  }

  // --- FOOTER REVEAL PARALLAX ---
  const footerRevealContainer = document.querySelector('.footer-reveal-container');
  const finalSection = document.querySelector('.final-section');
  if (footerRevealContainer && finalSection && !reduceMotion) {
    const isJourneyFooter = finalSection.classList.contains('final-section--journey');
    if (!isJourneyFooter) {
      gsap.fromTo(finalSection,
        { yPercent: -50 },
        {
          yPercent: 0,
          ease: "none",
          scrollTrigger: {
            trigger: footerRevealContainer,
            start: "top bottom",
            end: "bottom bottom",
            scrub: 0.65,
            invalidateOnRefresh: true,
          }
        }
      );
    }

    const footerCopy = finalSection.querySelectorAll('.footer-copy');
    if (footerCopy.length) {
      gsap.fromTo(footerCopy,
        { y: 54, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          ease: 'none',
          stagger: 0.08,
          scrollTrigger: {
            trigger: footerRevealContainer,
            start: 'top 92%',
            end: 'top 42%',
            scrub: 0.8,
            invalidateOnRefresh: true,
          },
        }
      );
    }
  }
})
