import { useState } from 'react'

const MAX_FILE_SIZE = 50 * 1024 * 1024

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function validateFile(file) {
  if (!file) {
    return 'Choose a ZIP file to begin.'
  }

  if (!file.name.toLowerCase().endsWith('.zip')) {
    return 'RepoLens accepts ZIP files only.'
  }

  if (file.size > MAX_FILE_SIZE) {
    return 'That ZIP is larger than the 50 MB upload limit.'
  }

  return ''
}

function ZipIcon() {
  return (
    <svg className="zip-icon" viewBox="0 0 48 48" aria-hidden="true">
      <path d="M13 4h16l8 8v31H13z" />
      <path d="M29 4v9h8M21 4v6m0 5v6m0 5v6m0 5v6" />
      <path d="M19 10h4m-4 10h4m-4 10h4" />
    </svg>
  )
}

function UploadPage({ file, onFileSelected, onRemove, onSubmit, disabled = false }) {
  const [isDragging, setIsDragging] = useState(false)
  const [validationMessage, setValidationMessage] = useState('')
  const inputId = 'project-archive'

  function acceptFile(nextFile) {
    const message = validateFile(nextFile)
    setValidationMessage(message)
    if (!message) {
      onFileSelected(nextFile)
    } else {
      onFileSelected(null)
    }
  }

  function handleInputChange(event) {
    acceptFile(event.target.files?.[0] || null)
    event.target.value = ''
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)
    if (!disabled) {
      acceptFile(event.dataTransfer.files?.[0] || null)
    }
  }

  function handleDragOver(event) {
    event.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  function handleDragLeave(event) {
    if (!event.currentTarget.contains(event.relatedTarget)) {
      setIsDragging(false)
    }
  }

  function handleRemove() {
    setValidationMessage('')
    onRemove()
  }

  return (
    <section className="upload-card" aria-labelledby="upload-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Start with your repository</p>
          <h2 id="upload-title">Upload a project archive</h2>
        </div>
        <span className="limit-chip">ZIP · max 50 MB</span>
      </div>

      <div
        className={`drop-zone ${isDragging ? 'drop-zone-active' : ''} ${file ? 'drop-zone-selected' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          id={inputId}
          className="file-input"
          type="file"
          accept=".zip,application/zip"
          onChange={handleInputChange}
          disabled={disabled}
        />

        {file ? (
          <div className="selected-file">
            <div className="file-icon-wrap"><ZipIcon /></div>
            <div className="file-details">
              <strong>{file.name}</strong>
              <span>{formatFileSize(file.size)} · Ready to analyze</span>
            </div>
            <button
              type="button"
              className="text-button"
              onClick={handleRemove}
              disabled={disabled}
              aria-label={`Remove ${file.name}`}
            >
              Remove
            </button>
          </div>
        ) : (
          <label className="drop-zone-content" htmlFor={inputId}>
            <div className="file-icon-wrap"><ZipIcon /></div>
            <strong>Drop your ZIP file here</strong>
            <span>or <span className="browse-link">browse from your computer</span></span>
            <small>We’ll inspect the source safely without executing it.</small>
          </label>
        )}
      </div>

      <div className="upload-actions">
        {validationMessage ? (
          <p className="validation-message" role="status">{validationMessage}</p>
        ) : (
          <p className="helper-text">Your archive stays within this analysis session.</p>
        )}
        <button
          type="button"
          className="button button-primary"
          onClick={onSubmit}
          disabled={!file || disabled || Boolean(validationMessage)}
        >
          Analyze project
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </section>
  )
}

export default UploadPage
