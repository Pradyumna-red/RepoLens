import React from 'react';

const StatsHeader = ({ result }) => {
  if (!result) return null;

  const { project_name: projectName, total_files, total_imports } = result;

  return (
    <section className="stats-header">
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-label">Project</span>
          <strong className="stat-value">{projectName}</strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">Python Files</span>
          <strong className="stat-value">{total_files?.toLocaleString() ?? 0}</strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">Total Imports</span>
          <strong className="stat-value">{total_imports?.toLocaleString() ?? 0}</strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">Circular Imports</span>
          <strong className="stat-value">
            {result.circular_imports?.length ?? 0}
          </strong>
        </div>
      </div>
    </section>
  );
};

export default StatsHeader;