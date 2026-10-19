import React from 'react';

const CircularImports = ({ circularImports }) => {
  if (!circularImports || circularImports.length === 0) {
    return null;
  }

  return (
    <section className="circular-imports-panel">
      <div className="panel-header">
        <h3>Circular Import Warnings</h3>
        <p className="warning-count">
          {circularImports.length} circular import{circularImports.length === 1 ? '' : 's'} detected
        </p>
      </div>
      <div className="circular-imports-list">
        {circularImports.map((circular, index) => (
          <div key={index} className="circular-import-item">
            <div className="circular-description">
              {circular.description}
            </div>
            <div className="circular-cycle">
              <code>{circular.cycle.join(' → ')}</code>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default CircularImports;