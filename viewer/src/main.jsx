import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowLeft,
  ChevronRight,
  Play,
  Search,
  X,
  Globe2,
  Clock3,
  Film,
} from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function fetchJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function artworkUrl(storageKey) {
  return storageKey
    ? `${API_URL}/catalog/artwork/${storageKey}`
    : "";
}

function getArtwork(item, type) {
  return (item?.artwork || []).find((a) => a.type === type)?.storage_key || "";
}

function isTrailerEpisode(episode) {
  return Number(episode?.season_number) === 0;
}

function normalEpisodes(show) {
  return (show?.episodes || []).filter((e) => !isTrailerEpisode(e));
}

function trailerEpisodes(show) {
  return (show?.episodes || []).filter(isTrailerEpisode);
}

function App() {
  const [catalogue, setCatalogue] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [selectedShow, setSelectedShow] = useState(null);
  const [loading, setLoading] = useState(true);

  const allShows = useMemo(() => {
    if (!catalogue?.sections) return [];
    return Object.values(catalogue.sections).flat();
  }, [catalogue]);

  useEffect(() => {
    fetchJson("/catalog")
      .then(setCatalogue)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function runSearch(value) {
    setQuery(value);
    if (!value.trim()) {
      setResults(null);
      return;
    }
    try {
      const data = await fetchJson(`/catalog/search?q=${encodeURIComponent(value.trim())}`);
      setResults(data.shows || []);
    } catch (err) {
      setError(err.message);
    }
  }

  if (selectedShow) {
    return (
      <ShowDetail
        show={selectedShow}
        onBack={() => setSelectedShow(null)}
      />
    );
  }

  return (
    <div className="app">
      <Header query={query} onSearch={runSearch} />
      {loading && <div className="state">Loading catalogue…</div>}
      {!loading && error && (
        <div className="state error-state">
          <strong>Catalogue unavailable</strong>
          <span>{error}</span>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      )}
      {!loading && !error && catalogue && (
        <>
          {results ? (
            <SearchResults shows={results} onSelect={setSelectedShow} query={query} />
          ) : (
            <Home catalogue={catalogue} shows={allShows} onSelect={setSelectedShow} />
          )}
        </>
      )}
    </div>
  );
}

function Header({ query, onSearch }) {
  return (
    <header className="header">
      <div className="brand" onClick={() => onSearch("")}>PEBLO<span>TV</span></div>
      <nav>
        <button className="nav-link" onClick={() => onSearch("")}>Home</button>
      </nav>
      <div className="search-box">
        <Search size={18} />
        <input
          value={query}
          onChange={(e) => onSearch(e.target.value)}
          placeholder="Search shows and episodes"
          aria-label="Search catalogue"
        />
        {query && <button onClick={() => onSearch("")} aria-label="Clear search"><X size={17} /></button>}
      </div>
    </header>
  );
}

function Home({ catalogue, shows, onSelect }) {
  const featured =
    Object.entries(catalogue.sections || {}).find(([section]) => section.toLowerCase() === "featured")?.[1]?.[0]
    || shows[0];

  return (
    <main>
      {featured && <Hero show={featured} onSelect={onSelect} />}
      <div className="content">
        {Object.entries(catalogue.sections || {}).map(([section, entries]) => (
          <section className="catalog-row" key={section}>
            <div className="row-heading">
              <h2>{section}</h2>
              <span>{entries.length} {entries.length === 1 ? "show" : "shows"}</span>
            </div>
            <div className="show-grid">
              {entries.map((show) => (
                <ShowCard key={show.id} show={show} onClick={() => onSelect(show)} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}

function Hero({ show, onSelect }) {
  const banner = getArtwork(show, "banner") || getArtwork(show, "poster");
  return (
    <section className="hero" style={banner ? { backgroundImage: `linear-gradient(90deg, rgba(8,8,10,.98) 0%, rgba(8,8,10,.72) 45%, rgba(8,8,10,.15) 100%), url("${artworkUrl(banner)}")` } : undefined}>
      <div className="hero-copy">
        <div className="eyebrow">FEATURED</div>
        <h1>{show.title}</h1>
        <p>{show.synopsis || "Explore episodes from Peblo TV."}</p>
        <div className="hero-meta">
          <span>{show.categories?.join(" · ") || "Series"}</span>
          <span>{normalEpisodes(show).length} episodes</span>
        </div>
        <button className="primary-button" onClick={() => onSelect(show)}>
          <Play size={18} fill="currentColor" /> Explore show
        </button>
      </div>
    </section>
  );
}

function ShowCard({ show, onClick }) {
  const image = getArtwork(show, "poster") || getArtwork(show, "thumbnail") || getArtwork(show, "banner");
  return (
    <button className="show-card" onClick={onClick}>
      <div className="poster">
        {image ? (
          <img src={artworkUrl(image)} alt="" loading="lazy" />
        ) : (
          <div className="poster-placeholder">{show.title?.slice(0, 1)}</div>
        )}
      </div>
      <div className="card-info">
        <strong>{show.title}</strong>
        <span>{show.categories?.slice(0, 2).join(" · ") || "Peblo TV"}</span>
      </div>
    </button>
  );
}

function SearchResults({ shows, onSelect, query }) {
  return (
    <main className="content search-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">SEARCH</div>
          <h1>Results for “{query}”</h1>
        </div>
        <span>{shows.length} results</span>
      </div>
      {shows.length ? (
        <div className="show-grid large-grid">
          {shows.map((show) => (
            <ShowCard key={show.id} show={show} onClick={() => onSelect(show)} />
          ))}
        </div>
      ) : (
        <div className="empty">No shows or episodes matched your search.</div>
      )}
    </main>
  );
}

function ShowDetail({ show, onBack }) {
  const episodes = normalEpisodes(show);
  const trailers = trailerEpisodes(show);
  const seasons = [...new Set(episodes.map((e) => e.season_number))].sort((a, b) => a - b);

  return (
    <div className="app">
      <header className="detail-header">
        <button className="back-button" onClick={onBack}><ArrowLeft size={19} /> Back</button>
        <div className="brand">PEBLO<span>TV</span></div>
      </header>

      <main className="detail">
        <section className="detail-hero">
          <div className="detail-art">
            {getArtwork(show, "poster") ? (
              <img src={artworkUrl(getArtwork(show, "poster"))} alt="" />
            ) : (
              <div className="poster-placeholder big">{show.title?.slice(0, 1)}</div>
            )}
          </div>
          <div className="detail-copy">
            <div className="eyebrow">{show.section || "PEBLO TV"}</div>
            <h1>{show.title}</h1>
            <p className="synopsis">{show.synopsis || "No synopsis available."}</p>
            <div className="detail-meta">
              {show.categories?.map((c) => <span key={c}>{c}</span>)}
            </div>
            <div className="stats">
              <span><Film size={17} /> {episodes.length} episodes</span>
              <span><Globe2 size={17} /> {[...new Set(episodes.flatMap((e) => e.languages || []))].join(", ") || "—"}</span>
            </div>
          </div>
        </section>

        {seasons.map((seasonNumber) => (
          <section className="episode-section" key={seasonNumber}>
            <div className="row-heading">
              <h2>Season {seasonNumber}</h2>
              <span>{episodes.filter((e) => e.season_number === seasonNumber).length} episodes</span>
            </div>
            <div className="episode-list">
              {episodes
                .filter((e) => e.season_number === seasonNumber)
                .map((episode, index) => <EpisodeCard key={`${episode.content_group}-${index}`} episode={episode} />)}
            </div>
          </section>
        ))}

        {trailers.length > 0 && (
          <section className="episode-section">
            <div className="row-heading">
              <h2>Trailers</h2>
              <span>Season 0</span>
            </div>
            <div className="episode-list">
              {trailers.map((episode, index) => <EpisodeCard key={`${episode.content_group}-trailer-${index}`} episode={episode} trailer />)}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function EpisodeCard({ episode, trailer }) {
  const image = getArtwork(episode, "thumbnail") || getArtwork(episode, "banner") || getArtwork(episode, "poster");
  return (
    <article className="episode-card">
      <div className="episode-thumb">
        {image ? <img src={artworkUrl(image)} alt="" loading="lazy" /> : <div className="thumb-placeholder"><Play size={24} /></div>}
        <div className="episode-number">{trailer ? "TRAILER" : `E${String(episode.episode_number).padStart(2, "0")}`}</div>
      </div>
      <div className="episode-copy">
        <div className="episode-title-line">
          <h3>{episode.title}</h3>
          {episode.duration_seconds ? <span><Clock3 size={15} /> {formatDuration(episode.duration_seconds)}</span> : null}
        </div>
        <p>{episode.synopsis || "No episode synopsis available."}</p>
        <div className="language-pills">
          {(episode.languages || []).map((language) => <span key={language}>{language}</span>)}
        </div>
      </div>
    </article>
  );
}

function formatDuration(seconds) {
  const minutes = Math.floor(Number(seconds) / 60);
  const secs = Number(seconds) % 60;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

createRoot(document.getElementById("root")).render(<App />);
