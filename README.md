# Synapse - Open Source AI Research Assistant

<p align="center">
  <img src="logo.png" alt="Synapse Logo" width="200"/>
</p>

<p align="center">
  <a href="https://github.com/Malaybhai11/synapse/releases">
    <img src="https://img.shields.io/github/v/release/Malaybhai11/synapse?style=flat-square" alt="Version"/>
  </a>
  <a href="https://github.com/Malaybhai11/synapse/stargazers">
    <img src="https://img.shields.io/github/stars/Malaybhai11/synapse?style=flat-square" alt="Stars"/>
  </a>
  <a href="https://github.com/Malaybhai11/synapse/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Malaybhai11/synapse?style=flat-square" alt="License"/>
  </a>
  <a href="https://discord.gg/37XJPXfz2w">
    <img src="https://img.shields.io/discord/37XJPXfz2w?style=flat-square" alt="Discord"/>
  </a>
  <a href="https://github.com/Malaybhai11/synapse/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/Malaybhai11/synapse/main.yml?style=flat-square" alt="Build"/>
  </a>
</p>

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Code Quality](#code-quality)
4. [Libraries & Dependencies](#libraries--dependencies)
5. [Version Decisions](#version-decisions)
6. [Architecture Analysis](#architecture-analysis)
7. [Component Reference](#component-reference)
8. [Installation](#installation)
9. [Configuration](#configuration)
10. [Development](#development)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [Security](#security)
14. [License](#license)

---

## Project Overview

Synapse is an open-source, privacy-focused alternative to Google's Notebook LM. It serves as an AI-powered research assistant enabling users to:

- **Upload multi-modal content**: PDFs, audio, video, web pages
- **Generate intelligent notes**: AI-powered note-taking and insight extraction
- **Search semantically**: Vector-based semantic search across all content
- **Chat with AI models**: Conversational AI with full context awareness
- **Produce professional podcasts**: Generate audio podcasts from content

### Key Values

| Value | Description |
|-------|-------------|
| **Privacy-first** | Complete control over your data |
| **Multi-provider AI** | Support for 13+ AI providers |
| **Fully self-hosted** | Run entirely on your infrastructure |
| **Open-source transparency** | Full code visibility |

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Next.js)                    │
│              frontend/ @ port 3000                       │
├─────────────────────────────────────────────────────────┤
│ - Notebooks, sources, notes, chat, podcasts, search UI    │
│ - Zustand state management, TanStack Query (React Query)│
│ - Shadcn/ui component library with Tailwind CSS          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI)                               │
│              api/ @ port 5055                           │
├─────────────────────────────────────────────────────────┤
│ - REST endpoints for notebooks, sources, notes, chat       │
│ - LangGraph workflow orchestration                     │
│ - Job queue for async operations (podcasts)               │
│ - Multi-provider AI provisioning via Esperanto          │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                           │
│         Graph database @ port 8000                     │
├─────────────────────────────────────────────────────────┤
│ - Records: Notebook, Source, Note, ChatSession, Credential│
│ - Relationships: source-to-notebook, note-to-source    │
│ - Vector embeddings for semantic search               │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend Tech Stack

| Technology | Version | Purpose | Why Used |
|------------|----------|---------|----------|
| **Next.js** | 16.1.5 | React framework with App Router | Most popular React framework, excellent SEO, server-side rendering, built-in routing |
| **React** | 19.2.3 | UI library | Industry standard, huge ecosystem |
| **TypeScript** | 5.x | Type safety | Catches errors at compile time, better DX |
| **Zustand** | 5.0.6 | State management | Lightweight, simple API, great performance |
| **TanStack Query** | 5.83.0 | Data fetching/caching | Industry standard for server state management |
| **Tailwind CSS** | 4.x | Styling | Utility-first, highly customizable |
| **Shadcn/ui** | Latest | Component library | Accessible, composable, no runtime overhead |
| **Radix UI** | Latest | Primitives | Headless, accessible component primitives |
| **i18next** | 25.7.3 | Internationalization | Most popular React i18n solution |
| **Lucide React** | 0.525.0 | Icons | Clean, consistent icon set |
| **Axios** | 1.13.5 | HTTP client | Predictable API, interceptors |
| **Zod** | 4.0.5 | Schema validation | TypeScript-native, composable |
| **React Hook Form** | 7.60.0 | Form handling | Performance, validation integration |
| **Sonner** | 2.0.6 | Toast notifications | Lightweight, beautiful |
| **Vitest** | 3.0.0 | Testing | Fast, Vite-integrated |
| **ESLint** | 9.x | Linting | Code quality |

### Backend Tech Stack

| Technology | Version | Purpose | Why Used |
|------------|----------|---------|----------|
| **Python** | 3.12 | Language | Excellent AI/ML ecosystem, async support |
| **FastAPI** | 0.104+ | Web framework | Fast, async native, automatic docs |
| **Uvicorn** | 0.24+ | ASGI server | Fast, async-native, standard |
| **Pydantic** | 2.9+ | Data validation | Type-safe, automatic validation |
| **LangGraph** | 1.0+ | Workflow orchestration | State machines for AI workflows |
| **LangChain** | 1.2+ | AI integration | Unified AI provider interface |
| **SurrealDB** | 1.0.4+ | Database | Graph DB, built-in vectors, async |
| **Esperanto** | Latest | AI provider abstraction | 13+ providers unified |
| **Loguru** | 0.7+ | Logging | Simpler than logging stdlib |
| **Tiktoken** | 0.12+ | Token counting | OpenAI encoding compatibility |

### Database Tech Stack

| Technology | Version | Purpose | Why Used |
|------------|----------|---------|----------|
| **SurrealDB** | 2.x | Graph database | Native graph, vectors, async, embedded |

### DevOps Tech Stack

| Technology | Purpose | Why Used |
|------------|---------|----------|
| **Docker** | Containerization | Industry standard |
| **Docker Compose** | Orchestration | Simple multi-container setup |
| **UV** | Package manager | Extremely fast Python package manager |
| **Supervisord** | Process management | Multi-process container management |

---

## Tools & Technologies (Complete List)

This section provides a comprehensive listing of ALL tools, technologies, platforms, and services used in Synapse.

### Development Tools

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **Python** | 3.12 | Backend language | Excellent AI/ML ecosystem, async support |
| **Node.js** | 20.x | Frontend runtime | Next.js requirement |
| **UV** | Latest | Python package manager | 10-100x faster than pip |
| **NPM** | Latest | Frontend package manager | Industry standard |
| **Git** | - | Version control | Code collaboration |

### Code Quality & Linting Tools

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **Ruff** | >=0.5.5 | Python linting | 10-100x faster than flake8 |
| **MyPy** | >=1.11.1 | Python type checking | Catch errors at compile time |
| **ESLint** | 9.x | JavaScript linting | Code quality |
| **Pre-commit** | >=4.0.1 | Git hooks | Automated checks |
| **Vitest** | 3.0.0 | Frontend testing | Fast, Vite-integrated |
| **Pytest** | >=8.0.0 | Backend testing | Industry standard |

### Frontend Tools & Libraries

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **Next.js** | 16.1.5 | React framework | SEO, SSR, routing |
| **React** | 19.2.3 | UI library | Industry standard |
| **TypeScript** | 5.x | Type safety | Better DX |
| **Vite** | Latest | Build tool | Fast builds |
| **Tailwind CSS** | 4.x | Styling | Utility-first |
| **Radix UI** | Latest | Headless components | Accessibility |
| **Shadcn/ui** | Latest | Component library | Composable |
| **Zustand** | 5.0.6 | State management | Lightweight |
| **TanStack Query** | 5.83.0 | Data fetching | Server state |
| **Axios** | 1.13.5 | HTTP client | Predictable API |
| **Zod** | 4.0.5 | Validation | TypeScript-native |
| **React Hook Form** | 7.60.0 | Forms | Performance |
| **Sonner** | 2.0.6 | Toasts | Lightweight |
| **i18next** | 25.7.3 | i18n | Most popular |
| **date-fns** | 4.1.0 | Date utilities | Lightweight |
| **Lucide React** | 0.525.0 | Icons | Consistent |
| **cmdk** | 1.1.1 | Command palette | Keyboard navigation |
| **@tailwindcss/typography** | 0.5.16 | Prose styling | Markdown rendering |
| **react-markdown** | 10.1.0 | Markdown rendering | Full features |
| **remark-gfm** | 4.0.1 | GitHub Flavored MD | Tables, etc |
| **@monaco-editor/react** | 4.7.0 | Code editor | VS Code editor |

### Backend Tools & Libraries

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **FastAPI** | >=0.104.0 | Web framework | Fast, async-native |
| **Uvicorn** | >=0.24.0 | ASGI server | Standard |
| **Pydantic** | >=2.9.2 | Validation | Type-safe |
| **Loguru** | >=0.7.2 | Logging | Simpler than stdlib |
| **LangChain** | >=1.2.0 | AI integration | Unified API |
| **LangGraph** | >=1.0.5 | Workflows | State machines |
| **LangChain Community** | >=0.4.1 | Community integrations | Extended providers |
| **LangChain OpenAI** | >=1.1.6 | OpenAI integration | GPT models |
| **LangChain Anthropic** | >=1.3.0 | Anthropic integration | Claude models |
| **LangChain Ollama** | >=1.0.1 | Ollama integration | Local models |
| **LangChain Google GenAI** | >=4.1.2 | Google integration | Gemini |
| **LangChain Groq** | >=1.1.1 | Groq integration | Fast inference |
| **LangChain Mistral** | >=1.1.1 | Mistral integration | Mistral models |
| **LangChain DeepSeek** | >=1.0.0 | DeepSeek integration | DeepSeek Chat |
| **Tiktoken** | >=0.12.0 | Token counting | OpenAI encoding |
| **LangGraph Checkpoint SQLite** | >=3.0.1 | State persistence | LangGraph persistence |

### Database & Storage

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **SurrealDB** | 2.x | Graph database | Native graph + vectors |
| **SQLite** | - | Checkpoint storage | LangGraph state |

### AI Provider Libraries

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **Esperanto** | >=2.19.3 | AI provider abstraction | 13+ providers unified |
| **content-core** | >=1.14.1 | Content extraction | 50+ file types |
| **ai-prompter** | >=0.3 | Prompt templating | Jinja2 templates |
| **podcast-creator** | >=0.11.2 | Podcast generation | TTS + audio |
| **surreal-commands** | >=1.3.1 | Async job queue | Background jobs |

### Middleware & Utilities

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **httpx** | >=0.27.0 | HTTP client | Async HTTP |
| **python-dotenv** | >=1.0.1 | Environment variables | Config management |
| **tomli** | >=2.0.2 | TOML parsing | Config files |
| **numpy** | >=2.4.1 | Numerical computing | Mean pooling |
| **pycountry** | >=26.2.16 | Country data | Localization |
| **babel** | >=2.18.0 | Internationalization | i18n utilities |
| **duckduckgo-search** | >=5.0.0 | Web search | Research tool |

### Frontend i18n Languages

| Language Code | Language | Status |
|------------|----------|--------|
| **en-US** | English (United States) | Primary |
| **pt-BR** | Portuguese (Brazil) | Supported |
| **zh-CN** | Chinese (Simplified) | Supported |
| **zh-TW** | Chinese (Traditional) | Supported |
| **ja-JP** | Japanese | Supported |
| **ru-RU** | Russian | Supported |

### Docker & Deployment Tools

| Tool | Purpose | Why Used |
|------|---------|----------|
| **Docker** | Container runtime | Industry standard |
| **Docker Compose** | Container orchestration | Multi-service |
| **Supervisord** | Process manager | Multi-process in container |
| **ffmpeg** | Audio processing | Podcast generation |

### Testing Tools

| Tool | Version | Purpose | Why Used |
|------|---------|---------|----------|
| **Pytest** | >=8.0.0 | Backend testing | Industry standard |
| **Pytest Asyncio** | >=1.2.0 | Async testing | pytest plugin |
| **Vitest** | 3.0.0 | Frontend testing | Fast |
| **@testing-library/react** | >=16.2.0 | React testing | DOM testing |
| **@testing-library/jest-dom** | >=6.6.3 | Jest matches | Custom matchers |
| **jsdom** | >=26.0.0 | DOM emulation | Node testing |
| **@vitest/ui** | >=3.0.0 | Test UI | Visual testing |

### Build & Bundle Tools

| Tool | Purpose | Why Used |
|------|---------|----------|
| **Webpack** | Bundler | Next.js built-in |
| **esbuild** | JS minification | Fast (via Vite) |
| **PostCSS** | CSS processing | Tailwind processing |

### Operating System Support

| OS | Support Level |
|---|---------------|
| **Linux** | Full support |
| **macOS** | Development support |
| **Windows** | WSL2 recommended |

### Cloud & Infrastructure

| Service | Purpose | Status |
|---------|---------|--------|
| **Docker Hub** | Image registry | Published |
| **GitHub Container Registry** | Image registry | Published |
| **SurrealDB** | Database | Embedded/Custom |
| **Ollama** | Local AI | Optional |
| **LM Studio** | Local AI | Optional |

### API Documentation Tools

| Tool | Purpose | Why Used |
|------|---------|----------|
| **Swagger UI** | API docs | FastAPI built-in |
| **ReDoc** | Alternative docs | Optional |

### Security Tools

| Tool | Purpose | Why Used |
|------|---------|----------|
| **Fernet** | Encryption | Symmetric encryption |
| **SecretStr** | Masked values | Pydantic built-in |

### Optional Extensions & Integrations

| Tool | Purpose | Required |
|------|---------|----------|
| **Ollama** | Local LLMs | No |
| **LM Studio** | Local LLM UI | No |
| ** whisper.cpp** | Local STT | No |
| **Custom TTS providers** | Speech synthesis | No |
| **OAuth/JWT** | Production auth | No |

### Supported AI Model Types

| Model Type | Description | Providers |
|-----------|-------------|-----------|
| **language** | LLM chat | All 13 providers |
| **embedding** | Text vectors | OpenAI, Cohere, Voyage, etc |
| **speech_to_text** | Transcription | OpenAI, Whisper |
| **text_to_speech** | Synthesis | ElevenLabs, OpenAI, etc |

### Complete Provider List (Esperanto)

1. **OpenAI** - GPT-4, GPT-3.5, DALL-E, Whisper
2. **Anthropic** - Claude 4, Claude 3
3. **Google** - Gemini, Vertex AI
4. **Groq** - Llama, Mixtral (fast inference)
5. **Ollama** - Local models
6. **Mistral** - Mistral, Codestral
7. **DeepSeek** - DeepSeek Chat
8. **xAI** - Grok
9. **OpenRouter** - Gateway to 100+ models
10. **Voyage** - Voyage embeddings
11. **ElevenLabs** - TTS
12. **Azure OpenAI** - Enterprise OpenAI
13. **OpenAI-Compatible** - Local/third-party APIs |

### Database Schema Entities

| Entity | Purpose |
|--------|---------|
| **Notebook** | Research project container |
| **Source** | Content (file/URL) |
| **Note** | User notes |
| **SourceInsight** | AI-generated insights |
| **SourceEmbedding** | Vector embeddings |
| **ChatSession** | Conversation threads |
| **Credential** | API keys (encrypted) |
| **Model** | AI model registry |
| **SpeakerProfile** | Podcast voices |
| **EpisodeProfile** | Podcast settings |
| **PodcastEpisode** | Generated podcasts |
| **Transformation** | Custom prompts |
| **DefaultModels** | Default configurations |

### Graph Relationships

| Relationship | From | To |
|---------------|------|-----|
| **contains** | Notebook | Source |
| **has_note** | Notebook | Note |
| **references** | Note | Source |
| **refers_to** | Note | Note |
| **artifact_of** | Source | Source |
| **linked_to** | Model | Credential |

### Async Job Commands

| Command | Purpose |
|---------|---------|
| **embed_source** | Vectorize source |
| **embed_note** | Vectorize note |
| **embed_insight** | Vectorize insight |
| **create_insight** | Generate AI insight |
| **process_source** | Ingest content |
| **run_transformation** | Apply transformation |
| **generate_podcast** | Create podcast |
| **rebuild_embeddings** | Bulk rebuild |

### Prompt Templates (ai-prompter)

| Template | Purpose |
|----------|---------|
| **ask/entry** | Search strategy |
| **ask/query_process** | Query execution |
| **ask/final_answer** | Final synthesis |
| **chat/system** | Chat system prompt |
| **source_chat/system** | Source chat prompt |
| **podcast/outline** | Podcast outline |
| **podcast/transcript** | Podcast dialogue |

---

## Code Quality

### Project Version

**Current Version**: `1.8.0` (from `pyproject.toml`)

### Python Code Quality Standards

#### Linting (Ruff)

The project uses **Ruff** for Python linting, configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = [
    "E501",  # line too long
    "E402",  # module level import not at top of file
    "E722",  # do not use bare except
    "F401",  # imported but unused
    "F541",  # f-string without placeholders
    "F841",  # local variable assigned but never used
]
```

#### Type Checking (MyPy)

The project uses **MyPy** for static type analysis:

```toml
[tool.mypy]
[[tool.mypy.overrides]]
module = "pages.*"
ignore_errors = true  # Streamlit pages excluded
```

MyPy configuration is in `mypy.ini`:

```ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

#### Import Sorting (isort)

```toml
[tool.isort]
profile = "black"
line_length = 88
```

### Frontend Code Quality Standards

#### ESLint Configuration

The frontend uses **ESLint 9** with Next.js configuration:

```javascript
// eslint.config-next.js (or extends next/typescript)
```

#### Package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "node start-server.js",
    "lint": "eslint src/",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

### Code Style Guidelines

From `docs/7-DEVELOPMENT/code-standards.md`:

1. **Line Length**: 88 characters (Black formatter)
2. **Type Safety**: Full type annotations in Python, TypeScript in frontend
3. **Docstrings**: Google-style docstrings in Python
4. **Comments**: Explain "why", not "what"
5. **Testing**: Minimum coverage for critical paths

---

## Libraries & Dependencies

### Backend Dependencies (pyproject.toml)

```toml
[project]
requires-python = ">=3.11,<3.13"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.9.2",
    "loguru>=0.7.2",
    "langchain>=1.2.0",
    "langgraph>=1.0.5",
    "tiktoken>=0.12.0",
    "langgraph-checkpoint-sqlite>=3.0.1",
    "langchain-community>=0.4.1",
    "langchain-openai>=1.1.6",
    "langchain-anthropic>=1.3.0",
    "langchain-ollama>=1.0.1",
    "langchain-google-genai>=4.1.2",
    "langchain-groq>=1.1.1",
    "langchain_mistralai>=1.1.1",
    "langchain_deepseek>=1.0.0",
    "tomli>=2.0.2",
    "python-dotenv>=1.0.1",
    "httpx[socks]>=0.27.0",
    "content-core>=1.14.1,<2",
    "ai-prompter>=0.3,<1",
    "esperanto>=2.19.3,<3",
    "surrealdb>=1.0.4",
    "podcast-creator>=0.11.2,<1",
    "surreal-commands>=1.3.1,<2",
    "numpy>=2.4.1",
    "pycountry>=26.2.16",
    "babel>=2.18.0",
    "duckduckgo-search>=5.0.0",
]
```

#### Core Dependencies Analysis

| Dependency | Version | Purpose |
|------------|----------|---------|
| **fastapi** | >=0.104.0 | REST API framework |
| **uvicorn** | >=0.24.0 | ASGI server |
| **pydantic** | >=2.9.2 | Data validation |
| **loguru** | >=0.7.2 | Logging |
| **langchain** | >=1.2.0 | AI integration |
| **langgraph** | >=1.0.5 | Workflow orchestration |
| **tiktoken** | >=0.12.0 | Token counting |
| **langgraph-checkpoint-sqlite** | >=3.0.1 | State persistence |
| **surrealdb** | >=1.0.4 | Database |
| **esperanto** | >=2.19.3 | AI provider unified API |
| **content-core** | >=1.14.1 | Content extraction |
| **ai-prompter** | >=0.3 | Jinja2 templating |
| **podcast-creator** | >=0.11.2 | Podcast generation |
| **surreal-commands** | >=1.3.1 | Async job queue |

### Backend Dev Dependencies

```toml
[project.optional-dependencies]
dev = [
    "ipykernel>=6.29.5",
    "ruff>=0.5.5",
    "mypy>=1.11.1",
    "types-requests>=2.32.0.20241016",
    "ipywidgets>=8.1.5",
    "pre-commit>=4.0.1",
    "pytest>=8.0.0",
]
```

### Frontend Dependencies (package.json)

```json
{
  "dependencies": {
    "@hookform/resolvers": "^5.1.1",
    "@monaco-editor/react": "^4.7.0",
    "@radix-ui/react-accordion": "^1.2.12",
    "@radix-ui/react-alert-dialog": "^1.1.14",
    "@radix-ui/react-checkbox": "^1.3.2",
    "@radix-ui/react-collapsible": "^1.1.11",
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.15",
    "@radix-ui/react-label": "^2.1.7",
    "@radix-ui/react-popover": "^1.1.15",
    "@radix-ui/react-progress": "^1.1.7",
    "@radix-ui/react-radio-group": "^1.3.8",
    "@radix-ui/react-scroll-area": "^1.2.9",
    "@radix-ui/react-select": "^2.2.5",
    "@radix-ui/react-separator": "^1.1.7",
    "@radix-ui/react-slot": "^1.2.3",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.12",
    "@radix-ui/react-tooltip": "^1.2.7",
    "@tailwindcss/typography": "^0.5.16",
    "@tanstack/react-query": "^5.83.0",
    "@uiw/react-md-editor": "^4.0.8",
    "axios": "^1.13.5",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "date-fns": "^4.1.0",
    "i18next": "^25.7.3",
    "i18next-browser-languagedetector": "^8.2.0",
    "lucide-react": "^0.525.0",
    "next": "^16.1.5",
    "next-themes": "^0.4.6",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "react-hook-form": "^7.60.0",
    "react-i18next": "^16.5.0",
    "react-markdown": "^10.1.0",
    "remark-gfm": "^4.0.1",
    "sonner": "^2.0.6",
    "tailwind-merge": "^3.3.1",
    "use-debounce": "^10.0.6",
    "zod": "^4.0.5",
    "zustand": "^5.0.6"
  }
}
```

### Frontend Dev Dependencies

```json
{
  "devDependencies": {
    "@eslint/eslintrc": "^3",
    "@tailwindcss/postcss": "^4",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.2.0",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "@vitejs/plugin-react": "^4.3.4",
    "@vitest/ui": "^3.0.0",
    "eslint": "^9",
    "eslint-config-next": "15.4.2",
    "jsdom": "^26.0.0",
    "tailwindcss": "^4",
    "tw-animate-css": "^1.3.5",
    "typescript": "^5",
    "vitest": "^3.0.0"
  }
}
```

---

## Version Decisions

### Python Version: 3.12

**Decision**: `3.12` (from `.python-version`)

**Rationale**:
- **Performance**: 10-25% faster than 3.11 for most workloads
- **Free-threaded GIL**: Experimental support for parallel execution
- **Typing improvements**: More expressive type annotations
- **Compatibility**: Most packages support 3.11+

**Constraint**: `>=3.11,<3.13` (from `pyproject.toml`)

### Next.js Version: 16.1.5

**Decision**: `^16.1.5`

**Rationale**:
- **React 19 support**: Native React 19 compatibility
- **App Router**: Mature App Router for server components
- **Performance**: Improved caching and streaming
- **Stability**: Production-ready

### React Version: 19.2.3

**Decision**: `^19.2.3`

**Rationale**:
- **Next.js 16 requirement**: Next.js 16 uses React 19
- **Performance improvements**: Better concurrent rendering
- **Modern hooks**: useOptimistic, useFormStatus improvements

### FastAPI Version: 0.104+

**Decision**: `>=0.104.0`

**Rationale**:
- **Pydantic v2 compatibility**: Native Pydantic v2 support
- **Background tasks**: Stable async task handling
- **Stability**: Mature, production-tested

### LangGraph Version: 1.0.5+

**Decision**: `>=1.0.5`

**Rationale**:
- **State machine patterns**: Robust workflow orchestration
- **Checkpointing**: SQLite persistence for long conversations
- **Multi-agent support**: Built-in agent patterns

### SurrealDB Version: 1.0.4+

**Decision**: `>=1.0.4`

**Rationale**:
- **Graph database**: Native relationship handling
- **Vector embeddings**: Built-in vector search
- **Async driver**: Full async/await support
- **ACID compliance**: Reliable transactions

### Tailwind CSS Version: 4.x

**Decision**: `^4`

**Rationale**:
- **Performance**: 10x faster build times
- **CSS-first config**: No JS config needed
- **Improved DX**: Automatic content detection

### Zustand Version: 5.0.6

**Decision**: `^5.0.6`

**Rationale**:
- **Simple API**: Minimal boilerplate
- **Performance**: No re-renders unless needed
- **TypeScript**: Full type safety
- **Middleware**: Built-in persist, devtools

### TanStack Query Version: 5.83.0

**Decision**: `^5.83.0`

**Rationale**:
- **Server state**: Best-in-class caching
- **Optimistic updates**: Built-in UI updates
- **Deduplication**: Automatic request dedup

### Zod Version: 4.0.5

**Decision**: `^4.0.5`

**Rationale**:
- **TypeScript-first**: Native TS support
- **Performance**: Fast validation
- **Composable**: Chained validation

---

## Architecture Analysis

### Root CLAUDE.md Analysis

The root `CLAUDE.md` provides architectural guidance at the project level:

#### Key Architecture Highlights

1. **Async-First Design**
   - All database queries, graph invocations, and API calls are async (await)
   - SurrealDB async driver with connection pooling
   - FastAPI handles concurrent requests efficiently

2. **LangGraph Workflows**
   - `source.py`: Content ingestion (extract → embed → save)
   - `chat.py`: Conversational agent with message history
   - `ask.py`: Search + synthesis (retrieve relevant sources → LLM)
   - `transformation.py`: Custom transformations on sources

3. **Multi-Provider AI**
   - **Esperanto library**: Unified interface to 8+ AI providers
   - **Credential system**: Individual encrypted credential records per provider
   - **ModelManager**: Factory pattern with fallback logic
   - **Smart selection**: Detects large contexts, prefers long-context models

4. **Database Schema**
   - **Automatic migrations**: AsyncMigrationManager runs on API startup
   - **SurrealDB graph model**: Records with relationships and embeddings
   - **Vector search**: Built-in semantic search
   - **Transactions**: Repo functions handle ACID operations

5. **Error Handling**
   - Custom exceptions (`exceptions.py`)
   - Error classification (`utils/error_classifier.py`)
   - Global exception handlers in FastAPI

### API Module Analysis (api/CLAUDE.md)

The API module uses a three-layer architecture:

#### Layers

1. **Routes** (`routers/*`): HTTP endpoints mapping to services
2. **Services** (`*_service.py`): Business logic orchestrating domain models
3. **Models** (`models.py`): Pydantic request/response schemas

#### Key Services

| Service | Purpose |
|---------|---------|
| `chat_service.py` | Invokes chat graph with messages, context |
| `podcast_service.py` | Orchestrates outline + transcript generation |
| `sources_service.py` | Content ingestion, vectorization, metadata |
| `transformations_service.py` | Applies transformations to content |
| `models_service.py` | Manages ModelManager config |
| `episode_profiles_service.py` | Podcast profile management |

#### Common Patterns

- **Service injection via FastAPI**: No DI framework
- **Async/await throughout**: All operations async
- **SurrealDB transactions**: Use repo_query, repo_create, repo_upsert
- **Config override pattern**: Models/config override via RunnableConfig

### Frontend Module Analysis (frontend/src/CLAUDE.md)

Three-layer architecture for Next.js React application:

#### Layers

1. **Pages** (`src/app/`): Next.js App Router
2. **Components** (`src/components/`): Feature-specific UI
3. **Lib** (`src/lib/`): Data fetching, state management, utilities

#### Data Flow

```
Pages (Next.js) → Components (feature-specific) → Hooks (queries/mutations)
                                                       ↓
                          Stores (auth/modal state) → API module → Backend
```

#### Component Organization

- **layout**: `AppShell.tsx`, `AppSidebar.tsx`
- **providers**: `ThemeProvider`, `QueryProvider`, `ModalProvider`
- **auth**: `LoginForm.tsx`
- **common**: `CommandPalette`, `ErrorBoundary`, `ContextToggle`
- **ui**: Radix UI building blocks
- **feature folders**: source, notebooks, search, podcasts

### Domain Module Analysis (open_notebook/domain/CLAUDE.md)

Core data models with async SurrealDB persistence:

#### Base Classes

| Class | Purpose |
|-------|---------|
| **ObjectModel** | Mutable records with auto-increment IDs |
| **RecordModel** | Singleton configuration |

#### Models

| Model | Purpose |
|-------|---------|
| **Notebook** | Research project container |
| **Source** | Content item (file/URL) |
| **Note** | Standalone or linked notes |
| **SourceInsight** | AI-generated insights |
| **ChatSession** | Conversation container |
| **Credential** | API key storage |

#### Key Features

- **Polymorphic get()**: Resolves subclass from ID prefix
- **Auto-embedding**: Fire-and-forget via surreal-commands
- **Relationship management**: Graph relationships

### AI Module Analysis (open_notebook/ai/CLAUDE.md)

Model configuration and provisioning:

#### Two-Tier System

1. **Database models** (`Model`, `DefaultModels`): Metadata storage
2. **ModelManager**: Factory for instantiating AI models

#### Key Components

| Component | Purpose |
|-----------|---------|
| **Model** | Database record with provider, type |
| **DefaultModels** | Singleton configuration |
| **ModelManager** | Model instantiation factory |
| **provision_langchain_model()** | Smart fallback logic |
| **key_provider.py** | Database-first API key provision |

#### Multi-Provider Support

```
Esperanto supports:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 4, Claude 3)
- Google (Gemini, Vertex)
- Groq (Llama, Mixtral)
- Ollama (Local models)
- Mistral (Mistral, Codestral)
- DeepSeek (DeepSeek Chat)
- xAI (Grok)
- OpenRouter (Gateway)
- Voyage (Embeddings)
- ElevenLabs (TTS)
- Azure OpenAI
- OpenAI-Compatible
```

### Graphs Module Analysis (open_notebook/graphs/CLAUDE.md)

LangGraph-based workflow orchestration:

#### Graphs

| Graph | Purpose |
|-------|---------|
| **chat.py** | Conversational agent with message history |
| **source_chat.py** | Source-focused chat |
| **ask.py** | Multi-search strategy agent |
| **source.py** | Content ingestion pipeline |
| **transformation.py** | Transformation executor |
| **prompt.py** | Generic prompt chain |

#### Key Patterns

- **Async/sync bridging**: ThreadPoolExecutor workaround
- **State machines**: StateGraph with conditional edges
- **Prompt templating**: ai_prompter with Jinja2
- **Checkpointing**: SqliteSaver for persistence

### Database Module Analysis (open_notebook/database/CLAUDE.md)

SurrealDB abstraction layer:

#### Two-Tier System

1. **Repository Layer**: Raw async CRUD operations
2. **Migration Layer**: Schema versioning

#### Key Functions

| Function | Purpose |
|-----------|---------|
| `db_connection()` | Connection context manager |
| `repo_query()` | Execute SurrealQL |
| `repo_create()` | Insert record |
| `repo_upsert()` | Create-or-update |
| `repo_update()` | Update existing |
| `repo_delete()` | Delete record |
| `repo_relate()` | Create relationship |

#### Migration System

- **AsyncMigrationManager**: 14 migrations
- **Auto-run on API startup**
- **Version tracking in `_sbl_migrations`**

### Utils Module Analysis (open_notebook/utils/CLAUDE.md)

Cross-cutting utilities:

#### Core Utilities

| Utility | Purpose |
|---------|---------|
| **context_builder.py** | LLM context assembly |
| **chunking.py** | Content-type aware text chunking |
| **embedding.py** | Unified embedding generation |
| **text_utils.py** | Text cleaning |
| **token_utils.py** | Token counting |
| **version_utils.py** | Version management |
| **encryption.py** | Fernet encryption |

#### Configuration

| Environment Variable | Purpose | Default |
|----------------------|---------|---------|
| `OPEN_NOTEBOOK_CHUNK_SIZE` | Max chunk size (chars) | 1200 |
| `OPEN_NOTEBOOK_CHUNK_OVERLAP` | Chunk overlap (chars) | 15% of chunk size |

### Podcasts Module Analysis (open_notebook/podcasts/CLAUDE.md)

Podcast generation with profile management:

#### Models

| Model | Purpose |
|-------|---------|
| **SpeakerProfile** | Voice and personality config |
| **EpisodeProfile** | Generation settings |
| **PodcastEpisode** | Generated episode with job tracking |

#### Key Features

- **Model registry references**: Replace old provider/model strings
- **Profile snapshots**: Freeze config at generation time
- **Job tracking**: surreal-commands integration

### Commands Module Analysis (commands/CLAUDE.md)

Async command handlers for long-running operations:

#### Command Types

| Command | Purpose |
|---------|---------|
| **embed_note_command** | Note embedding |
| **embed_insight_command** | Insight embedding |
| **embed_source_command** | Source embedding |
| **create_insight_command** | AI insight generation |
| **rebuild_embeddings_command** | Bulk rebuild |
| **process_source_command** | Content ingestion |
| **run_transformation_command** | Transformation execution |
| **generate_podcast_command** | Podcast generation |

#### Retry Strategy

```python
{
    "max_attempts": 5,
    "wait_strategy": "exponential_jitter",
    "stop_on": [ValueError]
}
```

### Prompts Module Analysis (prompts/CLAUDE.md)

Jinja2 prompt templates for AI workflows:

#### Template Organization

| Directory | Purpose |
|-----------|---------|
| **ask/** | Multi-stage search synthesis |
| **chat/** | Conversational agent |
| **source_chat/** | Source-focused chat |
| **podcast/** | Podcast generation |

#### Prompt Engineering Patterns

1. **Multi-stage chains**: Entry → Process → Final
2. **Conditional injection**: Jinja2 if/for blocks
3. **Citation enforcement**: Repeated instructions
4. **Format delegation**: External output format
5. **Extended thinking**: Separate reasoning from output

### Frontend Stores Module Analysis (frontend/src/lib/stores/CLAUDE.md)

Zustand-based state management:

#### Stores

| Store | Purpose |
|-------|---------|
| **auth-store.ts** | Authentication state |
| **Modal stores** | Modal visibility/data |

#### Key Patterns

- **Zustand + persist**: Auto-sync to localStorage
- **Selective persistence**: `partialize` option
- **Hydration tracking**: `setHasHydrated()`
- **30-second auth cache**: Avoid excessive API calls

### Frontend Hooks Module Analysis (frontend/src/lib/hooks/CLAUDE.md)

React hooks for data fetching:

#### Hook Types

| Hook | Purpose |
|------|---------|
| **Query hooks** | TanStack Query wrappers |
| **Mutation hooks** | Server mutations with cache invalidation |
| **Chat hooks** | Session + streaming management |
| **Streaming hooks** | SSE parsing |
| **Model/config hooks** | Settings management |

#### Key Features

- **Optimistic updates**: Add to state before server response
- **Broad invalidation**: Trade-off between accuracy + performance
- **Status polling**: Auto-refetch while running

### Frontend API Module Analysis (frontend/src/lib/api/CLAUDE.md)

Axios-based backend communication:

#### Key Components

| Component | Purpose |
|-----------|---------|
| **client.ts** | Central Axios instance |
| **Resource modules** | Endpoint-specific functions |
| **query-client.ts** | TanStack Query config |

#### Key Patterns

- **10-minute timeout**: For slow LLM operations
- **Bearer auth**: Auto-added from localStorage
- **FormData handling**: Auto-remove Content-Type

### Frontend Locales Module Analysis (frontend/src/lib/locales/CLAUDE.md)

i18next internationalization system:

#### Supported Languages

| Code | Language |
|------|---------|
| en-US | English (US) |
| pt-BR | Portuguese (Brazil) |
| zh-CN | Chinese (Simplified) |
| zh-TW | Chinese (Traditional) |
| ja-JP | Japanese |
| ru-RU | Russian |

#### Architecture

```
lib/
├── i18n.ts                    # i18next initialization
├── hooks/use-translation.ts     # Custom hook with Proxy API
├── locales/
│   ├── index.ts              # Locale registry
│   ├── en-US/index.ts        # English
│   └── ... (other locales)
└── utils/date-locale.ts      # Date formatting
```

### UI Components Module Analysis (frontend/src/components/ui/CLAUDE.md)

Radix UI-based component library:

#### Component Categories

| Category | Examples |
|----------|----------|
| **Primitives** | button, dialog, select |
| **Composite** | checkbox-list, wizard |
| **Form** | input, textarea, label |
| **Feedback** | alert, alert-dialog, progress |
| **Layout** | card, accordion, tabs |
| **Utilities** | badge, separator, tooltip |

#### Key Patterns

- **Radix UI wrappers**: Apply Tailwind via cn()
- **CVA**: Variant/size combinations
- **Data slots**: For testing/styling
- **Accessibility first**: ARIA attributes

---

## Component Reference

### Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| AppShell | components/layout/AppShell.tsx | Main layout wrapper |
| AppSidebar | components/layout/AppSidebar.tsx | Navigation sidebar |
| ThemeProvider | components/providers/ThemeProvider.tsx | Dark mode support |
| QueryProvider | components/providers/QueryProvider.tsx | React Query |
| LoginForm | components/auth/LoginForm.tsx | Authentication UI |
| CommandPalette | components/common/CommandPalette.tsx | Quick actions |
| ErrorBoundary | components/common/ErrorBoundary.tsx | Error catching |

### Backend Components

| Component | File | Purpose |
|-----------|------|---------|
| FastAPI App | api/main.py | Application entry |
| Chat Router | api/routers/chat.py | Chat endpoint |
| Source Router | api/routers/sources.py | Source CRUD |
| Notebook Router | api/routers/notebooks.py | Notebook CRUD |
| Podcast Router | api/routers/podcasts.py | Podcast generation |

### Domain Models

| Model | File | Purpose |
|-------|------|---------|
| Notebook | open_notebook/domain/notebook.py | Research container |
| Source | open_notebook/domain/notebook.py | Content item |
| Note | open_notebook/domain/notebook.py | Notes |
| Credential | open_notebook/domain/credential.py | API keys |
| Transformation | open_notebook/domain/transformation.py | Transformations |

### LangGraph Workflows

| Graph | File | Purpose |
|------|------|---------|
| chat | open_notebook/graphs/chat.py | Conversational agent |
| ask | open_notebook/graphs/ask.py | Search + synthesis |
| source | open_notebook/graphs/source.py | Content ingestion |
| transformation | open_notebook/graphs/transformation.py | Content transformation |

---

## Installation

### Quick Start (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/Malaybhai11/synapse.git
cd synapse

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:5055
# API Docs: http://localhost:5055/docs
```

### From Source

```bash
# Install Python 3.12+
# Install Node.js 20+

# Clone repository
git clone https://github.com/Malaybhai11/synapse.git
cd synapse

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend
npm install

# Start SurrealDB
docker compose up -d surrealdb

# Start API (terminal 1)
make api

# Start frontend (terminal 2)
make frontend
```

### Environment Variables

Create `.env` file:

```bash
# Required
OPEN_NOTEBOOK_PASSWORD=your-secure-password
OPEN_NOTEBOOK_ENCRYPTION_KEY=your-encryption-key

# Database (defaults)
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=open_notebook

# AI Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# ... etc
```

---

## Configuration

### AI Provider Configuration

From `docs/5-CONFIGURATION/ai-providers.md`:

Supported providers (13 total):

| Provider | API Type | Models |
|----------|---------|--------|
| OpenAI | API Key | GPT-4, GPT-3.5, Embeddings |
| Anthropic | API Key | Claude 4, Claude 3 |
| Google | API Key | Gemini |
| Groq | API Key | Llama, Mixtral |
| Ollama | URL | Local models |
| Mistral | API Key | Mistral, Codestral |
| DeepSeek | API Key | DeepSeek Chat |
| xAI | API Key | Grok |
| OpenRouter | API Key | Gateway |
| Voyage | API Key | Embeddings |
| ElevenLabs | API Key | TTS |
| Azure | Multi-field | Azure OpenAI |
| Vertex | Multi-field | Google Vertex |
| OpenAI-Compatible | Multi-field | Local/Third-party |

### Database Configuration

From `docs/5-CONFIGURATION/database.md`:

```bash
# SurrealDB
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=open_notebook
```

### Local TTS/STT Configuration

From `docs/5-CONFIGURATION/local-tts.md` and `local-stt.md`:

Ollama for local speech:
- TTS: Use Ollama with speech models
- STT: Use Whisper model

---

## Development

### Setup Development Environment

From `docs/7-DEVELOPMENT/development-setup.md`:

```bash
# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest tests/

# Run linting
make ruff
make lint
```

### Code Standards

From `docs/7-DEVELOPMENT/code-standards.md`:

1. **Line length**: 88 characters
2. **Import sorting**: isort profile
3. **Type hints**: Full annotations
4. **Docstrings**: Google-style

### Adding New Features

#### Add API Endpoint

1. Create router in `api/routers/feature.py`
2. Create service in `api/feature_service.py`
3. Define schemas in `api/models.py`
4. Register router in `api/main.py`

#### Add LangGraph Workflow

1. Create `open_notebook/graphs/workflow_name.py`
2. Define StateDict and node functions
3. Build graph with `.add_node()` / `.add_edge()`
4. Invoke in service

#### Add Database Migration

1. Create `migrations/N_description.surql`
2. Create `migrations/N_description_down.surql`
3. Update AsyncMigrationManager

---

## Testing

### Backend Testing

From `docs/7-DEVELOPMENT/testing.md`:

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_domain.py
```

### Frontend Testing

```bash
# Run tests
npm run test

# Run with UI
npm run test:ui

# Watch mode
npm run test:watch
```

### Testing Strategy

| Test Type | Location | Framework |
|----------|---------|-----------|
| Unit tests | `tests/test_domain.py` | Pytest |
| Graph tests | `tests/test_graphs.py` | Pytest |
| Utils tests | `tests/test_utils.py` | Pytest |
| Component tests | `frontend/src/**/*.test.tsx` | Vitest |

---

## Deployment

### Docker Deployment

From `docs/1-INSTALLATION/docker-compose.md`:

```bash
# Build production image
make docker-build-local

# Run production
docker run -p 5055:5055 -p 3000:3000 \
  -e OPEN_NOTEBOOK_PASSWORD=secret \
  -e OPEN_NOTEBOOK_ENCRYPTION_KEY=key \
  lfnovo/open_notebook:latest
```

### Production Checklist

1. **Security Settings**
   - Change default password
   - Set encryption key
   - Configure CORS restrictions
   - Enable authentication

2. **Environment Variables**
   - Database credentials
   - AI provider keys
   - Encryption key

3. **Reverse Proxy**
   - Configure Nginx/Caddy
   - SSL/TLS certificates

---

## Security

### Security Features

From `docs/5-CONFIGURATION/security.md`:

1. **API Key Encryption**
   - Fernet symmetric encryption
   - Database-first credential storage

2. **Authentication**
   - Password-based access control
   - JWT/OAuth ready

3. **Input Validation**
   - Pydantic validation
   - URL validation (SSRF protection)

4. **Error Handling**
   - Type-safe exceptions
   - User-friendly messages

### Security Considerations

| Feature | Implementation |
|---------|----------------|
| API Key Storage | Fernet encryption |
| Password | Environment variable |
| CORS | Configurable |
| Rate Limiting | Proxy layer |

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Support & Community

- **Documentation**: [open-notebook.ai](https://open-notebook.ai)
- **Discord**: [discord.gg/37XJPXfz2w](https://discord.gg/37XJPXfz2w)
- **Issues**: [github.com/Malaybhai11/synapse/issues](https://github.com/Malaybhai11/synapse/issues)
- **Discussions**: [github.com/Malaybhai11/synapse/discussions](https://github.com/Malaybhai11/synapse/discussions)

---

## Changelog

### Version 1.8.0

- Enhanced credential management system
- Model registry improvements
- Multi-provider TTS support

### Version 1.7.3

- LangGraph state persistence
- SQLite checkpoint storage
- Improved error handling

### Version 1.7.0

- SurrealDB migration system
- Async-first design
- Multi-stage podcast generation

---

<p align="center">
  <strong>Synapse</strong> - Open Source AI Research Assistant
</p>

<p align="center">
  <a href="https://github.com/Malaybhai11/synapse">GitHub</a> •
  <a href="https://discord.gg/37XJPXfz2w">Discord</a> •
  <a href="https://open-notebook.ai">Documentation</a>
</p>