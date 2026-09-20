import "./Landingpage.css";

const destinations = [
  {
    name: "Goa",
    image:
      "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=900&q=80",
    text: "Beaches, sunsets and unforgettable experiences.",
  },
  {
    name: "Dubai",
    image:
      "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=900&q=80",
    text: "Luxury, adventure and iconic city experiences.",
  },
  {
    name: "Kashmir",
    image:
      "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=900&q=80",
    text: "Mountains, lakes and peaceful escapes.",
  },
  {
    name: "Thailand",
    image:
      "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=900&q=80",
    text: "Tropical beaches, culture and adventure.",
  },
];

const packages = [
  {
    title: "Goa Beach Escape",
    location: "Goa, India",
    price: "₹14,999",
    image:
      "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=900&q=80",
  },
  {
    title: "Magical Kashmir",
    location: "Kashmir, India",
    price: "₹22,999",
    image:
      "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=900&q=80",
  },
  {
    title: "Dubai Explorer",
    location: "Dubai, UAE",
    price: "₹39,999",
    image:
      "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=900&q=80",
  },
];

export default function LandingPage() {
  const scrollToSection = (id) => {
    const element = document.getElementById(id);

    if (element) {
      element.scrollIntoView({
        behavior: "smooth",
      });
    }
  };

  return (
    <div className="hb-landing">
      {/* NAVBAR */}
      <nav className="hb-navbar">
        <div className="hb-logo"><center>
          Holiday</center>
        </div>

        

        
      </nav>

      {/* HERO */}
      <section id="home" className="hb-hero">
        <div className="hb-hero-overlay"></div>

        <div className="hb-hero-content">
          <div className="hb-hero-badge">
            ✈️ Your journey starts here
          </div>

          <h1>
            Explore the world.
            <br />
            <span>Make memories.</span>
          </h1>

          <p>
            Discover beautiful destinations, personalized trips and
            unforgettable experiences with HolidayBreakz.
          </p>

          <div className="hb-hero-actions">
            <button
              className="hb-primary-btn"
              onClick={() => scrollToSection("destinations")}
            >
              Explore Destinations
            </button>

            <button
              className="hb-secondary-btn"
              onClick={() => scrollToSection("packages")}
            >
              View Packages
            </button>
          </div>
        </div>
      </section>

      {/* SEARCH */}
      <section className="hb-search-section">
        <div className="hb-search-card">
          <div className="hb-search-item">
            <span>📍</span>
            <div>
              <small>Where</small>
              <strong>Choose destination</strong>
            </div>
          </div>

          <div className="hb-search-item">
            <span>📅</span>
            <div>
              <small>When</small>
              <strong>Select travel dates</strong>
            </div>
          </div>

          <div className="hb-search-item">
            <span>👥</span>
            <div>
              <small>Travelers</small>
              <strong>2 Travelers</strong>
            </div>
          </div>

          <button className="hb-search-btn">Search Trips</button>
        </div>
      </section>

      {/* STATS */}
      <section className="hb-stats">
        <div>
          <strong>50K+</strong>
          <span>Happy Travelers</span>
        </div>

        <div>
          <strong>100+</strong>
          <span>Destinations</span>
        </div>

        <div>
          <strong>500+</strong>
          <span>Travel Packages</span>
        </div>

        <div>
          <strong>24/7</strong>
          <span>Travel Support</span>
        </div>
      </section>

      {/* DESTINATIONS */}
      <section id="destinations" className="hb-section">
        <div className="hb-section-heading">
           
          <h2><center>Popular Destinations</center></h2>
           
        </div>

        <div className="hb-destination-grid">
          {destinations.map((destination) => (
            <div className="hb-destination-card" key={destination.name}>
              <img src={destination.image} alt={destination.name} />

              <div className="hb-card-overlay">
                <h3>{destination.name}</h3>
                <p>{destination.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* WHY US */}
      <section id="why-us" className="hb-why-section" backgroundColor="#f9f9f9">
        <div className="hb-section-heading">
           
          <h2>Travel made simple</h2>
           
        </div>

        <div className="hb-why-grid">
          <div className="hb-why-card">
            <div className="hb-icon">🌍</div>
            <h3>Beautiful Destinations</h3>
            <p>
              Discover amazing places and experiences around the world.
            </p>
          </div>

          <div className="hb-why-card">
            <div className="hb-icon">💰</div>
            <h3>Best Value</h3>
            <p>
              Get carefully planned travel packages at competitive prices.
            </p>
          </div>

          <div className="hb-why-card">
            <div className="hb-icon">🤖</div>
            <h3>AI Travel Assistant</h3>
            <p>
              Get instant help with destinations, bookings and travel
              questions.
            </p>
          </div>

          <div className="hb-why-card">
            <div className="hb-icon">🛎️</div>
            <h3>24/7 Support</h3>
            <p>
              Our support is available whenever you need assistance.
            </p>
          </div>
        </div>
      </section>

      {/* PACKAGES */}
      <section id="packages" className="hb-section">
        <div className="hb-section-heading">
          
          <h2>Plan your next adventure</h2>
          
        </div>

        <div className="hb-package-grid">
          {packages.map((pkg) => (
            <div className="hb-package-card" key={pkg.title}>
              <img src={pkg.image} alt={pkg.title} />

              <div className="hb-package-content">
                <span>{pkg.location}</span>
                <h3>{pkg.title}</h3>

                <div className="hb-package-bottom">
                  <div>
                    <small>Starting from</small>
                    <strong>{pkg.price}</strong>
                  </div>

                  <button>View Trip</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* AI ASSISTANT */}
      <section className="hb-ai-section">
        <div className="hb-ai-content">
          <span>AI TRAVEL ASSISTANT</span>

          <h2>
            Your personal travel
            <br />
            assistant is always ready.
          </h2>

          <p>
            Ask about destinations, flights, bookings, cancellations,
            baggage and more. Get instant answers while planning your trip.
          </p>

          <button
            className="hb-primary-btn"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            Chat with AI Assistant
          </button>
        </div>
      </section> <br></br>

      

      {/* FOOTER */}
      <footer className="hb-footer" >
        <div className="hb-footer-logo">
          <center>Holiday<span>Breakz</span></center>
        </div>

        <p><center>
          Your journey. Your memories. Your HolidayBreakz.
        </center></p>

          <div className="hb-footer-links"> <center>
          <button onClick={() => scrollToSection("home")}>Home</button>
          <button onClick={() => scrollToSection("destinations")}>
            Destinations
          </button>
          <button onClick={() => scrollToSection("packages")}>
            Packages
          </button>
          <button onClick={() => scrollToSection("contact")}>
            Contact
          </button>
        </center></div> 

        <small><center>© 2026 HolidayBreakz. All rights reserved.</center></small>
      </footer>
    </div>
  );
}