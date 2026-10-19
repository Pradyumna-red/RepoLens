import { useState } from 'react'
import './App.css'
import ErrorMessage from './components/ErrorMessage'
import LoadingScreen from './components/LoadingScreen'
import UploadPage from './components/UploadPage'
import Dashboard from './components/Dashboard'
import { uploadProject } from './services/api'

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  )
}

function App() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!file || status === 'loading') return

    setError('')
    setStatus('loading')

    try {
      const response = await uploadProject(file)
      setResult(response)
      setStatus('success')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong. Please try again.')
      setStatus('error')
    }
  }

  function resetFlow() {
    setFile(null)
    setResult(null)
    setError('')
    setStatus('idle')
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="RepoLens home">
          <BrandMark />
          <span>Repo<span className="brand-accent">Lens</span></span>
        </a>
        <div className="header-meta">
          <span className="status-dot" aria-hidden="true" />
          <span>Private, local analysis</span>
        </div>
      </header>

      <main className="main-content">
        <div className="hero-copy">
          <p className="eyebrow">Understand your codebase</p>
          <h1>See the shape of your<br /><em>Python project.</em></h1>
          <p className="hero-description">
            Upload a repository and RepoLens will map its imports, dependencies, and architecture — in seconds.
          </p>
        </div>

        <div className={`flow-container${status === 'success' ? ' flow-container-dashboard' : ''}`}>
          {status === 'loading' && <LoadingScreen />}
          {status === 'success' && result && (
            <Dashboard result={result} onReset={resetFlow} />
          )}
          {status === 'error' && (
            <ErrorMessage message={error} onRetry={resetFlow} />
          )}
          {(status === 'idle' || status === 'ready') && (
            <UploadPage
              file={file}
              onFileSelected={(nextFile) => {
                setFile(nextFile)
                setStatus(nextFile ? 'ready' : 'idle')
                setError('')
              }}
              onRemove={resetFlow}
              onSubmit={handleSubmit}
              disabled={status === 'loading'}
            />
          )}
        </div>

        <p className="privacy-note">
          <span aria-hidden="true">✦</span> Source code is processed temporarily and never executed.
        </p>
      </main>

      <footer className="site-footer">
        <span>RepoLens <span className="footer-muted">/</span> Project intelligence for developers</span>
        <span className="footer-muted">Milestone 07</span>
      </footer>
    </div>
  )
}

export default App
