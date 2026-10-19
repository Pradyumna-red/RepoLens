import React from 'react'

const FileList = ({ files, importedBy, selectedPath, onFileSelect }) => {
  if (!files || files.length === 0) {
    return (
      <div className="file-list-empty">
        <p>No Python files found in the uploaded project.</p>
      </div>
    )
  }

  return (
    <section className="file-list-panel" aria-labelledby="file-list-title">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Source map</p>
          <h3 id="file-list-title">Python files</h3>
        </div>
        <p className="file-count">{files.length} files</p>
      </div>
      <div className="file-list-content">
        {files.map((file) => {
          const isSelected = file.path === selectedPath
          return (
            <button
              type="button"
              key={file.path}
              className={`file-item${isSelected ? ' file-item-selected' : ''}`}
              onClick={() => onFileSelect?.(file.path)}
              aria-pressed={isSelected}
            >
              <span className="file-info">
                <span className="file-name">
                  <strong>{file.name}</strong>
                  <span className="file-path">{file.path}</span>
                </span>
                <span className="file-stats">
                  <span className="stat">
                    <span className="stat-label">Imports</span>
                    <span className="stat-value">{file.imports?.length || 0}</span>
                  </span>
                  <span className="stat">
                    <span className="stat-label">Imported by</span>
                    <span className="stat-value">{importedBy?.[file.path]?.length || 0}</span>
                  </span>
                </span>
              </span>
            </button>
          )
        })}
      </div>
    </section>
  )
}

export default FileList
