/**
 * Transform the backend adjacency-list response into React Flow data.
 */
export const transformToReactFlow = (analysisData, selectedPath = null) => {
  const files = analysisData?.files || []
  const importedBy = analysisData?.imported_by || {}
  const dependencyGraph = analysisData?.dependency_graph || {}
  const selectedTargets = new Set(dependencyGraph[selectedPath] || [])
  const selectedSources = new Set(
    Object.entries(dependencyGraph)
      .filter(([, targets]) => targets.includes(selectedPath))
      .map(([source]) => source),
  )

  const nodes = files.map((file, index) => {
    const column = index % 3
    const row = Math.floor(index / 3)
    const isSelected = file.path === selectedPath
    const isConnected = selectedPath && (selectedTargets.has(file.path) || selectedSources.has(file.path))

    return {
      id: file.path,
      data: {
        label: file.path,
        imports: file.imports?.length || 0,
        importedBy: importedBy[file.path]?.length || 0,
        importCount: analysisData.import_counts?.[file.path] || file.import_count || 0,
      },
      position: { x: column * 250, y: row * 140 },
      className: isSelected ? 'graph-node-selected' : isConnected ? 'graph-node-connected' : '',
    }
  })

  const edges = Object.entries(dependencyGraph).flatMap(([source, targets]) =>
    targets.map((target, index) => {
      const isHighlighted = selectedPath && (source === selectedPath || target === selectedPath)
      return {
        id: `e-${source}-${target}-${index}`,
        source,
        target,
        type: 'smoothstep',
        className: isHighlighted ? 'graph-edge-highlighted' : '',
        animated: Boolean(isHighlighted),
      }
    }),
  )

  return { nodes, edges }
}

export const getFileDetails = (filePath, analysisData) => {
  const file = analysisData?.files?.find((candidate) => candidate.path === filePath)
  if (!file) return null

  return {
    path: file.path,
    name: file.name,
    imports: file.imports || [],
    importedBy: analysisData.imported_by?.[file.path] || [],
    importCount: analysisData.import_counts?.[file.path] || file.import_count || 0,
    importedByCount: analysisData.imported_by?.[file.path]?.length || 0,
  }
}
