# Peblo TV Mini

A full-stack mini streaming platform implementing:

**CMS → FastAPI + PostgreSQL → Publish Job → Published Catalogue → Viewer**

Built for the Peblo Full-Stack Platform Engineer take-home challenge.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **CMS:** React + TypeScript + Vite
- **Viewer:** React + TypeScript + Vite
- **Storage:** Local filesystem behind a storage abstraction
- **Infrastructure:** Docker Compose, Nginx
- **Testing:** Pytest
- **CI:** GitHub Actions

## Run Locally

### Prerequisites

- Docker Desktop
- Docker Compose

### Start Everything with Docker

From the project root:

```powershell
cd D:\peblo-tv-mini
docker compose up --build
```

This starts PostgreSQL, the FastAPI backend, CMS, and Viewer together.

To run in the background:

```powershell
docker compose up --build -d
```

To stop the stack:

```powershell
docker compose down
```

To stop the stack and remove the database volume:

```powershell
docker compose down -v
```

To view running containers:

```powershell
docker compose ps
```

To view backend logs:

```powershell
docker compose logs -f backend
```

To view all logs:

```powershell
docker compose logs -f
```

Applications:

| Service | URL |
|---|---|
| CMS | http://localhost:5173 |
| Viewer | http://localhost:5174 |
| API / Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

The backend automatically runs Alembic migrations on startup.

### Run Backend Manually (Without Docker)

If PostgreSQL is already running locally and the Python virtual environment is configured:

```powershell
cd D:\peblo-tv-mini
.\.venv\Scripts\activate
cd backend
uvicorn app.main:app --reload --port 8000
```

Then open Swagger:

```text
http://localhost:8000/docs
```

Open ReDoc:

```text
http://localhost:8000/redoc
```

Check the health endpoint:

```text
http://localhost:8000/health
```

### Run CMS Manually

```powershell
cd D:\peblo-tv-mini\cms
npm install
npm run dev
```

CMS:

```text
http://localhost:5173
```

### Run Viewer Manually

```powershell
cd D:\peblo-tv-mini\viewer
npm install
npm run dev
```

Viewer:

```text
http://localhost:5174
```

### Run Backend Tests

With Docker:

```powershell
docker compose exec backend pytest
```

Without Docker:

```powershell
cd D:\peblo-tv-mini\backend
..\.venv\Scripts\activate
pytest
```

### Useful API Commands

Health check:

```powershell
curl http://localhost:8000/health
```

Get the published catalogue:

```powershell
curl http://localhost:8000/catalog
```

Get the validation report (requires an authenticated editor/admin token):

```text
GET http://localhost:8000/admin/validation-report
```

Publish the catalogue (requires an authenticated admin token):

```text
POST http://localhost:8000/admin/catalog/publish
```

Swagger provides an interactive way to authenticate and test all API endpoints.

### Development Credentials

**Admin**

```text
Email:    admin@peblo.local
Password: admin12345
```

**Editor**

```text
Email:    editor@peblo.local
Password: editor12345
```

These credentials are for local development only. Production credentials and secrets should be supplied through a secret manager or deployment environment.

## Architecture

```text
                    ┌──────────────────┐
                    │    CMS (React)   │
                    │   :5173          │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ FastAPI Backend  │
                    │      :8000       │
                    └───────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────────┐   ┌────────────────────┐
        │   PostgreSQL    │   │ Published Catalogue│
        │     :5433       │   │  catalogue.json   │
        └─────────────────┘   └─────────┬──────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │ Viewer (React)  │
                               │     :5174       │
                               └─────────────────┘
```

The CMS uses authenticated admin APIs for content management. The viewer reads only the published catalogue APIs and does not use admin endpoints.

## Core Features

### Content Management

- Show, season, and episode CRUD
- Search, filters, and pagination
- Episode language variants
- Server-side validation
- Draft/published content states
- Editor/admin role separation

### Artwork

Three artwork types are supported:

| Type | Required dimensions |
|---|---:|
| Poster | 600 × 900 |
| Banner | 1280 × 720 |
| Thumbnail | 640 × 360 |

The backend validates dimensions/aspect ratio and enforces the **200 KB** file-size ceiling before accepting artwork.

Validation errors are returned in editor-readable terms.

### Catalogue Publishing

`POST /admin/catalog/publish`

Publishing:

- Includes only published shows and episodes
- Groups language variants using `content_group`
- Produces a single catalogue episode entry with available languages
- Groups content by section
- Uses deterministic ordering
- Records publish runs with trigger information, counts, and outcome
- Writes the catalogue atomically

### Viewer

The viewer is a separate React application that reads the published catalogue.

It provides:

- Netflix-style featured hero
- Horizontal content rows by section
- Search
- Category and language filters
- Show detail pages
- Seasons and episodes
- Episode language options
- Episode durations
- Separate trailer handling for Season 0
- Image loading fallbacks and empty states

## Atomic Publishing

The publisher builds the complete catalogue before replacing the live file.

The process is:

1. Build the catalogue from the database.
2. Write the complete result to a temporary file.
3. Flush and `fsync` the temporary file.
4. Atomically replace the existing catalogue using `os.replace()`.

A reader therefore sees either the previous complete catalogue or the newly published complete catalogue.

If the process dies before the final replacement, the existing live catalogue remains unchanged. A failed publish is recorded as an unsuccessful `PublishRun` where the failure occurs.

This avoids the unsafe pattern of directly overwriting the live catalogue while it is being read.

## Storage Abstraction

The development implementation stores files on local disk under the backend storage directory.

Storage access is kept behind application storage/service code so the API and catalogue-building logic are not tied directly to local filesystem operations.

For production, the storage implementation can be replaced with a Cloudflare R2/S3-compatible implementation. The main change would be the storage adapter and its configuration; the content and publishing logic would remain the same.

## Search & Scaling

Viewer search is performed against the published catalogue and supports:

```text
q
category
language
section
```

The filters are composable. The query matches show titles, episode titles, and categories.

This implementation is intentionally suitable for the small catalogue used by this take-home.

At significantly larger catalogue sizes, repeatedly loading and scanning a JSON document would become inefficient in latency and memory usage. The next step would be an indexed read/search model, such as PostgreSQL full-text/search indexes or a dedicated search service, while keeping the published catalogue as a stable viewer-facing snapshot.

## Why a Pre-Published Catalogue?

The viewer is a read-heavy surface. A pre-built catalogue avoids executing joins and content transformations across the editorial database for every viewer request.

It also provides a deterministic snapshot: CMS edits become visible to viewers only after a successful publish.

The trade-off is freshness. A content change is not immediately visible to viewers until publishing succeeds. This is intentional because publishing acts as the content release boundary.

## Validation & Business Rules

Validation is enforced by the backend rather than relying only on the CMS.

Important rules include:

- An episode cannot be published without artwork.
- An episode cannot be published without a duration.
- `(content_group, language)` must be unique.
- A published show must have a section.
- Artwork dimensions and file size must be valid.
- Season 0 is reserved for trailers.
- Language variants sharing a `content_group` collapse into one catalogue entry.

`GET /admin/validation-report` exposes current publish-blocking issues so editors can resolve them without needing engineering assistance.

## Authentication & RBAC

Two roles are enforced by backend authorization:

| Role | CRUD | Publish |
|---|---:|---:|
| Editor | Yes | No |
| Admin | Yes | Yes |

The CMS hides unavailable actions for usability, but authorization is independently enforced by the API.

## Tests

Tests focus on higher-risk backend behavior such as:

- Validation rules
- Catalogue publishing
- Language grouping
- API authorization/RBAC
- Publish behavior

Run the test suite with:

```bash
docker compose exec backend pytest
```

## CI / Deployment

GitHub Actions is used for the project's quality gates, including linting, tests, and Docker image builds.

The deployment step is documented rather than tied to a real cloud environment. A production deployment would:

1. Build immutable container images.
2. Push them to a container registry.
3. Inject environment variables/secrets through the deployment platform.
4. Run database migrations as a controlled release step.
5. Deploy API, CMS, and Viewer behind a reverse proxy.
6. Monitor the health endpoint and service-level failures.

## Environment & Secrets

`.env.example` documents the environment variables required by the application.

For production, secrets such as:

- Database credentials
- Authentication secret
- Admin credentials
- Storage credentials

should be stored in the deployment platform's secret manager rather than committed to Git.

## Health & Alerting

The backend exposes:

```text
GET /health
```

which provides a basic service health check.

A production alert should be triggered when the backend health check fails continuously, because this indicates that the API—and therefore CMS and viewer catalogue access—is unavailable.

Publish failures should also be monitored because a failed publish can prevent approved content from reaching viewers even while the API itself remains healthy.

## Known Scope / Omissions

The challenge includes optional stretch features such as catalogue versioning with rollback, publish dry-run/diff, and a detailed audit log.

These were intentionally not prioritized over the core workflow. The implementation focuses on the required end-to-end path:

**content management → validation → publish → published catalogue → viewer browse/search**

The supplied seed data is deliberately imperfect. Invalid content is surfaced by validation rather than weakening the rules just to force a successful publish.

## AI Usage

AI was used as an implementation and debugging assistant for scaffolding, troubleshooting, code review, and exploring implementation approaches.

Generated suggestions were reviewed and tested rather than accepted blindly. In particular, validation rules, RBAC enforcement, database constraints, language grouping, atomic publishing, and Docker behavior were verified against the challenge requirements and local execution.

## Time / Scope

The implementation was developed with priority on the highest-value challenge areas:

1. Data model and migrations
2. Authentication and RBAC
3. CRUD and server-side validation
4. Artwork upload and validation
5. Atomic catalogue publishing
6. CMS workflow
7. Viewer browse/search/detail experience
8. Docker Compose
9. Tests and CI
