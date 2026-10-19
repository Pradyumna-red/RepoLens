function LoadingScreen() {
  return (
    <section className="loading-panel" aria-live="polite" aria-busy="true">
      <span className="loading-spinner" aria-hidden="true" />
      <div>
        <p className="eyebrow">Analysis in progress</p>
        <h2>Uploading and analyzing your project…</h2>
        <p className="muted-text">This can take a moment for larger repositories.</p>
      </div>
    </section>
  )
}

export default LoadingScreen
