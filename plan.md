# RepoLens — Python Codebase Explorer

## 1. Project Overview

**What is RepoLens?**
RepoLens is a web application that helps developers understand Python codebases by analyzing their structure, dependencies, and import relationships. Users upload a ZIP file containing a Python project, and RepoLens visualizes how different modules connect to each other.

**Goals:**
- Make it easy to understand unfamiliar Python projects
- Identify problematic circular imports (when module A imports B, and B imports A)
- Visualize the dependency graph in an interactive way
- Help developers find bottleneck files (modules that many others depend on)

**User Workflow:**
1. User visits the React web application
2. User uploads a ZIP file containing a Python project
3. Backend extracts and analyzes the Python files using AST (Abstract Syntax Tree)
4. Backend builds a dependency graph and detects circular imports
5. Frontend displays the results: file list, dependency graph visualization, and circular import warnings
6. User can interact with the graph (zoom, pan, click nodes to see details)

---

## 2. Version 1 Features vs Future Improvements

### Version 1 (MVP - Minimum Viable Product)
✅ **We will build:**
- Upload ZIP files (max 50MB, Python files only)
- Extract and parse `.py` files
- Detect `import` and `from ... import` statements using Python AST
- Build a dependency graph (which module imports which)
- Detect circular imports
- Display results in a React dashboard with:
  - File list with basic stats
  - Interactive dependency graph using React Flow
  - Circular import warnings
- Basic error handling and security checks

### Future Improvements (Version 2+)
🔮 **Not building yet:**
- Function-level dependency analysis
- Dead code detection
- Code metrics (complexity, lines of code)
- Support for other languages (JavaScript, Java)
- User accounts and saved analyses
- Comparing multiple projects
- Export reports as PDF/JSON
- Real-time collaboration
- Integration with GitHub/GitLab APIs

---

## 3. Technology Choices (Simple Explanations)

### Frontend Technologies

**React**
- JavaScript library for building user interfaces
- We use components (reusable pieces of UI)
- Perfect for interactive dashboards

**Vite**
- Modern build tool that's faster than older tools like Create React App
- Provides instant server start and hot module replacement (changes show up immediately)

**React Flow**
- Library specifically for drawing node-based graphs
- We'll use it to show modules as nodes and imports as edges (arrows)

**JavaScript (not TypeScript)**
- Keeping it simple for Version 1
- No need to learn type annotations yet

### Backend Technologies

**Python**
- Same language we're analyzing, so we can use built-in tools
- Has an `ast` module (Abstract Syntax Tree) for parsing Python code

**FastAPI**
- Modern Python web framework
- Automatically generates API documentation
- Built-in validation with Pydantic
- Faster than Flask for this use case

**Pydantic**
- Data validation library
- Ensures uploaded data has the correct structure
- Works seamlessly with FastAPI

### Why Python AST?

**AST (Abstract Syntax Tree)** is a tree representation of code structure. Python's `ast` module lets us:
- Parse Python files without executing them (safe!)
- Extract import statements reliably
- Understand code structure programmatically

**Example:** For the code `import os`, AST sees it as:
```
Module(body=[Import(names=[alias(name='os')])])
```

### Why No Database?

For Version 1:
- Each analysis is independent (user uploads → analyze → show results)
- No need to store results long-term
- Keeps architecture simple
- Analysis data stays in memory during the request

---

## 4. Frontend Architecture

### Screens

**Screen 1: Upload Page**
- Hero section with project title
- Drag-and-drop zone for ZIP files
- Upload button
- File size limit warning (max 50MB)

**Screen 2: Analysis Loading**
- Progress indicator
- Status messages ("Extracting files...", "Analyzing imports...", "Building graph...")

**Screen 3: Results Dashboard**
- Header with project name and stats
- Left panel: File list with import counts
- Center: Interactive dependency graph
- Right panel: Circular import warnings and details
- "Analyze Another Project" button

### Component Structure

```
src/
├── App.jsx                    # Main app component, routing
├── main.jsx                   # Entry point
├── index.css                  # Global styles
│
├── components/
│   ├── UploadPage.jsx         # Screen 1: Upload interface
│   ├── LoadingScreen.jsx      # Screen 2: Analysis in progress
│   ├── Dashboard.jsx          # Screen 3: Results display
│   │
│   ├── FileList.jsx           # Left panel: list of Python files
│   ├── DependencyGraph.jsx    # Center: React Flow graph
│   ├── CircularImports.jsx    # Right panel: warnings
│   ├── StatsHeader.jsx        # Summary statistics bar
│   └── ErrorMessage.jsx       # Error display component
│
├── services/
│   └── api.js                 # API calls to backend
│
└── utils/
    └── graphUtils.js          # Helper functions for graph layout
```

**Component Responsibilities:**

- **App.jsx**: Manages overall state (uploaded, analyzing, results)
- **UploadPage.jsx**: Handles file selection, validation, upload
- **LoadingScreen.jsx**: Shows progress during analysis
- **Dashboard.jsx**: Container for all result components
- **FileList.jsx**: Displays files with import/imported-by counts
- **DependencyGraph.jsx**: Renders interactive graph with React Flow
- **CircularImports.jsx**: Lists circular dependency chains
- **api.js**: Centralized HTTP requests to FastAPI backend

---

## 5. Backend Architecture

### API Endpoints

#### **POST /api/analyze**
Upload and analyze a Python project ZIP file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (ZIP file)

**Response (Success - 200):**
```json
{
  "project_name": "my_project",
  "total_files": 15,
  "total_imports": 42,
  "files": [
    {
      "path": "src/main.py",
      "imports": ["utils", "config"],
      "imported_by": ["app"],
      "import_count": 2,
      "imported_by_count": 1
    }
  ],
  "dependencies": [
    {
      "source": "src/main.py",
      "target": "src/utils.py",
      "import_type": "import"
    }
  ],
  "circular_imports": [
    {
      "cycle": ["src/utils.py", "src/helpers.py", "src/utils.py"],
      "description": "utils.py → helpers.py → utils.py"
    }
  ]
}
```

**Response (Error - 400):**
```json
{
  "detail": "File size exceeds 50MB limit"
}
```

**Response (Error - 422):**
```json
{
  "detail": "Not a valid ZIP file"
}
```

#### **GET /api/health**
Health check endpoint.

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Backend Architecture Flow

```
Request → FastAPI Route → Validation → File Handler → Analyzer → Response

1. Route (main.py): Receives upload, validates file type/size
2. File Handler (file_handler.py): Extracts ZIP safely, filters Python files
3. Analyzer (analyzer.py): 
   - Parses files with AST
   - Extracts imports
   - Builds dependency graph
   - Detects cycles
4. Response: Returns JSON with analysis results
```

### Module Responsibilities

**main.py**
- Define FastAPI app
- Configure CORS (allow frontend to call backend)
- Define `/api/analyze` and `/api/health` routes
- Handle file upload

**models.py**
- Pydantic models for response structure
- `FileInfo`, `Dependency`, `CircularImport`, `AnalysisResult`

**file_handler.py**
- Extract ZIP to temporary directory
- Validate file paths (prevent path traversal attacks)
- Filter only `.py` files
- Clean up temporary files after analysis

**analyzer.py**
- Parse Python files using `ast` module
- Extract import statements
- Build dependency graph (dict/list structure)
- Detect circular imports using graph traversal

**security.py**
- Validate file size
- Check file extensions
- Sanitize file paths
- Prevent directory traversal

---

## 6. Project Folder Structure

```
RepoLens/
├── plan.md                          # This file
├── README.md                        # Setup instructions
├── .gitignore                       # Ignore venv, node_modules, etc.
│
├── frontend/                        # React application
│   ├── package.json                 # npm dependencies
│   ├── vite.config.js               # Vite configuration
│   ├── index.html                   # HTML entry point
│   ├── public/                      # Static assets
│   └── src/                         # Source code (see section 4)
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       ├── services/
│       └── utils/
│
├── backend/                         # Python FastAPI application
│   ├── requirements.txt             # Python dependencies
│   ├── main.py                      # FastAPI app entry point
│   ├── models.py                    # Pydantic models
│   ├── analyzer.py                  # AST parsing & graph building
│   ├── file_handler.py              # ZIP extraction & validation
│   ├── security.py                  # Security checks
│   └── tests/                       # Pytest tests
│       ├── test_analyzer.py
│       ├── test_file_handler.py
│       └── test_api.py
│
└── docs/                            # Documentation
    └── demo_project.zip             # Sample Python project for testing
```

**File Responsibilities Summary:**

| File | Purpose |
|------|---------|
| `frontend/src/App.jsx` | Main React component, state management |
| `frontend/src/services/api.js` | HTTP requests to backend |
| `backend/main.py` | FastAPI routes and app configuration |
| `backend/analyzer.py` | Core logic: AST parsing, graph building |
| `backend/file_handler.py` | ZIP extraction and file management |
| `backend/security.py` | Input validation and security checks |
| `backend/models.py` | Data structures for API responses |

---

## 7. Technical Deep Dive

### Understanding Python AST

**What is AST?**
Abstract Syntax Tree is a tree representation of code. Python's `ast` module parses source code into a tree structure we can analyze programmatically.

**Example Code:**
```python
import os
from pathlib import Path
import sys
```

**How We Extract This:**
```python
import ast

code = """
import os
from pathlib import Path
import sys
"""

tree = ast.parse(code)

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        # Regular import: import os
        for alias in node.names:
            print(f"Import: {alias.name}")
    
    elif isinstance(node, ast.ImportFrom):
        # From import: from pathlib import Path
        module = node.module  # "pathlib"
        print(f"From {module} import ...")
```

**Output:**
```
Import: os
From pathlib import ...
Import: sys
```

### Import Resolution Strategy

**Challenge:** Python imports can be relative or absolute.

```python
# Absolute import
import myproject.utils

# Relative import
from . import helpers
from .. import config
```

**Our Approach for Version 1:**
1. Extract the import string as-is
2. Resolve relative imports based on file location in the project
3. Map imports to actual file paths
4. Ignore imports to standard library (os, sys) and external packages (requests, numpy)

**Example Resolution:**

File: `src/services/api.py`
```python
from ..utils import helpers  # Relative import
```

Resolution:
- Current file: `src/services/api.py`
- `..` means parent directory: `src/`
- `utils` is a subdirectory: `src/utils/`
- Final path: `src/utils/helpers.py`

### Building the Dependency Graph

**Data Structure:**

We represent the graph as an adjacency list (dictionary):

```python
dependency_graph = {
    "src/main.py": ["src/utils.py", "src/config.py"],
    "src/utils.py": ["src/helpers.py"],
    "src/config.py": [],
    "src/helpers.py": ["src/utils.py"]  # This creates a cycle!
}
```

**Algorithm:**
1. For each Python file in the project:
   - Parse with AST
   - Extract all import statements
   - Resolve imports to file paths
   - Add edges to the graph

2. Store both directions:
   - `imports`: files this file imports
   - `imported_by`: files that import this file

### Detecting Circular Imports

**What is a Circular Import?**

A cycle in the dependency graph where:
- File A imports File B
- File B imports File C  
- File C imports File A

**Detection Algorithm (Depth-First Search):**

```python
def detect_cycles(graph):
    visited = set()
    recursion_stack = set()
    cycles = []
    
    def dfs(node, path):
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in recursion_stack:
                # Found a cycle!
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
        
        recursion_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles
```

**Example with Cycle:**

Files:
- `utils.py`: imports `helpers.py`
- `helpers.py`: imports `utils.py`

Graph:
```python
{
    "utils.py": ["helpers.py"],
    "helpers.py": ["utils.py"]
}
```

Detected cycle:
```python
["utils.py", "helpers.py", "utils.py"]
```

---

## 8. Development Roadmap (8 Milestones)

### Milestone 1: Project Setup & Environment

**What we build:**
- Project folder structure
- Python virtual environment
- Node.js project initialization
- Git repository
- Basic README

**Why first:**
- Foundation for everything else
- Ensures consistent development environment
- Allows team collaboration

**Prerequisites:**
- Python 3.8+ installed
- Node.js 16+ installed
- Git installed

**Steps:**
1. Create `RepoLens/` directory
2. Create `frontend/` and `backend/` subdirectories
3. Initialize Git: `git init`
4. Create Python venv: `python -m venv backend/venv`
5. Initialize npm: `cd frontend && npm create vite@latest . -- --template react`
6. Create `.gitignore` for Python and Node
7. Write basic README with setup instructions

**Expected Files:**
- `frontend/package.json`
- `backend/requirements.txt` (empty for now)
- `.gitignore`
- `README.md`

**Testing:**
- Activate venv: `source backend/venv/bin/activate` (Mac/Linux) or `backend\venv\Scripts\activate` (Windows)
- Install Vite: `cd frontend && npm install`
- Run Vite dev server: `npm run dev` (should see "Welcome to Vite + React")

**Completion Checklist:**
- [ ] Folder structure created
- [ ] Git initialized with first commit
- [ ] Python venv activated successfully
- [ ] Vite dev server runs on `localhost:5173`
- [ ] README documents setup steps

---

### Milestone 2: Backend Foundation (FastAPI + Health Endpoint)

**What we build:**
- Basic FastAPI application
- `/api/health` endpoint
- CORS configuration
- Development server script

**Why now:**
- Proves backend works before adding complexity
- Tests Python environment
- Establishes API pattern

**Prerequisites:**
- Milestone 1 complete
- Virtual environment activated

**Steps:**
1. Create `backend/main.py`
2. Add FastAPI, uvicorn, python-multipart to `requirements.txt`
3. Install dependencies: `pip install -r requirements.txt`
4. Implement basic FastAPI app with health endpoint
5. Configure CORS to allow frontend (localhost:5173)
6. Test with: `uvicorn main:app --reload`

**Expected Files:**
- `backend/main.py` (~30 lines)
- `backend/requirements.txt` (FastAPI, uvicorn, python-multipart)

**Testing:**
- Start server: `cd backend && uvicorn main:app --reload`
- Visit `http://localhost:8000/api/health` in browser
- Should see: `{"status": "ok", "version": "1.0.0"}`
- Check auto-generated docs: `http://localhost:8000/docs`

**Completion Checklist:**
- [ ] FastAPI app runs without errors
- [ ] Health endpoint returns 200 status
- [ ] Swagger docs accessible at `/docs`
- [ ] CORS configured for `localhost:5173`

---

### Milestone 3: File Upload & Security (Backend)

**What we build:**
- `POST /api/analyze` endpoint (stub version)
- File upload handling
- Security validation (file size, type, path traversal)
- Temporary file extraction
- `backend/security.py` and `backend/file_handler.py`

**Why now:**
- Security must be built in from the start, not added later
- File handling is complex and needs to work before analysis
- Tests our validation logic

**Prerequisites:**
- Milestone 2 complete
- Backend running

**Steps:**
1. Create `backend/security.py` with validation functions
2. Create `backend/file_handler.py` with ZIP extraction
3. Update `main.py` with `/api/analyze` endpoint
4. Implement file size limit check (50MB)
5. Validate file is a ZIP
6. Extract to temporary directory
7. Filter only `.py` files
8. Return list of Python files found (no analysis yet)

**Expected Files:**
- `backend/security.py` (~50 lines)
- `backend/file_handler.py` (~80 lines)
- `backend/main.py` (updated, ~100 lines)

**Testing:**
- Create a test ZIP with Python files
- Use curl or Postman to POST to `/api/analyze`
- Test security:
  - Upload file > 50MB (should reject)
  - Upload non-ZIP file (should reject)
  - Upload ZIP with path traversal attempts like `../../etc/passwd` (should sanitize)
- Verify response lists Python files

**Test Command:**
```bash
curl -X POST -F "file=@test_project.zip" http://localhost:8000/api/analyze
```

**Completion Checklist:**
- [ ] Upload accepts valid ZIP files
- [ ] Rejects files over 50MB
- [ ] Rejects non-ZIP files
- [ ] Sanitizes dangerous file paths
- [ ] Extracts only `.py` files
- [ ] Cleans up temporary directory after processing
- [ ] Returns list of found Python files

---

### Milestone 4: AST Parser & Import Extractor (Backend Core)

**What we build:**
- `backend/analyzer.py` with AST parsing
- Import extraction logic (both `import` and `from ... import`)
- Import resolution (relative to absolute paths)
- Unit tests for analyzer

**Why now:**
- This is the core of our application
- Needs to work before we can build graphs
- Isolated logic that we can test thoroughly

**Prerequisites:**
- Milestone 3 complete
- Sample Python projects for testing

**Steps:**
1. Create `backend/analyzer.py`
2. Implement `parse_imports(file_path)` using Python AST
3. Handle both `import x` and `from x import y`
4. Resolve relative imports (`.` and `..`)
5. Create `backend/tests/test_analyzer.py`
6. Test with various import patterns
7. Update `/api/analyze` to use analyzer

**Expected Files:**
- `backend/analyzer.py` (~120 lines)
- `backend/tests/test_analyzer.py` (~80 lines)

**Testing:**
Create test files:

**test_simple.py:**
```python
import os
import sys
from pathlib import Path
```

**test_relative.py:**
```python
from . import helpers
from .. import config
```

Run analyzer:
```python
python -m pytest backend/tests/test_analyzer.py -v
```

**Expected Output:**
```
test_analyzer.py::test_simple_imports PASSED
test_analyzer.py::test_relative_imports PASSED
test_analyzer.py::test_no_imports PASSED
```

**Completion Checklist:**
- [ ] Parses standard imports (`import os`)
- [ ] Parses from imports (`from x import y`)
- [ ] Handles relative imports (`.`, `..`)
- [ ] Ignores non-import statements
- [ ] All tests pass
- [ ] API returns imports for each file

---

### Milestone 5: Dependency Graph Builder

**What we build:**
- Graph building logic in `analyzer.py`
- Dependency mapping (file → imports)
- Reverse mapping (file → imported by)
- Pydantic models for structured responses

**Why now:**
- Depends on import extraction (Milestone 4)
- Needed before circular import detection
- Required for frontend visualization

**Prerequisites:**
- Milestone 4 complete
- Imports being extracted correctly

**Steps:**
1. Create `backend/models.py` with Pydantic models
2. Add `build_dependency_graph()` function to `analyzer.py`
3. Create adjacency list structure
4. Calculate import counts
5. Build reverse mappings (imported_by)
6. Update API response to match models
7. Add tests for graph building

**Expected Files:**
- `backend/models.py` (~60 lines)
- `backend/analyzer.py` (updated, ~200 lines)
- `backend/tests/test_graph.py` (~50 lines)

**Testing:**
Create test project:
```
test_project/
├── main.py        # imports utils, config
├── utils.py       # imports helpers
├── config.py      # no imports
└── helpers.py     # no imports
```

Run analyzer and check graph:
```python
Expected graph structure:
{
  "main.py": ["utils.py", "config.py"],
  "utils.py": ["helpers.py"],
  "config.py": [],
  "helpers.py": []
}

Expected reverse:
{
  "utils.py": ["main.py"],
  "config.py": ["main.py"],
  "helpers.py": ["utils.py"],
  "main.py": []
}
```

**Completion Checklist:**
- [ ] Graph structure built correctly
- [ ] Import counts calculated
- [ ] Reverse mappings (imported_by) work
- [ ] Pydantic models validate responses
- [ ] API returns complete graph data
- [ ] Tests pass for various project structures

---

### Milestone 6: Circular Import Detection

**What we build:**
- Cycle detection algorithm (DFS-based)
- Cycle formatting for display
- Integration with API response

**Why now:**
- Depends on dependency graph (Milestone 5)
- Core feature of the application
- Backend is now complete after this

**Prerequisites:**
- Milestone 5 complete
- Graph building working

**Steps:**
1. Add `detect_circular_imports()` to `analyzer.py`
2. Implement DFS with recursion stack
3. Find all cycles in the graph
4. Format cycles as readable chains
5. Add to API response
6. Create tests with known circular imports

**Expected Files:**
- `backend/analyzer.py` (updated, ~280 lines)
- `backend/tests/test_circular.py` (~60 lines)

**Testing:**
Create project with circular imports:

**a.py:**
```python
from . import b
```

**b.py:**
```python
from . import c
```

**c.py:**
```python
from . import a  # Creates cycle: a → b → c → a
```

Expected detection:
```json
{
  "circular_imports": [
    {
      "cycle": ["a.py", "b.py", "c.py", "a.py"],
      "description": "a.py → b.py → c.py → a.py"
    }
  ]
}
```

**Completion Checklist:**
- [ ] Detects simple cycles (A → B → A)
- [ ] Detects complex cycles (A → B → C → A)
- [ ] Handles graphs with no cycles
- [ ] Formats cycles readably
- [ ] API includes circular import data
- [ ] All tests pass

---

### Milestone 7: Frontend Upload & API Integration

**What we build:**
- Upload page UI
- File upload logic
- API service module
- Loading states
- Error handling

**Why now:**
- Backend is complete
- We can now build against real API
- Tests full end-to-end flow

**Prerequisites:**
- Milestones 1-6 complete
- Both frontend and backend running

**Steps:**
1. Create `frontend/src/services/api.js`
2. Implement `uploadProject(file)` function
3. Create `frontend/src/components/UploadPage.jsx`
4. Add drag-and-drop zone
5. Add file validation (size, type)
6. Show loading state during analysis
7. Handle errors and display messages
8. Update `App.jsx` to manage state

**Expected Files:**
- `frontend/src/services/api.js` (~40 lines)
- `frontend/src/components/UploadPage.jsx` (~120 lines)
- `frontend/src/components/LoadingScreen.jsx` (~30 lines)
- `frontend/src/components/ErrorMessage.jsx` (~20 lines)
- `frontend/src/App.jsx` (updated, ~100 lines)

**Testing:**
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Visit `localhost:5173`
4. Try uploading:
   - Valid ZIP → should show loading state
   - Large file → should show error
   - Non-ZIP → should show error
5. Check browser console for API responses

**Completion Checklist:**
- [ ] Upload page renders correctly
- [ ] Drag-and-drop works
- [ ] File validation works client-side
- [ ] Loading state shows during analysis
- [ ] API calls successfully reach backend
- [ ] Errors display properly
- [ ] Response data logged to console

---

### Milestone 8: Results Dashboard & Visualization

**What we build:**
- Dashboard layout
- File list component
- React Flow dependency graph
- Circular import warnings panel
- Complete user experience

**Why now:**
- Final piece to complete Version 1
- Makes all our backend work visible
- Delivers full user value

**Prerequisites:**
- Milestone 7 complete
- API returning full analysis data

**Steps:**
1. Install React Flow: `npm install reactflow`
2. Create `frontend/src/components/Dashboard.jsx`
3. Create `frontend/src/components/FileList.jsx`
4. Create `frontend/src/components/DependencyGraph.jsx`
5. Create `frontend/src/components/CircularImports.jsx`
6. Create `frontend/src/components/StatsHeader.jsx`
7. Transform API data to React Flow format
8. Add graph interactivity (zoom, pan, click)
9. Style components
10. Add "Analyze Another Project" button

**Expected Files:**
- `frontend/src/components/Dashboard.jsx` (~80 lines)
- `frontend/src/components/FileList.jsx` (~60 lines)
- `frontend/src/components/DependencyGraph.jsx` (~100 lines)
- `frontend/src/components/CircularImports.jsx` (~50 lines)
- `frontend/src/components/StatsHeader.jsx` (~40 lines)
- `frontend/src/utils/graphUtils.js` (~50 lines)
- `frontend/src/index.css` (updated)

**Testing:**
1. Upload a real Python project
2. Verify dashboard shows:
   - Correct file count
   - All Python files in list
   - Dependency graph with nodes and edges
   - Circular imports (if any)
3. Test interactions:
   - Click and drag graph
   - Zoom in/out
   - Click nodes to highlight
4. Test responsive layout
5. Click "Analyze Another Project"

**Graph Data Transformation Example:**
```javascript
// API response
const apiData = {
  files: [...],
  dependencies: [
    { source: "main.py", target: "utils.py" }
  ]
};

// React Flow format
const nodes = apiData.files.map(file => ({
  id: file.path,
  data: { label: file.path },
  position: { x: 0, y: 0 }  // Auto-layout
}));

const edges = apiData.dependencies.map((dep, i) => ({
  id: `e${i}`,
  source: dep.source,
  target: dep.target
}));
```

**Completion Checklist:**
- [ ] Dashboard displays all analysis data
- [ ] File list shows all Python files
- [ ] Dependency graph renders correctly
- [ ] Nodes and edges are visible
- [ ] Graph is interactive (pan, zoom)
- [ ] Circular imports display prominently
- [ ] Layout is responsive
- [ ] Can analyze multiple projects in sequence
- [ ] No console errors

---

## 9. Security Considerations

### ZIP Upload Security

**Risk:** Malicious ZIP files can exploit vulnerabilities.

**Mitigations:**
1. **File Size Limit:** Max 50MB to prevent resource exhaustion
2. **File Type Validation:** Check ZIP magic bytes, not just extension
3. **No Execution:** Never run uploaded code with `exec()` or `eval()`
4. **Temporary Isolation:** Extract to unique temporary directory

**Implementation:**
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file_size(file):
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset
    if size > MAX_FILE_SIZE:
        raise ValueError("File too large")
```

### Path Traversal Prevention

**Risk:** Malicious ZIP with paths like `../../etc/passwd` could access system files.

**Mitigations:**
1. Validate extracted paths stay within temp directory
2. Sanitize filenames
3. Use `os.path.abspath()` and `os.path.commonpath()`

**Implementation:**
```python
import os
from pathlib import Path

def is_safe_path(base_dir, file_path):
    """Ensure file_path is inside base_dir"""
    base = Path(base_dir).resolve()
    target = Path(base_dir, file_path).resolve()
    return base in target.parents or base == target
```

### Input Validation

**Risk:** Malformed data crashes the server.

**Mitigations:**
1. Use Pydantic for request/response validation
2. Catch and handle parsing exceptions
3. Return meaningful error messages

**Implementation:**
```python
from fastapi import HTTPException

@app.post("/api/analyze")
async def analyze(file: UploadFile):
    try:
        validate_file_size(file)
        validate_file_type(file)
        # ... process
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Analysis failed")
```

### Resource Limits

**Risk:** Large projects consume too much memory/CPU.

**Mitigations:**
1. Limit number of files analyzed (e.g., max 1000 Python files)
2. Timeout for long analyses (e.g., 60 seconds)
3. Clean up temp files immediately after analysis

### Never Execute Uploaded Code

**CRITICAL RULE:** We only *read and parse* Python files. We never:
- Use `exec()` or `eval()`
- Import uploaded modules
- Run uploaded scripts

We analyze code structure safely using AST.

---

## 10. Testing, Git, and Completion

### Testing Strategy

**Backend Tests (Pytest):**

```bash
cd backend
pytest tests/ -v --cov=.
```

**Test Coverage:**
- `test_analyzer.py`: Import extraction, graph building, cycles
- `test_file_handler.py`: ZIP extraction, path validation
- `test_security.py`: Size limits, file type checks
- `test_api.py`: API endpoints, error responses

**Sample Test:**
```python
def test_simple_import():
    code = "import os\nimport sys"
    imports = extract_imports(code)
    assert "os" in imports
    assert "sys" in imports
```

**Frontend Testing:**

For Version 1, manual testing:
1. Upload various ZIP files
2. Verify graph renders
3. Check error handling
4. Test on Chrome, Firefox

*Automated testing (Jest, React Testing Library) is a Version 2 improvement.*

### Git Workflow

**Branching:**
- `main`: Stable, working code
- `develop`: Integration branch
- `feature/milestone-X`: Feature branches

**Commit Messages:**
```
feat: add AST import extractor
fix: handle relative imports correctly
docs: update README with setup steps
```

**Workflow:**
1. Create feature branch: `git checkout -b feature/milestone-3`
2. Commit regularly with clear messages
3. Merge to `develop` after testing
4. Merge to `main` when milestone is complete

### README Contents

**Include:**
1. Project description
2. Features
3. Tech stack
4. Setup instructions (frontend + backend)
5. Running the application
6. Project structure
7. Development workflow
8. Testing
9. Known limitations
10. Future improvements

### Demo Preparation

**Create a demo Python project:**
```
demo_project/
├── app/
│   ├── main.py          # imports config, utils
│   ├── config.py        # imports helpers
│   └── utils.py         # imports helpers
├── helpers/
│   ├── __init__.py
│   └── formatting.py
└── tests/
    └── test_app.py      # imports app.main
```

**Add intentional circular import for demo:**
- `utils.py` imports `config.py`
- `config.py` imports `utils.py`

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| AST parsing fails on complex code | Can't analyze some files | Catch exceptions, skip problematic files, show warning |
| Large projects cause timeout | Poor user experience | Add file limit (max 1000 files) and timeout (60s) |
| Import resolution errors | Incomplete graph | Handle unresolved imports gracefully, show "external" label |
| React Flow performance with huge graphs | Slow rendering | Add node limit (max 500 nodes), offer filtered views |
| CORS issues in production | Frontend can't call backend | Document CORS configuration for deployment |
| Circular import false positives | User confusion | Verify cycle detection thoroughly, show clear examples |

### Version 1 Completion Checklist

**Functionality:**
- [ ] Users can upload ZIP files
- [ ] Backend extracts and analyzes Python files
- [ ] Imports are extracted correctly
- [ ] Dependency graph is built
- [ ] Circular imports are detected
- [ ] Dashboard displays results
- [ ] Graph is interactive

**Quality:**
- [ ] All backend tests pass
- [ ] No console errors in frontend
- [ ] Error messages are helpful
- [ ] Loading states are clear
- [ ] Security validations work

**Documentation:**
- [ ] README is complete
- [ ] Code has comments
- [ ] API endpoints are documented
- [ ] Setup instructions tested

**Polish:**
- [ ] UI is responsive
- [ ] Graph layout is readable
- [ ] File list is sortable/searchable
- [ ] "Analyze Another" workflow works

**Deployment Ready:**
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Backend requirements freeze (`pip freeze > requirements.txt`)
- [ ] Environment variables documented
- [ ] Demo video or screenshots captured

---

## Summary

RepoLens Version 1 is a focused, achievable project that teaches:
- Full-stack development (React + FastAPI)
- Python code analysis with AST
- Graph algorithms (dependency graphs, cycle detection)
- Security best practices
- Testing and git workflow

The 8 milestones build incrementally, with each step verifiable before moving forward. By following this plan, you'll have a working application that demonstrates real software engineering skills.

**Start with Milestone 1 (project setup), and work through each milestone sequentially. Each builds on the previous one.**

Good luck building RepoLens! 🚀
