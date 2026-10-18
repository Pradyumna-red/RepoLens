# RepoLens — Python Codebase Explorer

RepoLens is a web application that helps developers understand Python codebases by analyzing their structure, dependencies, and import relationships. Upload a ZIP file containing a Python project, and RepoLens will visualize the dependency graph and detect circular imports.

## Features

- 📦 Upload Python project ZIP files
- 🔍 Analyze import statements using Python AST
- 📊 Interactive dependency graph visualization
- 🔄 Circular import detection
- 🎯 Identify bottleneck modules

## Tech Stack

**Frontend:**
- React 18
- Vite
- React Flow (for graph visualization)

**Backend:**
- Python 3.8+
- FastAPI
- Pydantic

## Project Structure

```
RepoLens/
├── frontend/          # React application
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── backend/           # FastAPI application
│   ├── venv/          # Python virtual environment
│   ├── main.py
│   └── requirements.txt
├── docs/              # Documentation
├── plan.md            # Development plan
└── README.md          # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Install Python dependencies (when available):
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit: `http://localhost:5173`

## Running the Application

### Start Backend (Milestone 2+)
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

Backend will run on: `http://localhost:8000`

### Start Frontend
```bash
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:5173`

## Development Workflow

This project follows an 8-milestone development plan. See `plan.md` for detailed information about each milestone.

### Current Status: Milestone 1 ✅
- [x] Project structure created
- [x] Git repository initialized
- [x] Python virtual environment set up
- [x] Vite + React initialized
- [x] Basic documentation

### Next: Milestone 2
- [ ] FastAPI backend foundation
- [ ] Health check endpoint
- [ ] CORS configuration

## Testing

### Backend Tests (when implemented)
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
Manual testing for Version 1. Automated testing will be added in Version 2.

## Version 1 Scope

Version 1 focuses on core functionality:
- Upload and analyze Python ZIP files (max 50MB)
- Extract import statements using Python AST
- Build dependency graphs
- Detect circular imports
- Interactive visualization with React Flow

## Security

- File size limits (50MB max)
- ZIP file validation
- Path traversal prevention
- No code execution (analysis only via AST)

## Future Improvements (Version 2+)

- Function-level dependency analysis
- Dead code detection
- Code complexity metrics
- Multi-language support
- User accounts and saved analyses
- GitHub/GitLab integration

## Contributing

This is a learning project for BTech CSE students. Follow the milestone plan in `plan.md` for structured development.

## License

Educational project - feel free to use and modify.

---

Built with ❤️ as a full-stack learning project
