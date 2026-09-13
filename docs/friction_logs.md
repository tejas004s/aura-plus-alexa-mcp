# Amazon Developer Hackathon: Official Friction Logs

> **Submitted for up to 10% Judging Bonus (Stage 1 Internal Review & Stage 2 Spreadsheet Score)**  
> **Project:** Aura+ — Autonomous Multi-Service Concierge for Alexa+ & AWS Bedrock  
> **Primary Track:** Alexa+ | **Mini-Challenge:** AWS Builder  

---

### Friction Entry 1: Model Context Protocol (MCP) Streamable HTTP Header & Transport Negotiation

- **Task Attempted:** Implementing bidirectional streaming tool execution over the MCP 2025-11-25 Streamable HTTP transport specification using Server-Sent Events (SSE).
- **Steps Taken:**
  1. Configured an SSE endpoint (`/mcp/sse`) yielding standard EventSource format events.
  2. Implemented the initial `endpoint` handshake event to return the HTTP POST message URI (`/mcp/message?session_id=...`).
  3. Attempted to send chunked JSON-RPC 2.0 tool execution updates back through the active SSE stream while simultaneously returning HTTP 200 to the client's POST call.
- **Expected Result:** Client maintains a persistent SSE connection while POST requests trigger concurrent streaming events on the SSE channel without buffering or connection drops.
- **Actual Result:** Standard HTTP reverse proxies (and some browser HTTP/2 implementations) automatically buffered chunked transfer frames when `Content-Type: text/event-stream` was not accompanied by `X-Accel-Buffering: no` and explicit `Cache-Control: no-cache, no-transform`. Furthermore, when multiple asynchronous tool calls executed in parallel, message serialization on the SSE channel caused race conditions if session locks were not strictly sequenced.
- **Severity Rating:** **High** (Blocks real-time multi-agent execution streaming).
- **Workaround Used:** Built an asynchronous queue-based transport manager (`StreamableHTTPTransport`) with explicit `asyncio.Queue` per session, enforced `X-Accel-Buffering: no`, and added an automatic 15-second heartbeat keepalive ping (`event: ping`) to prevent idle timeouts across proxies.
- **Actionable Suggestion for Amazon/MCP Team:** Provide an official Python and TypeScript reference SDK wrapper specifically for the Streamable HTTP transport pattern that bundles built-in connection keepalive, session queue multiplexing, and standard header presets.

---

### Friction Entry 2: AWS Bedrock Converse API Tool Calling & Multi-Agent Role Ordering

- **Task Attempted:** Invoking Amazon Bedrock (`anthropic.claude-3-5-sonnet-20241022-v2:0` and `amazon.nova-pro-v1:0`) using the `boto3` Bedrock Runtime `converse` API with complex multi-turn tool call schemas.
- **Steps Taken:**
  1. Formatted `toolConfig` with `tools=[{"toolSpec": {"name": ..., "inputSchema": ...}}]`.
  2. Attempted to supply intermediate agent thoughts and tool results across a multi-agent hierarchy (Supervisor -> Worker Agents).
  3. Sent tool results back to Bedrock Converse API with custom metadata tags.
- **Expected Result:** The Converse API accepts tool results associated with `toolUseId` and allows optional contextual metadata in the `toolResult` content block.
- **Actual Result:** The Bedrock Converse API strictly enforces that every `toolUse` block in an assistant turn MUST be followed immediately by a corresponding `toolResult` in the subsequent user turn. If an agent executes three tools in parallel and attempts to send results incrementally or includes conversational text interspersed between tool results, Bedrock returns `ValidationException: The model responded with toolUse blocks that are not properly followed by toolResult blocks`.
- **Severity Rating:** **High** (Causes unhandled API exceptions during parallel agent execution).
- **Workaround Used:** Implemented an execution buffer in `AgentCoreOrchestrator` that gathers all parallel tool outputs, verifies all `toolUseId` references match, and constructs a single unified user turn containing strictly ordered `toolResult` blocks before calling the Bedrock synthesis stage.
- **Actionable Suggestion for AWS Bedrock Team:** Relax the strict synchronous turn constraint in ConverseStream to permit progressive streaming tool results, and allow sub-agents to report execution progress asynchronously without requiring an entire conversational turn reconstruction.

---

### Friction Entry 3: Alexa+ Agent Skills Manifest vs. MCP JSON Schema Typing Divergence

- **Task Attempted:** Mapping Alexa+ Agent Skill parameter manifests directly into MCP Tool Schemas (`inputSchema.properties`) for zero-friction interoperability.
- **Steps Taken:**
  1. Exported Agent Skill manifests from the Alexa+ developer preview documentation.
  2. Converted skill definitions to standard JSON Schema Draft 7 for MCP `tools/list`.
  3. Tested validation of nested objects and arrays of strings (e.g. `dietary_restrictions: ["Gluten-Free"]`).
- **Expected Result:** Uniform schema validation across Alexa+ agent runtime and standard MCP clients.
- **Actual Result:** Certain Alexa+ skill schemas rely on implicit string coercion for scalar parameters (e.g. `"guest_count": "3"` passed as a string instead of integer `3`), while MCP clients strictly validate JSON schema types against Pydantic models. This resulted in runtime 422 Unprocessable Entity errors when numbers or booleans were transmitted as strings from voice transcripts.
- **Severity Rating:** **Medium** (Degrades reliability during voice-driven tool invocation).
- **Workaround Used:** Added lenient type coercion sanitizers inside each skill handler (e.g. `int(arguments.get("guest_count", 3))`) and defined permissive union types in Pydantic schemas.
- **Actionable Suggestion for Alexa+ Developer Platform:** Standardize the Alexa+ Agent Skill manifest definition to strictly adhere to JSON Schema Draft 2020-12 and provide an automated linter/converter CLI tool (`alexa-mcp-validate`) that generates compliant MCP schemas automatically.

---

### Friction Entry 4: Generative UI (MCP Apps) Lifecycle & State Reconciliation

- **Task Attempted:** Dynamically rendering rich interactive components (carousels, cart checkout cards, ambiance sliders) in the Alexa+ web interface while maintaining bidirectional state with the backend.
- **Steps Taken:**
  1. Emitted structured `mcp_app_card` and `mcp_app_carousel` payloads from tool executions.
  2. Rendered interactive sliders and checkout buttons on screen.
  3. Attempted to update the cart card state (from `awaiting_approval` to `confirmed`) when the user clicked "Approve Purchase".
- **Expected Result:** Seamless in-place card update with smooth transition animations.
- **Actual Result:** When the agent emitted both a natural voice response and an interactive card, re-rendering the conversation stream wiped out the local client-side state of active sliders and button focus, causing UI jitter on mobile and touch displays.
- **Severity Rating:** **Medium** (Impairs interactive UX and visual polish).
- **Workaround Used:** Decoupled the Generative UI canvas (`#mcp-apps-canvas`) from the conversational speech dialogue feed (`#dialogue-feed`). Implemented component-level UUIDs (`card_id`) and selective DOM node patching so that actions like "Approve Purchase" or slider drags update only their target widget without re-rendering the entire canvas.
- **Actionable Suggestion for Alexa+ Multi-Modal Team:** Publish an official Alexa+ Generative UI Component Library (React/Web Components) that standardizes Card, Carousel, and Action widget lifecycle states (`draft`, `awaiting_approval`, `executing`, `finalized`).

---

### Friction Entry 5: Cross-Session Long-Term Context Retention vs. LLM Context Window Bloat

- **Task Attempted:** Storing complete family profiles, historical preferences, past dining notes, and connected device states in persistent memory, then injecting this context into Bedrock prompts.
- **Steps Taken:**
  1. Loaded the entire household profile JSON into the Bedrock system prompt.
  2. Injected connected device topologies and historical preferences on every turn.
- **Expected Result:** High-quality context-aware responses with full awareness of household history.
- **Actual Result:** As household memory grew, passing the entire raw profile into every Bedrock prompt increased token consumption by over 65% per turn, increased time-to-first-token latency by ~420ms, and occasionally diluted the model's focus on the user's immediate instruction.
- **Severity Rating:** **Low-Medium** (Increases AWS inference cost and response latency).
- **Workaround Used:** Shifted from monolithic context injection to an on-demand Agent Skill pattern (`household_memory_query_dietary`). The Master Planner Bedrock prompt now contains only a lightweight summary (~80 tokens) and explicitly delegates to the Memory Skill to fetch only the relevant member profile dynamically when needed.
- **Actionable Suggestion for AWS / AgentCore Team:** Provide built-in long-term session memory caching mechanisms within Bedrock AgentCore that maintain indexed persistent state on the cloud side, eliminating the need to re-transmit static household context on every interaction turn.
