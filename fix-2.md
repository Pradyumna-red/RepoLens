# Fix 2: Circular Import Resolution

## Issue

RepoLens correctly extracted Python imports with the AST analyzer and correctly detected cycles when they were already present in the dependency graph. The failure occurred earlier, while converting imported module names into graph edges.

The supplied archive, `django-ecommerce-master-1.zip`, contains a common wrapper directory:

```text
django-ecommerce-master/
```

The relevant files were extracted as:

```text
django-ecommerce-master/djecommerce/urls.py
django-ecommerce-master/djecommerce/wsgi.py
```

However, the Python source imports used the actual project package names:

```python
# djecommerce/urls.py
from djecommerce.wsgi import application

# djecommerce/wsgi.py
from djecommerce.urls import urlpatterns
```

These imports form the cycle:

```text
djecommerce.urls -> djecommerce.wsgi -> djecommerce.urls
```

## Why the cycle was not detected

The graph builder used extracted, project-relative file paths to build module names. Before the fix, the files above were indexed using names equivalent to:

```text
django-ecommerce-master.djecommerce.urls
django-ecommerce-master.djecommerce.wsgi
```

The imports from the source code were indexed as:

```text
djecommerce.wsgi
djecommerce.urls
```

Because those names did not match, `resolve_import()` could not map either import to a project file. The imports were recorded as unresolved instead of becoming dependency-graph edges.

The resulting graph contained no edges for the two files:

```text
django-ecommerce-master/djecommerce/urls.py -> []
django-ecommerce-master/djecommerce/wsgi.py -> []
```

The circular-import detector only analyzes the dependency graph it receives. Since the two edges were missing before cycle detection began, the detector had no cycle to report. The problem was therefore archive-wrapper/module-root normalization, not the DFS cycle algorithm.

## Changes made

The minimal fix was implemented in `backend/analyzer.py` inside `build_dependency_graph()`:

1. Detect one common top-level wrapper directory when all Python files are beneath it.
2. Confirm that the wrapper is not itself a Python package by checking that it does not contain `__init__.py`.
3. Keep the wrapper in the returned graph node IDs, preserving API compatibility and existing file paths.
4. Add an additional import-resolution alias for the files below the wrapper, using their actual Python package names.
5. Resolve imports such as `djecommerce.urls`, `djecommerce.wsgi`, and `core.models` without treating `django-ecommerce-master` as a Python package.
6. Continue leaving standard-library, third-party, and other unresolved imports out of the project dependency graph.

The graph now preserves the original node IDs while resolving the imports correctly:

```text
django-ecommerce-master/djecommerce/urls.py -> django-ecommerce-master/djecommerce/wsgi.py
django-ecommerce-master/djecommerce/wsgi.py -> django-ecommerce-master/djecommerce/urls.py
```

## Tests added

Regression coverage was added for:

- A wrapped project containing the `djecommerce.urls` and `djecommerce.wsgi` cycle.
- API detection of the cycle in a wrapped ZIP archive.
- Unwrapped project imports.
- Existing direct imports.
- Existing relative imports.
- Existing package imports.
- Existing duplicate-import and syntax-error handling.

The existing ZIP security checks, upload-size limits, response models, and third-party dependency behavior were not changed.

## Verification

The real `django-ecommerce-master-1.zip` was submitted through the same endpoint used by the frontend:

```text
POST http://127.0.0.1:8000/api/analyze
```

Before the fix:

```json
{
  "total_files": 23,
  "total_imports": 58,
  "circular_imports": []
}
```

After the fix, the API returned HTTP 200 and reported:

```json
{
  "total_files": 23,
  "total_imports": 58,
  "circular_imports": [
    {
      "cycle": [
        "django-ecommerce-master/djecommerce/urls.py",
        "django-ecommerce-master/djecommerce/wsgi.py",
        "django-ecommerce-master/djecommerce/urls.py"
      ],
      "description": "django-ecommerce-master/djecommerce/urls.py → django-ecommerce-master/djecommerce/wsgi.py → django-ecommerce-master/djecommerce/urls.py"
    }
  ]
}
```

Validation results:

- Backend test suite: **62 passed**
- Frontend lint: **passed**
- Frontend production build: **passed**
- `git diff --check`: **passed**
- Real ZIP API verification: **HTTP 200; expected cycle detected**

No dependencies were added, the supplied ZIP was not modified, and no Git commit was created.

## Remaining limitations

The normalization intentionally handles one common non-package wrapper directory. Archives with multiple nested wrappers, unusual package layouts, namespace packages, or imports whose runtime behavior depends on custom import hooks may require additional import-resolution rules. Third-party and standard-library modules remain unresolved by design because RepoLens only creates graph edges for files contained in the uploaded project.
