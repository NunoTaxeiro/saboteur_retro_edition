function App() {
  const buildStamp = "20260405b";

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">React + HTML Host Page</p>
        <h1>Saboteur Retro Edition</h1>
        <p>
          This React page embeds the browser build of your Python game.
          Drop the generated web files into public/saboteur-web and the game
          loads below.
        </p>
      </header>

      <main className="layout">
        <section className="panel game-panel">
          <div className="panel-head">
            <h2>Playable Game</h2>
            <a href={`/saboteur-web/index.html?v=${buildStamp}`} target="_blank" rel="noreferrer">
              Open standalone
            </a>
          </div>

          <div className="game-shell">
            <iframe
              title="Saboteur Retro Edition"
              src={`/saboteur-web/index.html?v=${buildStamp}`}
              className="game-frame"
              allow="autoplay; fullscreen; gamepad; xr-spatial-tracking"
            />
          </div>
        </section>

        <section className="panel setup-panel">
          <h2>One-time Setup</h2>
          <ol>
            <li>Build a web version of saboteur.py (for example with pygbag).</li>
            <li>Copy all generated web files into web/public/saboteur-web.</li>
            <li>Run npm install, then npm run dev in the web folder.</li>
          </ol>
          <p className="note">
            If you still see the placeholder page in the frame, the generated
            game files are not in public/saboteur-web yet.
          </p>
        </section>
      </main>
    </div>
  );
}

export default App;
