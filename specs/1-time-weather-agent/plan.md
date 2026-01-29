# Implementation Plan: Time & Weather Agent

**Branch**: `1-time-weather-agent` | **Date**: 2026-01-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/1-time-weather-agent/spec.md`

## Summary

Build a conversational agent using Microsoft Agent Framework that remembers user location from conversation context, connects to MCP servers for weather and time data, and maintains conversation state across multiple turns. The agent will be implemented as a single Python script following existing sample patterns, using AgentThread for memory and MCPStreamableHTTPTool for MCP server connectivity.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: agent-framework==1.0.0b251120, fastmcp==2.13.1, pytz==2025.2  
**Storage**: In-memory via AgentThread (conversation state persisted in thread)  
**Testing**: Manual testing via Agent Framework Dev UI, integration tests with MCP servers  
**Target Platform**: Local development, Docker-compatible for MCP servers  
**Project Type**: Single workshop scenario script  
**Performance Goals**: Response time <5s for weather queries, <3s for time queries (per spec SC-002, SC-003)  
**Constraints**: Must follow existing sample patterns; MCP servers must be running  
**Scale/Scope**: Single-user workshop demo; 6 supported locations in weather server

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Explorative Learning & Safe Experimentation** | ✅ PASS | Feature branch `1-time-weather-agent` isolates experiment; learnings documented in this plan |
| **II. Modular, Composable Components** | ✅ PASS | Reuses shared `model_client.py`, existing MCP servers; agent follows ChatAgent pattern |
| **III. Automation-First Workflows** | ✅ PASS | Single command execution documented in quickstart.md; MCP servers have existing run scripts |
| **IV. Simple, Readable Codebases** | ✅ PASS | Follows existing sample patterns; linear control flow; minimal dependencies |
| **V. Documentation & Pattern Consistency** | ✅ PASS | README.md already exists; quickstart.md to be generated; follows `simple-agents/` naming |

**Gate Result**: ✅ All principles satisfied - proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/1-time-weather-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool contracts)
└── checklists/
    └── requirements.md  # Validation checklist
```

### Source Code (repository root)

```text
src/scenarios/01-hello-world-agent/
├── README.md                    # Existing scenario description
├── base_agent.py                # Existing placeholder (to be replaced)
└── time_weather_agent.py        # NEW: Main agent implementation

src/mcp-server/
├── 02-user-server/
│   └── server-mcp-sse-user.py   # Existing: User info & time tools
└── 04-weather-server/
    └── server-mcp-sse-weather.py # Existing: Weather tools

samples/shared/
└── model_client.py              # Existing: Reusable chat client factory
```

**Structure Decision**: Single scenario script in existing `src/scenarios/01-hello-world-agent/` directory. Reuses existing MCP servers and shared utilities. No new directories needed.

## Complexity Tracking

> No violations - design stays within constitution limits.

## Phase 0: Research Summary

See [research.md](research.md) for full findings.

**Key Decisions**:
1. **Conversation Memory**: Use `AgentThread` with `store=True` parameter (per `agent-thread.py` pattern)
2. **MCP Connection**: Use `MCPStreamableHTTPTool` for HTTP-based MCP servers (per `agents-using-mcp.py` pattern)
3. **Location Extraction**: Rely on LLM's natural language understanding via system instructions; no custom parsing needed
4. **Time Calculation**: User server already provides `get_current_time(location)` tool - reuse it
5. **Weather Retrieval**: Weather server provides `get_weather_at_location(location)` tool - reuse it

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](data-model.md) for entity definitions.

**Key Entities**:
- Conversation Thread (AgentThread instance)
- User Message (ChatMessage with role="user")
- Agent Response (ChatMessage with role="assistant")
- Tool Call Record (tracked in thread for Dev UI visibility)

### API Contracts

See [contracts/](contracts/) directory.

**MCP Server Tools Used**:
- `02-user-server`: `get_current_time(location: str) -> str`
- `04-weather-server`: `get_weather_at_location(location: str) -> str`, `list_supported_locations() -> list[str]`

### Quickstart

See [quickstart.md](quickstart.md) for run instructions.

## Implementation Phases

### Phase 2: Implementation Tasks

*To be generated via `/speckit.tasks` command after plan approval.*

**Anticipated task breakdown**:
1. Create `time_weather_agent.py` with ChatAgent setup
2. Configure MCPStreamableHTTPTool connections to both MCP servers
3. Define system instructions for location awareness
4. Implement conversation loop with AgentThread
5. Add Dev UI integration for observability
6. Test with all 5 input queries from spec
7. Update README.md with run instructions

---

## Post-Design Constitution Re-Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Explorative Learning** | ✅ PASS | Isolated in feature branch; research.md captures learnings |
| **II. Modular, Composable** | ✅ PASS | Reuses model_client.py, existing MCP servers; no new abstractions |
| **III. Automation-First** | ✅ PASS | quickstart.md documents single-command execution |
| **IV. Simple, Readable** | ✅ PASS | Linear script; follows existing patterns; descriptive naming |
| **V. Documentation & Patterns** | ✅ PASS | README exists; quickstart generated; matches simple-agents style |

**Final Gate Result**: ✅ Design approved - ready for Phase 2 task generation
