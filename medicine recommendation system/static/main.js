/*==================== SHOW MENU ====================*/
const showMenu = (toggleId, navId) =>{
    const toggle = document.getElementById(toggleId),
    nav = document.getElementById(navId)
    
    // Validate that variables exist
    if(toggle && nav){
        toggle.addEventListener('click', ()=>{
            // We add the show-menu class to the div tag with the nav__menu class
            nav.classList.toggle('show-menu')
        })
    }
}
showMenu('nav-toggle','nav-menu')

/*==================== REMOVE MENU MOBILE ====================*/
const navLink = document.querySelectorAll('.nav__link')

function linkAction(){
    const navMenu = document.getElementById('nav-menu')
    // When we click on each nav__link, we remove the show-menu class
    navMenu.classList.remove('show-menu')
}
navLink.forEach(n => n.addEventListener('click', linkAction))

/*==================== SCROLL SECTIONS ACTIVE LINK ====================*/
const sections = document.querySelectorAll('section[id]')

function scrollActive(){
    const scrollY = window.pageYOffset

    sections.forEach(current =>{
        const sectionHeight = current.offsetHeight
        const sectionTop = current.offsetTop - 50;
        sectionId = current.getAttribute('id')

        if(scrollY > sectionTop && scrollY <= sectionTop + sectionHeight){
            document.querySelector('.nav__menu a[href*=' + sectionId + ']').classList.add('active-link')
        }else{
            document.querySelector('.nav__menu a[href*=' + sectionId + ']').classList.remove('active-link')
        }
    })
}
window.addEventListener('scroll', scrollActive)

/*==================== CHANGE BACKGROUND HEADER ====================*/ 
function scrollHeader(){
    const nav = document.getElementById('header')
    // When the scroll is greater than 200 viewport height, add the scroll-header class to the header tag
    if(this.scrollY >= 200) nav.classList.add('scroll-header'); else nav.classList.remove('scroll-header')
}
window.addEventListener('scroll', scrollHeader)

/*==================== SHOW SCROLL TOP ====================*/ 
function scrollTop(){
    const scrollTop = document.getElementById('scroll-top');
    // When the scroll is higher than 560 viewport height, add the show-scroll class to the a tag with the scroll-top class
    if(this.scrollY >= 560) scrollTop.classList.add('show-scroll'); else scrollTop.classList.remove('show-scroll')
}
window.addEventListener('scroll', scrollTop)

/*==================== DARK LIGHT THEME ====================*/ 
const themeButton = document.getElementById('theme-button')
const darkTheme = 'dark-theme'
const iconTheme = 'bx-sun'

// Previously selected topic (if user selected)
const selectedTheme = localStorage.getItem('selected-theme')
const selectedIcon = localStorage.getItem('selected-icon')

// We obtain the current theme that the interface has by validating the dark-theme class
const getCurrentTheme = () => document.body.classList.contains(darkTheme) ? 'dark' : 'light'
const getCurrentIcon = () => themeButton.classList.contains(iconTheme) ? 'bx-moon' : 'bx-sun'

// We validate if the user previously chose a topic
if (selectedTheme) {
  // If the validation is fulfilled, we ask what the issue was to know if we activated or deactivated the dark
  document.body.classList[selectedTheme === 'dark' ? 'add' : 'remove'](darkTheme)
  themeButton.classList[selectedIcon === 'bx-moon' ? 'add' : 'remove'](iconTheme)
}

// Activate / deactivate the theme manually with the button
themeButton.addEventListener('click', () => {
    // Add or remove the dark / icon theme
    document.body.classList.toggle(darkTheme)
    themeButton.classList.toggle(iconTheme)
    // We save the theme and the current icon that the user chose
    localStorage.setItem('selected-theme', getCurrentTheme())
    localStorage.setItem('selected-icon', getCurrentIcon())
})

/*==================== SCROLL REVEAL ANIMATION ====================*/
const sr = ScrollReveal({
    origin: 'top',
    distance: '30px',
    duration: 2000,
    reset: true
});

sr.reveal(`.home__data, .home__img,
            .about__data, .about__img,
            .services__content, .menu__content,
            .app__data, .app__img,
            .contact__data, .contact__button,
            .footer__content`, {
    interval: 200
})


  document.addEventListener("DOMContentLoaded", function () {
    const userSelect = document.getElementById("language-select");

    userSelect.addEventListener("change", () => {
      const selectedLang = userSelect.value;
      const googleCombo = document.querySelector(".goog-te-combo");

      if (!googleCombo) {
        alert("Translator not loaded yet. Please wait a moment and try again.");
        return;
      }

      googleCombo.value = selectedLang;
      googleCombo.dispatchEvent(new Event("change"));
    });
  });

 
  // NEW JAVASCRIPT FOR MAP AND DOCTOR SEARCH
document.addEventListener('DOMContentLoaded', () => {
    const mapStatusDiv = document.getElementById('map-status');
    const findDoctorsBtn = document.getElementById('findDoctorsBtn');
    let map; // Declare map variable globally or in a scope accessible to functions

    // Initialize the map only if the mapid element exists
    if (document.getElementById('mapid')) {
        // Set default view (e.g., a central location like London)
        // This will be updated to the user's location if geolocation is successful.
        map = L.map('mapid').setView([51.505, -0.09], 13);

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        mapStatusDiv.textContent = 'Map loaded. Click "Find Nearby Doctors" to begin.';
    } else {
        mapStatusDiv.textContent = 'Map container not found. Ensure #mapid exists in index.html.';
    }

    // Event listener for the "Find Nearby Doctors" button
    if (findDoctorsBtn) {
        findDoctorsBtn.addEventListener('click', findDoctors);
    }

    function findDoctors() {
        if (!map) {
            mapStatusDiv.textContent = 'Map not initialized. Cannot find doctors.';
            return;
        }

        mapStatusDiv.textContent = 'Locating you...';
        findDoctorsBtn.disabled = true; // Disable button during search

        // Get user's current geolocation
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;

                    mapStatusDiv.textContent = `Located at: ${lat.toFixed(4)}, ${lon.toFixed(4)}. Searching for doctors...`;
                    map.setView([lat, lon], 14); // Center map on user's location

                    // Clear existing markers if any
                    map.eachLayer((layer) => {
                        if (layer instanceof L.Marker) {
                            map.removeLayer(layer);
                        }
                    });

                    // Call backend to find doctors
                    fetch('/find_doctors', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ latitude: lat, longitude: lon })
                    })
                    .then(response => {
                        if (!response.ok) {
                            // If response is not OK (e.g., 404, 500), throw an error
                            return response.json().then(err => { throw new Error(err.error || 'Server error'); });
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.doctors && data.doctors.length > 0) {
                            mapStatusDiv.textContent = `Found ${data.doctors.length} doctors nearby!`;
                            data.doctors.forEach(doctor => {
                                // Add a marker for each doctor
                                L.marker([doctor.lat, doctor.lon])
                                    .addTo(map)
                                    .bindPopup(`<b>${doctor.name || 'Doctor'}</b><br>${doctor.address || 'Address not available'}`)
                                    .openPopup();
                            });
                        } else {
                            mapStatusDiv.textContent = 'No doctors found nearby.';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching doctors:', error);
                        mapStatusDiv.textContent = `Error: ${error.message}. Could not find doctors.`;
                    })
                    .finally(() => {
                        findDoctorsBtn.disabled = false; // Re-enable button
                    });
                },
                (error) => {
                    // Handle geolocation errors
                    findDoctorsBtn.disabled = false;
                    let errorMessage;
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage = "Geolocation permission denied. Please allow location access.";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage = "Location information is unavailable.";
                            break;
                        case error.TIMEOUT:
                            errorMessage = "The request to get user location timed out.";
                            break;
                        case error.UNKNOWN_ERROR:
                            errorMessage = "An unknown geolocation error occurred.";
                            break;
                        default:
                            errorMessage = "Geolocation error.";
                    }
                    mapStatusDiv.textContent = `Error: ${errorMessage}`;
                    console.error('Geolocation error:', error);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 } // Geolocation options
            );
        } else {
            findDoctorsBtn.disabled = false;
            mapStatusDiv.textContent = 'Geolocation is not supported by your browser.';
        }
    }
});
document.getElementById('symptom-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const symptoms = document.getElementById('symptoms').value.trim();
  if (!symptoms) {
    alert("Please enter symptoms first.");
    return;
  }
  fetch('/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symptoms: symptoms })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
      return;
    }
    document.getElementById('predicted-disease').textContent = data.predicted_disease;
    document.getElementById('disease-description').textContent = data.description;
    // Update lists
    const setList = (id, items) => {
      const ul = document.getElementById(id);
      ul.innerHTML = "";
      (items || []).forEach(i => {
        const li = document.createElement("li");
        li.textContent = i;
        ul.appendChild(li);
      });
    };
    setList("precautions-list", data.precautions);
    setList("medications-list", data.medications);
    setList("diet-list", data.diet);
    setList("workout-list", data.workout);
    document.getElementById('result').style.display = "block";
    document.getElementById('result').scrollIntoView({ behavior: "smooth" });
  })
  .catch(() => {
    alert("Error getting suggestions. Please try again.");
  });
});