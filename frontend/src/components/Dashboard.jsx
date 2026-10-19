import React, { useState } from 'react'
import StatsHeader from './StatsHeader'
import FileList from './FileList'
import DependencyGraph from './DependencyGraph'
import CircularImports from './CircularImports'

const Dashboard = ({ result, onReset }) => {
  const [selectedPath, setSelectedPath] = useState(null)

  if (!result) return null

  return (
    <section className="dashboard" aria-labelledby="dashboard-title">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">Analysis complete</p>
          <h2 id="dashboard-title">{result.project_name || 'Project'} at a glance</h2>
        </div>
        <button type="button" className="button button-secondary" onClick={onReset}>
          Analyze another project
        </button>
      </div>
      <StatsHeader result={result} />
      <div className="dashboard-content">
        <div className="dashboard-sidebar">
          <FileList
            files={result.files}
            importedBy={result.imported_by}
            selectedPath={selectedPath}
            onFileSelect={setSelectedPath}
          />
          <CircularImports circularImports={result.circular_imports} />
        </div>
        <div className="dashboard-main">
          <DependencyGraph
            result={result}
            selectedPath={selectedPath}
            onNodeSelect={setSelectedPath}
          />
        </div>
      </div>
    </section>
  )
}

export default Dashboard
