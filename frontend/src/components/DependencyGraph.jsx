import React, { useMemo } from 'react'
import { Background, Controls, MiniMap, ReactFlow } from 'reactflow'
import 'reactflow/dist/style.css'
import { transformToReactFlow } from '../utils/graphUtils'

const DependencyGraph = ({ result, selectedPath, onNodeSelect }) => {
  const { nodes, edges } = useMemo(
    () => transformToReactFlow(result, selectedPath),
    [result, selectedPath],
  )

  return (
    <section className="dependency-graph-panel" aria-labelledby="dependency-graph-title">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">Architecture view</p>
          <h3 id="dependency-graph-title">Dependency graph</h3>
        </div>
        <p className="graph-info">{nodes.length} files <span aria-hidden="true">•</span> {edges.length} links</p>
      </div>
      <div className="react-flow-wrapper">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          onNodeClick={(_event, node) => onNodeSelect?.(node.id)}
          onPaneClick={() => onNodeSelect?.(null)}
          minZoom={0.45}
          maxZoom={2}
          nodesConnectable={false}
          elementsSelectable
        >
          <Background color="#323852" gap={24} size={1} />
          <Controls />
          <MiniMap nodeColor={(node) => node.className?.includes('selected') ? '#b4aaff' : '#6357c8'} />
        </ReactFlow>
      </div>
      <p className="graph-hint">Select a file to highlight its direct dependencies.</p>
    </section>
  )
}

export default DependencyGraph
