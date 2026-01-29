# Tasks: Time & Weather Agent

**Input**: Design documents from `/specs/1-time-weather-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: No automated tests requested - manual validation via Agent Framework Dev UI

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md project structure:
- Main implementation: `src/scenarios/01-hello-world-agent/`
- Shared utilities: `samples/shared/`
- MCP servers: `src/mcp-server/` (existing, no changes needed)

---

## Phase 1: Setup

**Purpose**: Project initialization and environment verification

- [x] T001 Verify Python 3.11+ and dependencies installed per requirements.txt
- [x] T002 Verify .env file exists with required Azure OpenAI environment variables
- [x] T003 [P] Verify user MCP server starts successfully at http://localhost:8002/mcp
- [x] T004 [P] Verify weather MCP server starts successfully at http://localhost:8004/mcp

**Checkpoint**: Environment ready - all dependencies and servers verified

---

## Phase 2: Foundational (Core Agent Setup)

**Purpose**: Create the base agent infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create time_weather_agent.py with standard imports and path setup in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T006 Add chat client initialization using shared model_client.py pattern in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T007 Configure MCPStreamableHTTPTool for user server (port 8002) in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T008 Configure MCPStreamableHTTPTool for weather server (port 8004) in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T009 Create ChatAgent with both MCP tools and base system instructions in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T010 Implement async main() entry point with agent context manager in src/scenarios/01-hello-world-agent/time_weather_agent.py

**Checkpoint**: Foundation ready - base agent can be instantiated with MCP tools

---

## Phase 3: User Story 1 - Location-Aware Conversation (Priority: P1) 🎯 MVP

**Goal**: Agent remembers user location from conversation and recalls it when asked

**Independent Test**: Tell agent "I am currently in London", then ask "Where did I say I am?" - agent should correctly recall London

### Implementation for User Story 1

- [x] T011 [US1] Create AgentThread instance for conversation persistence in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T012 [US1] Add system instructions for location awareness and memory in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T013 [US1] Implement conversation loop that passes thread to agent.run() with store=True in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T014 [US1] Add user input prompt and response display formatting in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T015 [US1] Test location memory with query: "I am currently in London" followed by "Can you remind me where I said I am based?"

**Checkpoint**: User Story 1 complete - agent remembers and recalls user location

---

## Phase 4: User Story 2 - Weather Inquiry (Priority: P1)

**Goal**: Agent retrieves weather for user's stated location using weather MCP server

**Independent Test**: State location, then ask "What is the weather now here?" - agent should return weather for stated location

### Implementation for User Story 2

- [x] T016 [US2] Enhance system instructions to map city names to weather server format in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T017 [US2] Add instructions for graceful handling when location unknown in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T018 [US2] Test weather query with: "I am currently in London" followed by "What is the weather now here?"
- [x] T019 [US2] Test weather with location change: "I moved to Berlin, what is the weather like today?"

**Checkpoint**: User Story 2 complete - agent provides weather for user's location

---

## Phase 5: User Story 3 - Time Inquiry (Priority: P2)

**Goal**: Agent retrieves current time for user's stated timezone location

**Independent Test**: State location, then ask "What time is it for me right now?" - agent should return correct local time

### Implementation for User Story 3

- [x] T020 [US3] Add system instructions for timezone mapping (city name → IANA format) in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T021 [US3] Add instructions to use user server get_current_time tool in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T022 [US3] Test time query with: "I am in London" followed by "What time is it for me right now?"

**Checkpoint**: User Story 3 complete - agent provides current time for user's timezone

---

## Phase 6: User Story 4 - Multi-Turn Contextual Queries (Priority: P2)

**Goal**: Agent handles seamless multi-turn conversations combining location, weather, and time

**Independent Test**: Conduct full conversation sequence from spec input queries

### Implementation for User Story 4

- [x] T023 [US4] Refine system instructions for natural conversational flow in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T024 [US4] Test complete conversation sequence from spec:
  - "I am currently in London"
  - "What is the weather now here?"
  - "What time is it for me right now?"
  - "I moved to Berlin, what is the weather like today?"
  - "Can you remind me where I said I am based?"

**Checkpoint**: User Story 4 complete - all 5 spec queries pass in single conversation

---

## Phase 7: Polish & Documentation

**Purpose**: Final validation, documentation, and observability

- [x] T025 [P] Add error handling for MCP server connection failures in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [x] T026 [P] Add graceful exit handling (Ctrl+C) for conversation loop in src/scenarios/01-hello-world-agent/time_weather_agent.py
- [ ] T027 Launch Agent Framework Dev UI and verify tool calls are visible
- [x] T028 [P] Update README.md with run instructions and link to quickstart.md in src/scenarios/01-hello-world-agent/README.md
- [x] T029 Run full quickstart.md validation sequence
- [x] T030 Verify SC-001 through SC-006 success criteria from spec

**Checkpoint**: Feature complete - all acceptance criteria met

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──────────────────────────────────────────────┐
       │                                                       │
       ▼                                                       │
Phase 2 (Foundational) ───────────────────────────────────────│
       │                                                       │
       ├──────────────────┬──────────────────┬────────────────┤
       │                  │                  │                │
       ▼                  ▼                  ▼                │
Phase 3 (US1)        Phase 4 (US2)     Phase 5 (US3)         │
  P1 MVP             P1 Weather         P2 Time              │
       │                  │                  │                │
       └──────────────────┴──────────────────┘                │
                          │                                   │
                          ▼                                   │
                    Phase 6 (US4)                             │
                    P2 Multi-turn                             │
                          │                                   │
                          ▼                                   │
                    Phase 7 (Polish)  ◄────────────────────────┘
```

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|------------|----------------------|
| US1 (Location Memory) | Phase 2 only | US2, US3 |
| US2 (Weather) | Phase 2 + US1 for context | US3 |
| US3 (Time) | Phase 2 + US1 for context | US2 |
| US4 (Multi-Turn) | US1, US2, US3 | None |

### Within Each Phase

- Tasks marked [P] can run in parallel
- Sequential tasks within same file should be done in order
- Test tasks validate the implementation before marking story complete

### Parallel Opportunities

**Phase 1** (all parallel):
```
T003 (user server verify) ←→ T004 (weather server verify)
```

**Phases 3-5** (stories can overlap):
```
US1 implementation ←→ US2 implementation ←→ US3 implementation
(all operate on same file but different logical sections)
```

**Phase 7** (parallel where marked):
```
T025 (error handling) ←→ T026 (exit handling) ←→ T028 (README update)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. ✅ Complete Phase 1: Setup (verify environment)
2. ✅ Complete Phase 2: Foundational (create base agent)
3. ✅ Complete Phase 3: User Story 1 (location memory)
4. **STOP and VALIDATE**: Test location recall independently
5. **MVP ACHIEVED**: Agent remembers location across conversation turns

### Incremental Delivery

| Milestone | Stories Complete | Value Delivered |
|-----------|------------------|-----------------|
| MVP | US1 | Location-aware conversation memory |
| +Weather | US1, US2 | Weather queries for remembered location |
| +Time | US1, US2, US3 | Time queries for remembered timezone |
| Complete | US1-US4 | Full multi-turn contextual agent |

### Single Developer Workflow

1. Setup → Foundational → US1 → Test → US2 → Test → US3 → Test → US4 → Test → Polish
2. Each story builds on previous; test before moving forward
3. Commit after each phase checkpoint

---

## Notes

- All implementation is in a **single file**: `time_weather_agent.py`
- No database or persistence - AgentThread handles in-memory state
- MCP servers are **existing infrastructure** - no changes needed
- System instructions are the primary mechanism for agent behavior
- Tests are manual via Dev UI and conversation testing (no automated tests requested)
- Total tasks: **30**
- Estimated effort: 2-3 hours for experienced developer
