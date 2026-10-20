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

  // Calculate dynamic node dimensions based on filename length
  const nodes = files.map((file, index) => {
    const isSelected = file.path === selectedPath
    const isConnected = selectedPath && (selectedTargets.has(file.path) || selectedSources.has(file.path))

    // Calculate dynamic dimensions for the node label
    const label = file.path;
    const maxWidth = 280; // Maximum width for very long paths
    const minWidth = 120; // Minimum width for readability
    const charWidth = 7.5; // Approximate width of a character in 10px monospace font
    const padding = 24; // Horizontal padding (12px each side)

    // Calculate width based on content, constrained by min/max
    const contentWidth = label.length * charWidth + padding;
    const width = Math.min(Math.max(contentWidth, minWidth), maxWidth);

    // Calculate height needed for wrapped text (assuming ~12px line height)
    const estimatedLines = Math.max(1, Math.ceil(contentWidth / maxWidth));
    const lineHeight = 12;
    const verticalPadding = 20; // Top and bottom padding
    const height = Math.min(Math.max(estimatedLines * lineHeight + verticalPadding, 40), 80); // Min 40px, max 80px

    // Use a simple grid layout but with more sophisticated spacing
    // We'll use columns based on average expected width to prevent overlap
    const column = index % 3;
    const row = Math.floor(index / 3);
    const baseX = column * (maxWidth + 30); // 30px gap between columns
    const baseY = row * (60 + 20); // Base row height + gap

    // Fine-tune positioning based on actual node width to center in column
    const offsetX = (maxWidth - width) / 2;
    const positionX = baseX + offsetX;
    const positionY = baseY;

    return {
      id: file.path,
      data: {
        label: file.path,
        imports: file.imports?.length || 0,
        importedBy: importedBy[file.path]?.length || 0,
        importCount: analysisData.import_counts?.[file.path] || file.import_count || 0,
      },
      position: { x: positionX, y: positionY },
      width: width,
      height: height,
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
