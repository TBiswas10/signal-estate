import React, { useEffect, useState } from "react";

import { apiGet, apiPost } from "../api";

function formatMoney(value) {
  return `$${Math.round(value).toLocaleString()}`;
}

export default function LandingPage() {
  const [rankings, setRankings] = useState([]);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [navFloating, setNavFloating] = useState(false);

  useEffect(() => {
    if (!menuOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [menuOpen]);

  useEffect(() => {
    function onScroll() {
      setNavFloating(window.scrollY > 18);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    async function loadPreview() {
      try {
        const data = await apiGet("/rankings/suburbs?limit=3");
        setRankings(data);
      } catch {
        setRankings([]);
      }
    }
    loadPreview();
  }, []);

  useEffect(() => {
    const elements = Array.from(document.querySelectorAll(".reveal"));
    if (!elements.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16, rootMargin: "0px 0px -8% 0px" },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  async function submitWaitlist(event) {
    event.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || !trimmed.includes("@")) {
      setStatus("error");
      setMessage("Enter a valid email to join the private waitlist.");
      return;
    }

    try {
      setSubmitting(true);
      const result = await apiPost("/waitlist", {
        email: trimmed,
        source: "landing",
      });
      setStatus("success");
      setMessage(result.message);
      setEmail("");
    } catch {
      setStatus("error");
      setMessage("Could not submit your request. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={`landing-root ${menuOpen ? "mobile-menu-open" : ""}`}>
      <header className={`landing-nav ${navFloating ? "is-floating" : ""}`}>
        <a href="/" className="brand-wordmark">
          SignalEstate
        </a>
        <button
          type="button"
          className={`hamburger-btn ${menuOpen ? "is-open" : ""}`}
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="landing-nav-links"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
        <nav id="landing-nav-links" className={menuOpen ? "nav-open" : ""}>
          <a href="#why" onClick={() => setMenuOpen(false)}>
            Why Us
          </a>
          <a href="#system" onClick={() => setMenuOpen(false)}>
            Engine
          </a>
          <a href="#guide" onClick={() => setMenuOpen(false)}>
            Guide
          </a>
          <a href="#waitlist" onClick={() => setMenuOpen(false)}>
            Waitlist
          </a>
          <a className="nav-cta" href="/app" onClick={() => setMenuOpen(false)}>
            Enter App
          </a>
        </nav>
      </header>
      <button
        type="button"
        aria-label="Close menu"
        className={`mobile-menu-backdrop ${menuOpen ? "is-open" : ""}`}
        onClick={() => setMenuOpen(false)}
      />

      <section className="landing-hero">
        <p className="eyebrow">AUSTRALIAN PROPERTY INTELLIGENCE</p>
        <h1>Find Alpha Before The Market Sees It.</h1>
        <p className="hero-subtext">
          SignalEstate blends valuation mechanics, scenario stress testing, and suburb intelligence into one decisive investment screen.
        </p>
        <div className="hero-cta-row">
          <a className="primary-cta" href="#waitlist">
            Join Private Waitlist
          </a>
          <a className="secondary-cta" href="/app">
            Explore Live App
          </a>
          <a className="secondary-cta" href="/guide.html" target="_blank" rel="noreferrer">
            Read Quick Guide
          </a>
        </div>
      </section>

      <section id="why" className="landing-section reveal reveal-1">
        <div className="section-title-wrap">
          <p className="eyebrow">WHY INVESTORS SWITCH</p>
          <h2>From Listings To Conviction.</h2>
        </div>
        <div className="feature-grid">
          <article>
            <h3>Scenario Intelligence</h3>
            <p>See how each property behaves across rates-down, base-case, and rates-up environments.</p>
          </article>
          <article>
            <h3>Risk-Layered Valuation</h3>
            <p>Every estimate is paired with fragility, liquidity, downside, and macro stress context.</p>
          </article>
          <article>
            <h3>Actionable Signals</h3>
            <p>Get alpha signals and strategy-fit tags instead of generic suburb heatmaps.</p>
          </article>
        </div>
      </section>

      <section id="system" className="landing-section system-card reveal reveal-2">
        <div>
          <p className="eyebrow">LIVE PREVIEW</p>
          <h2>Top Suburb Signals Right Now</h2>
          <p>This feed is generated from the same analysis engine powering in-app valuation intelligence.</p>
        </div>
        <ul className="suburb-preview-list">
          {rankings.length > 0 ? (
            rankings.map((r) => (
              <li key={`${r.postcode}-${r.suburb}`}>
                <div>
                  <strong>
                    {r.suburb}, {r.state}
                  </strong>
                  <span>
                    median {formatMoney(r.median_price)} | yield {r.rental_yield_pct.toFixed(1)}%
                  </span>
                </div>
                <em>{r.investment_score.toFixed(2)}</em>
              </li>
            ))
          ) : (
            <li>
              <div>
                <strong>Data feed unavailable</strong>
                <span>Start backend to enable live suburb previews.</span>
              </div>
              <em>-</em>
            </li>
          )}
        </ul>
      </section>

      <section id="guide" className="landing-section platform-map reveal reveal-3">
        <div className="platform-map-intro">
          <p className="eyebrow">HOW THE SOFTWARE WORKS</p>
          <h2>Signal Pipeline: Data Intake To Execution Decision</h2>
          <p>
            The product runs as a deterministic pipeline. Every action in the interface moves evidence through three layers: ingest, analysis,
            and execution. This is the operating model used by active investors to avoid ad-hoc decisions.
          </p>
          <div className="guide-mission-strip" aria-label="Core workflow path">
            <span>Discover</span>
            <span>Underwrite</span>
            <span>Stress Test</span>
            <span>Execute</span>
          </div>
          <div className="platform-map-actions">
            <a className="primary-cta" href="/guide.html" target="_blank" rel="noreferrer">
              Open Full Guide
            </a>
          </div>
        </div>

        <div className="platform-flow" aria-label="SignalEstate flow diagram">
          <article className="flow-lane lane-ingest">
            <header>
              <span className="lane-chip">Layer 1</span>
              <h3>Ingest</h3>
            </header>
            <ul>
              <li>
                <strong>Market + Deals</strong>
                <span>Source opportunities from ranked suburbs, spread signals, and deal momentum.</span>
              </li>
              <li>
                <strong>News + Comps</strong>
                <span>Add context from macro headlines and comparable evidence before underwriting.</span>
              </li>
            </ul>
          </article>

          <article className="flow-lane lane-analysis">
            <header>
              <span className="lane-chip">Layer 2</span>
              <h3>Analysis</h3>
            </header>
            <ul>
              <li>
                <strong>Valuation + Research</strong>
                <span>Generate confidence, downside, acquisition costs, tax position, and serviceability.</span>
              </li>
              <li>
                <strong>Strategy + Scenario</strong>
                <span>Stress rates, rents, and costs under base, upside, and downside market regimes.</span>
              </li>
              <li>
                <strong>Portfolio Risk</strong>
                <span>Model volatility and concentration impact before committing a pipeline slot.</span>
              </li>
            </ul>
          </article>

          <article className="flow-lane lane-execution">
            <header>
              <span className="lane-chip">Layer 3</span>
              <h3>Execution</h3>
            </header>
            <ul>
              <li>
                <strong>Watchlist + Pipeline</strong>
                <span>Promote high-conviction assets into active workflows and track stage progression.</span>
              </li>
              <li>
                <strong>Reports + Artifacts</strong>
                <span>Export committee-ready briefs with assumptions, risk posture, and recommendation logic.</span>
              </li>
            </ul>
          </article>
        </div>

        <div className="platform-map-footer">
          <div className="flow-legend-item">
            <span className="legend-dot legend-live" />
            <small>Live data surfaces</small>
          </div>
          <div className="flow-legend-item">
            <span className="legend-dot legend-model" />
            <small>Model and scenario computation</small>
          </div>
          <div className="flow-legend-item">
            <span className="legend-dot legend-output" />
            <small>Execution and reporting outputs</small>
          </div>
        </div>

        <div className="guide-operations-grid">
          <article className="guide-ops-card">
            <h3>Operator Playbook</h3>
            <ul>
              <li>
                <strong>Market</strong>
                <span>Use Trending, Deals, and News to build candidate inventory from mispricing and momentum.</span>
              </li>
              <li>
                <strong>Analysis</strong>
                <span>Run valuation, research, strategy, and portfolio risk before advancing an asset.</span>
              </li>
              <li>
                <strong>Execution</strong>
                <span>Promote only risk-cleared opportunities to Watchlist, Pipeline, and final reporting.</span>
              </li>
            </ul>
          </article>

          <article className="guide-ops-card">
            <h3>Decision Guardrails</h3>
            <ul>
              <li>
                <strong>Confidence Gate</strong>
                <span>Avoid high-conviction decisions when confidence is weak or assumptions are stale.</span>
              </li>
              <li>
                <strong>Scenario Discipline</strong>
                <span>Always pass downside stress before upside narratives influence position sizing.</span>
              </li>
              <li>
                <strong>Portfolio Fit</strong>
                <span>Check concentration and volatility contribution before committing pipeline bandwidth.</span>
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section id="waitlist" className="landing-section waitlist-card reveal reveal-2">
        <div>
          <p className="eyebrow">PRIVATE BETA</p>
          <h2>Join The Waitlist</h2>
          <p>Get early access, investor workflow templates, and first-wave model updates.</p>
        </div>
        <form onSubmit={submitWaitlist} className="waitlist-form">
          <input
            type="email"
            placeholder="you@domain.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Request Access"}
          </button>
        </form>
        {status !== "idle" && (
          <p className={status === "success" ? "status-success" : "status-error"}>{message}</p>
        )}
      </section>
    </div>
  );
}
