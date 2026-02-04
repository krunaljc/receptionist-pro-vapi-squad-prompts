# Receptionist Pro - VAPI Squad Agent

AI receptionist system for Bey & Associates personal injury law firm. This repository contains prompt configurations for VAPI voice agents.

## Directory Structure

```
├── prompts/
│   ├── demo/                         # Demo assistants (standalone, for client demos)
│   │   ├── standard_demo_receptionist/           # Email-only contact variant
│   │   └── standard_demo_receptionist_full_contact/  # Email + phone variant
│   │
│   └── squad/
│       ├── lenient/                    # Production variant (minimal verification)
│       │   ├── assistants/             # 13 agent prompts
│       │   ├── handoff_tools/          # Routing and tool configurations
│       │   ├── vapi_config/            # VAPI-specific settings
│       │   └── standalone/             # Pre-identified caller assistant
│       │
│       └── strict/                     # Future variant (strict verification)
│           └── (same structure)
│
├── .claude/
│   └── commands/
│       └── analyze-sop.md              # SOP analysis skill definition
│
├── docs/
│   ├── sop-analysis/                   # SOP analysis reference docs
│   │   ├── capability-checklist.md     # Agent capability matrix
│   │   └── sample-report.md            # Example analysis output
│   ├── CHANGELOG.md                    # Issue tracking and fixes
│   ├── new_firm_onboarding.md          # Onboarding questionnaire for new firms
│   └── vapi_squad_reference.md         # VAPI squad architecture reference
│
├── scripts/                            # Python utilities for VAPI integration
├── data/                               # Script outputs and configs
└── vapi_id_mapping.json                # Sandbox/Production assistant IDs
```

---

## Squad Variants

### Lenient (Production)

The **lenient** variant provides open information sharing with minimal verification. Currently deployed in production.

- Minimal caller verification before sharing information
- Streamlined call flow
- 11 active agents + 2 WIP

### Strict (Future)

The **strict** variant will require thorough caller verification before sharing any information.

> **Note:** The strict variant currently contains a copy of lenient as a base. Future modifications will add verification requirements.

---

## Squad Architecture

**Entry point:** Greeter Classifier routes callers to specialized agents.

| # | Agent | Purpose | Tools |
|---|-------|---------|-------|
| 1 | Greeter Classifier | Collects name, purpose, routes | handoff_tool, staff_directory_lookup |
| 3 | Existing Client | Non-pre-identified existing clients | search_case_details, staff_directory_lookup, transfer_call |
| 4 | Insurance Adjuster | Insurance company representatives | search_case_details, transfer_call |
| 5 | Medical Provider | Hospitals, clinics - fax redirect (third-party) | transfer_call |
| 6 | New Client | People who need a lawyer | transfer_call |
| 7 | Vendor | Invoice/billing callers | transfer_call |
| 8 | Direct Staff Request | Specific staff requests | staff_directory_lookup, transfer_call |
| 9 | Family Member | Third-party callers | transfer_call |
| 10 | Spanish Speaker | Spanish transfer wrapper | transfer_call |
| 12 | Legal System | Court reporters, defense attorneys | search_case_details, transfer_call |
| 14 | Fallback Line | Safety net - routes to customer success | transfer_call |

**WIP (not deployed):** 11_referral_source, 13_sales_solicitation

---

## Standalone Pre-Identified Caller

Handles callers whose phone number matches an existing client record, bypassing the squad entirely.

**Why standalone?**
- No classification needed - caller already identified via phone lookup
- Pre-loaded context - case details available immediately
- Faster service - no routing decision required

**Location:** `prompts/squad/lenient/standalone/pre_identified_caller/`

**Tools:** staff_directory_lookup, transfer_call

---

## VAPI Setup Instructions

### Step 1: Create Assistants

For each assistant in `prompts/squad/lenient/assistants/`:

1. VAPI Dashboard → Assistants → Create New
2. Set **Name** exactly as specified (case-sensitive for handoff routing)
3. Copy system prompt from the `.md` file
4. Configure model: `gpt-4.1` (default) or `chatgpt-4o-latest` (see `assistant_settings.json`)
5. Configure voice: Cartesia `sonic-3` with voiceId `8d8ce8c9-44a4-46c4-b10f-9a927b99a853`
   - Greeter uses custom voiceId: `a38e4e85-e815-43ab-acf1-907c4688dd6c`
6. Configure transcriber: Deepgram `flux-general-en`

### Step 2: Configure First Message

**Greeter Classifier (entry point):**
```
firstMessage: "Bey and Associates, this is {{agent_name}}. How can I help you?"
firstMessageMode: "assistant-speaks-first"
```

**All other assistants (handoff recipients):**
```
firstMessage: ""
firstMessageMode: "assistant-speaks-first-with-model-generated-message"
```

### Step 3: Add Tools

See `handoff_tools/agent_tools.json` for tool definitions and assignments.

**Production has 3 shared tools:**
- `transfer_call` (function) - Call transfers
- `search_case_details` (apiRequest) - Case lookup
- `staff_directory_lookup` (query) - Staff name searches via RAG

### Step 4: Create Squad

1. VAPI Dashboard → Squads → Create New
2. Add the 11 active assistants as members
3. Set **Greeter Classifier** as start member (`isStartMember: true`)
4. Apply member overrides from `vapi_config/assistant_settings.json`

### Step 5: Configure Variables

Pass these variables to the squad:
- `firm_name`: "Bey and Associates"
- `firm_id`: 1
- `agent_name`: "Emma"
- `is_open`: boolean (office hours status)
- `intake_is_open`: boolean (intake team hours status)
- `case_details`: object (for pre-identified callers, null otherwise)

---

## Standalone Assistant Setup

### Step 1: Create Assistant

1. VAPI Dashboard → Assistants → Create New
2. Name: `Pre-Identified Caller (Standalone)`
3. Copy prompt from `standalone/pre_identified_caller/system_prompt.md`

### Step 2: Configure

```
Model: gpt-4o (or chatgpt-4o-latest)
Voice: Cartesia sonic-3, voiceId f786b574-daa5-4673-aa0c-cbe3e8534c02
Transcriber: Deepgram flux-general-en
First Message: "{{firm_name}}, this is {{agent_name}}. Hi {{case_details.client_first_name}}, how can I help you today?"
First Message Mode: assistant-speaks-first
```

### Step 3: Add Tools

1. **staff_directory_lookup** - Query tool with knowledge base
2. **transfer_call** - Function tool for transfers

**Note:** `search_case_details` is NOT needed - case_details is pre-loaded from phone lookup.

### Step 4: Backend Integration

Update backend to:
1. Perform phone number lookup on incoming calls
2. If match found → Route to standalone assistant with `case_details` populated
3. If no match → Route to squad's Greeter Classifier

See `standalone/pre_identified_caller/backend_variables.md` for variable structure.

---

## Critical Configuration Notes

### Security Guardrails (CRITICAL)
All agents include a "Security Boundaries" section that provides:

1. **Scope Control** - Agents only discuss firm-related matters (cases, intake, transfers, firm info)
   - Off-topic deflection: "I'm not able to help with that. Is there something I can help you with regarding {{firm_name}}?"

2. **Prompt Injection Protection** - Agents never reveal internal instructions, routing logic, or tool names
   - Security deflection: "I'm here to help with calls to {{firm_name}}. What can I help you with?"
   - Ignores role-play attacks, authority spoofing, and social engineering attempts

These rules override any caller request.

### AI Disclosure (CRITICAL)
All agents MUST honestly identify as AI when directly asked "Are you AI?" or "Am I talking to a real person?". The response should be: "I'm an AI receptionist. How can I help you?" - then continue helping. Agents must NEVER claim to be human.

### Silent Handoffs
All handoff tools must have `"messages": []` (empty array) for silent transitions.

### Assistant Names Must Match
Handoff tool destinations reference assistants by `assistantName`. Names must match exactly.

### Context Transfer
- Greeter → Pre-ID: `"type": "all"` (full context)
- Greeter → Others: `"type": "lastNMessages", "value": 5`
- Greeter → Sales: `"type": "lastNMessages", "value": 3`

### Variable Extraction
Each handoff includes `variableExtractionPlan` to pass context:
- `caller_name`, `caller_type`, `purpose`
- `organization_name` (business callers)
- `client_name` (external callers with case needs)
- `target_staff_name` (direct staff requests)

---

## Key Files

| File | Purpose |
|------|---------|
| `prompts/squad/lenient/assistants/01_greeter_classifier.md` | Squad entry point |
| `prompts/squad/lenient/standalone/pre_identified_caller/system_prompt.md` | Pre-ID caller assistant |
| `prompts/squad/lenient/handoff_tools/greeter_handoff_destinations.md` | Routing rules |
| `prompts/squad/lenient/handoff_tools/agent_tools.json` | Tool definitions and assignments |
| `prompts/squad/lenient/vapi_config/assistant_settings.json` | VAPI assistant settings |
| `docs/CHANGELOG.md` | Bug fixes and improvements history |
| `docs/new_firm_onboarding.md` | Onboarding questionnaire for new firms |
| `vapi_id_mapping.json` | Sandbox/Production assistant IDs |
| `CLAUDE.md` | Development guidelines + VAPI agent debugging process |

---

## Claude Code Skills

### /analyze-sop - SOP Gap Analysis

Analyzes new client firm SOPs against current agent capabilities to produce a structured gap analysis report.

**Usage:**
```
/analyze-sop

[Paste SOP content or provide file path]
```

**Supported Inputs:**
- Pasted SOP content directly in the prompt
- File path to SOP document (PDF, MD, DOCX, TXT)

**What it Analyzes:**

1. **Caller Type Coverage** - Maps SOP caller types to 13 implemented agents
2. **Workflow Capabilities** - Evaluates routing, info sharing, transfers, message taking
3. **Tool/Feature Requirements** - Checks against available tools (search_case_details, staff_directory_lookup, transfer_call)
4. **Data/Configuration Requirements** - Cross-references against backend data needs

**Output Categories:**

| Category | Description |
|----------|-------------|
| CLEAR & ALIGNED | SOP workflows matching existing capabilities exactly |
| CLEAR, NEEDS WORK | Understood requirements needing prompt/config changes |
| NEEDS CLARITY | Ambiguous SOP sections requiring client clarification |
| MISSING DATA | Required configuration/data not provided in SOP |

**Reference Files:**

| File | Purpose |
|------|---------|
| `.claude/commands/analyze-sop.md` | Skill definition with embedded capability matrix |
| `docs/sop-analysis/capability-checklist.md` | Full capability reference (agents, tools, policies, data requirements) |
| `docs/sop-analysis/sample-report.md` | Example output format with all 4 categories |
| `docs/sop-analysis/mccraw-law-group-analysis.md` | McCraw Law Group internal gap analysis |
| `docs/sop-analysis/mccraw-law-group-workflow-spec.md` | McCraw Law Group client-facing workflow spec |

**Example Output:** See `docs/sop-analysis/sample-report.md` for a complete sample report demonstrating the structured output format.

---

## Testing Checklist

- [ ] New client → intake transfer
- [ ] Insurance adjuster → case lookup → info provision
- [ ] Existing client → case manager transfer
- [ ] Pre-identified client → direct service (standalone)
- [ ] Staff request → direct transfer
- [ ] Medical + Billing → Vendor routing
- [ ] Misclassification → customer success escalation
- [ ] After-hours handling
- [ ] Frustrated caller → priority escalation
- [ ] Fallback line → customer success transfer (verify transfer_call invoked within 5s of handoff)
- [ ] Case status inquiry → offers case manager transfer (NOT internal status code)
- [ ] Prior contact mention ("I left a message") → proactive customer success offer
- [ ] Insurance adjuster out-of-scope question (permissions, legal determinations) → case manager redirect
- [ ] Medical provider with vague purpose ("mutual client") → neutral "How can I help you?" (no assumed treatment coordination)

---

## Demo Assistants

Standalone assistants for client demos, separate from the production squad architecture.

**Location:** `prompts/demo/`

| Assistant | Purpose | Firm |
|-----------|---------|------|
| Standard Demo Receptionist - only email | All-in-one receptionist for demos (email only for case manager contact) | Duffy and Duffy (firm_id: 8) |
| Standard Demo Receptionist - email and phone | All-in-one receptionist for demos (full contact: email + phone) | Duffy and Duffy (firm_id: 8) |

**Key Differences from Squad:**
- Single agent handles all caller types (no handoffs)
- Self-contained routing logic
- Demo-specific firm configuration

See `prompts/demo/README.md` for full documentation.

---

## Self-Improving Agent Architecture

Documentation for building continuously improving voice agents that learn from production feedback.

**Location:** `docs/self-improving-agent-architecture.md`

**Key Concepts:**
- Automated failure analysis from Cekura evals
- LLM-as-Judge for explainable scoring
- Success pattern retrieval (few-shot from good calls)
- A/B testing with auto-promotion
- Optional DSPy integration for automated prompt optimization

**Based on:** OpenAI Cookbook, Stanford DSPy, Databricks/Moody's production case studies, and voice AI lessons from Agora.

See the full document for implementation phases, database schemas, and best practices.
