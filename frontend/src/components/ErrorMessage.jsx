function ErrorMessage({ message, onRetry }) {
  return (
    <section className="error-panel" role="alert">
      <div className="status-icon status-icon-error" aria-hidden="true">
        !
      </div>
      <div className="error-copy">
        <p className="eyebrow">Unable to analyze</p>
        <h2>Something needs your attention</h2>
        <p>{message}</p>
      </div>
      <button type="button" className="button button-secondary" onClick={onRetry}>
        Choose another file
      </button>
    </section>
  )
}

export default ErrorMessage
