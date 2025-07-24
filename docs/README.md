## Agent Development Kit (ADK) Documentation

> **Version**: v0.1 – auto-generated comprehensive developer guide for the open-source ADK Python package shipped in this repository.
>
> **Purpose**: Provide a single, searchable markdown reference that explains the *public* classes, functions and CLI commands exposed by ADK together with practical copy-paste ready examples.

---

### Contents

1. [Quick-Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [High-level Workflow](#high-level-workflow)
4. [Public API Reference](#public-api-reference)
   1. [google.adk.Agent](#googleadkagent)
   2. [google.adk.Runner](#googleadkrunner)
   3. [Tools](#tools)
   4. [Events & Sessions](#events--sessions)
   5. [Models](#models)
   6. [Memory Services](#memory-services)
   7. [Artifacts](#artifacts)
   8. [Plugins](#plugins)
5. [Extending ADK](#extending-adk)
6. [CLI Utilities](#cli-utilities)
7. [Complete Examples](#complete-examples)
8. [FAQ](#faq)

---

## Quick-Start

```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.tools import google_search

# 1️⃣  Build a root agent (single-agent use-case)
assistant = Agent(
    name="search_assistant",
    model="gemini-2.0-flash",               # Works with Gemini and 3rd-party LLMs
    instruction=(
        "You are a helpful assistant. Use Google Search to answer questions "
        "when necessary."
    ),
    tools=[google_search],
)

# 2️⃣  Create ephemeral in-memory services (good for local experiments)
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

session_service  = InMemorySessionService()
artifact_service = InMemoryArtifactService()

# 3️⃣  Launch a runner to execute the agent
runner = Runner(
    app_name="demo_app",
    agent=assistant,
    session_service=session_service,
    artifact_service=artifact_service,
)

# 4️⃣  Start a new conversation (blocking / synchronous helper)
from google.genai import types

for event in runner.run(
    user_id="alice",
    session_id="default",
    new_message=types.Content( parts=[types.Part(text="Who is Ada Lovelace?")] ),
):
    if event.content:
        print(event.content.parts[0].text)
```

**Live-streaming mode** (`run_live`) and asynchronous mode (`run_async`) are also available – see the reference section below.

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | Encapsulates model prompts, tools, callbacks and (optionally) child agents. Implemented by `google.adk.agents.Agent` (alias for `LlmAgent`). |
| **Runner** | Orchestrates agent execution inside a Session, managing memory, artifacts, plugins and telemetry. |
| **Tool** | A callable (Python function, subclass of `BaseTool`, or `BaseToolset`) that the agent can invoke to accomplish tasks (Google Search, BigQuery, etc.). |
| **Event** | Immutable struct emitted by agents describing model outputs, tool calls, or state changes. Persisted inside the Session. |
| **Session** | Conversation transcript + per-session key-value state stored by a `SessionService`. |
| **ArtifactService** | Pluggable blob storage for files uploaded / generated during a run (GCS, local FS, in-memory). |
| **MemoryService** | Long-term conversation memory. Default is `InMemoryMemoryService`. |
| **Plugin** | Hook points that can intercept user messages, events, or lifecycle actions (spam filter, analytics, etc.). |

---

## High-level Workflow

1. **User** sends a message ⇒ `Runner` appends it to the `Session`.
2. `Runner` decides which **Agent** in the tree should handle the turn.
3. Agent builds an **LLM request** (instructions, history, tool schema) and calls the **model**.
4. Agent interprets the LLM response – it can:
   * Return a text reply → emit `Event` with `author='model'`.
   * Make a tool call → execute **Tool**, capture output, feed back into itself.
   * Transfer control to another sub-agent.
5. Every emitted `Event` is persisted by `SessionService`; `ArtifactService` stores any blobs.
6. Runner yields events to the caller and triggers **plugin** callbacks.

---

## Public API Reference

### google.adk.Agent

Alias for `google.adk.agents.llm_agent.LlmAgent` re-exported at the package root for convenience.

```python
from google.adk import Agent
```

**Key Parameters** (selected):

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | `str` | _required_ | Human-readable identifier; must be unique in the agent tree. |
| `model` | `str \| BaseLlm` | `''` | Gemini model ID or a custom model instance. Inherits from parent if empty. |
| `instruction` | `str \| InstructionProvider` | `''` | System prompt guiding the agent. If callable, receives `ReadonlyContext`. |
| `tools` | `list[ToolUnion]` | `[]` | Functions / `BaseTool` / `BaseToolset` available to the agent. |
| `planner` | `BasePlanner` | `None` | Enables advanced reasoning / plan-and-execute workflows. |
| `code_executor` | `BaseCodeExecutor` | `None` | Runs code blocks returned by the model (e.g. Python, JS, Docker). |
| `before_model_callback` / `after_model_callback` | callable(s) | `None` | Intercept raw LLM requests / responses. |
| `input_schema` / `output_schema` | `pydantic.BaseModel` subclass | `None` | Typed I/O enforcement when exposing agent as a function-tool or returning structured JSON. |

#### Common Methods

| Method | Returns | Notes |
|--------|---------|-------|
| `run_async(ctx)` | `AsyncGenerator[Event]` | Low-level helper; usually invoked via `Runner`. |
| `run_live(ctx)` | `AsyncGenerator[Event]` | Supports incremental user input/output streams. |
| `canonical_*` accessors | Internal helpers that resolve lazy fields (model, instruction, tools, etc.). |

#### Minimal Example

```python
from google.adk import Agent
from google.adk.tools import google_search

assistant = Agent(
    name="assistant",
    model="gemini-2.0-pro",
    instruction="Answer with citations when possible.",
    tools=[google_search],
)
```

---

### google.adk.Runner

Create exactly **one** Runner per executing application instance.

```python
from google.adk import Runner
```

**Constructor**

```python
Runner(
    app_name: str,
    agent: BaseAgent,
    session_service: BaseSessionService,
    *,
    plugins: list[BasePlugin] | None = None,
    artifact_service: BaseArtifactService | None = None,
    memory_service: BaseMemoryService | None = None,
    credential_service: BaseCredentialService | None = None,
)
```

Speed comparison – *blocking*, *async*, *live*:

| Call | Signature | Best For |
|------|-----------|---------|
| `run` | synchronous; returns `Generator[Event]` | Simple scripts, Jupyter notebooks |
| `run_async` | async; returns `AsyncGenerator[Event]` | Web backends, micro-services |
| `run_live` | async; bidirectional | Real-time UIs (chat streaming) |

---

### Tools

Tools live under `google.adk.tools.*` and follow one of three forms:

1. **Simple function** – automatically converted to a `FunctionTool`.
2. **Subclass of `BaseTool`** – single operation with rich metadata.
3. **Subclass of `BaseToolset`** – groups many tools and manages shared resources.

Example: `google.adk.tools.google_search`

```python
from google.adk.tools import google_search

results = google_search(query="Lunar eclipse next")
```

> To build custom tools, inherit from `BaseTool` or `BaseToolset` and implement `spec` & `run`.

---

### Events & Sessions

`google.adk.events.event.Event` encapsulates one turn in the conversation. Important properties:

* `author`: `'user' | 'model' | 'system'`
* `content`: `google.genai.types.Content` – multimodal gemini-compatible format
* `partial`: `bool` – indicates streaming chunk
* `actions.state_delta`: optional dict used to update `Session.state`

Session storage is abstracted behind `BaseSessionService`.

Built-in implementations:

* `InMemorySessionService` – quick prototypes
* `FirestoreSessionService` – scalable Cloud Firestore backend (optional extension)
* `VertexAiSessionService` – first-class integration with Vertex AI Agent Engine

---

### Models

`google.adk.models.*` contains LLM wrappers exposing a unified `BaseLlm` interface.

| Class | Provider | Notes |
|-------|----------|-------|
| `GeminiLlm` (default) | Google Vertex | Requires `google-genai` auth |
| `Claude` | Anthropic | Available if `anthropic` extra installed |
| `LiteLLM` | Many | Via `litellm` extra |

Register custom models with `LLMRegistry.register("id", MyLlmSubclass)` and reference them by id in your Agents.

---

### Memory Services

`BaseMemoryService` API:

```python
async get_memory(self, *, app_name: str, user_id: str, session_id: str) -> str
async save_memory(...)
```

Inject your own long-term memory (vector DB, SQL, etc.) by subclassing and passing `memory_service=` to `Runner`.

---

### Artifacts

Blob storage for binary files exchanged during a conversation.

* `InMemoryArtifactService` – default, not persisted.
* `LocalFsArtifactService` – save to disk directory.
* `GcsArtifactService` – backs onto Google Cloud Storage.

---

### Plugins

Plugins are subclasses of `BasePlugin` with optional hooks:

* `before_run`, `after_run`
* `on_user_message`
* `on_event`

Attach via the `plugins` parameter of `Runner`.

```python
class SentimentPlugin(BasePlugin):
    async def on_event(self, invocation_context, event):
        if event.author == "model":
            print("Model replied with", event.content.parts[0].text)

runner = Runner(..., plugins=[SentimentPlugin()])
```

---

## Extending ADK

* **Custom Tools** – inherit from `BaseTool` or `BaseToolset`.
* **Custom Agents** – subclass `BaseAgent` or `LlmAgent` for specialized behavior.
* **Custom Memory / Artifact / Session services** – swap database or storage backends.
* **Model Integrations** – implement `BaseLlm` and register with `LLMRegistry`.

---

## CLI Utilities

ADK ships a `adk` command-line entry point.

```
usage: adk [--help] <command> ...

Commands:
  run       # Launch FastAPI dev server with hot-reload
  eval      # Execute evaluation sets (.evalset.json)
  graph     # Render agent tree diagram using graphviz
  auth      # Manage OAuth credentials and JWT service accounts
```

Try `adk <command> --help` for exhaustive flags.

---

## Complete Examples

### 1. Multi-agent with Planner and Memory

```python
from google.adk import Agent, Runner
from google.adk.tools import google_search, load_web_page
from google.adk.memory import InMemoryMemoryService

planner = MyFancyPlanner()  # Subclass of BasePlanner (omitted for brevity)

assistant = Agent(
    name="assistant",
    model="gemini-2.0-pro",
    instruction="Answer like a research assistant. Cite sources.",
    tools=[google_search, load_web_page],
    planner=planner,
)

runner = Runner(
    app_name="research_lab",
    agent=assistant,
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
)
```

### 2. Live streaming (bidirectional)

```python
import asyncio
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.live_request_queue import LiveRequestQueue

async def chat():
    queue = LiveRequestQueue()
    runner = Runner(...)
    async for event in runner.run_live(
        user_id="alice", session_id="live", live_request_queue=queue
    ):
        if event.content:
            print("MODEL>", event.content.parts[0].text)

asyncio.run(chat())
```

---

## FAQ

1. **Which Python versions are supported?** – 3.9-3.13.
2. **How do I change the model temperature?** – Pass `generate_content_config=types.GenerateContentConfig(temperature=0.2)` to the Agent.
3. **Is ADK production-ready?** – Yes; Google uses it internally and provides official packages. The API surface, however, might evolve – pin the exact PyPI version in production.

---

*Generated automatically – feel free to refine and commit updates.*