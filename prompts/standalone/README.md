# Standalone Assistants

This directory contains VAPI assistants that operate independently from the main 13-agent squad.

---

## Pre-Identified Caller Assistant

**Purpose:** Handle callers whose phone number matches an existing client record, bypassing the main squad entirely.

**Location:** `pre_identified_caller/`

### Why Standalone?

The pre-identified caller workflow is fundamentally different from the main squad flow:
- **No classification needed** - the caller is already identified via phone lookup
- **No greeter handoff** - this assistant IS the entry point
- **Pre-loaded context** - case details are available immediately
- **Faster service** - no routing decision required

### Setup Instructions

#### Step 1: Create Assistant in VAPI Dashboard

1. Go to VAPI Dashboard → Assistants → Create New
2. Set **Name** to: `Pre-Identified Caller (Standalone)`

#### Step 2: Configure System Prompt

Copy the system prompt from `pre_identified_caller/system_prompt.md` (the section inside the triple backticks).

#### Step 3: Configure Model

```
Provider: OpenAI
Model: gpt-4o (or chatgpt-4o-latest)
Temperature: 0.7
Max Tokens: 250
```

#### Step 4: Configure Voice

```
Provider: Cartesia
Model: sonic-3
Voice ID: f786b574-daa5-4673-aa0c-cbe3e8534c02
```

#### Step 5: Configure Transcriber

```
Provider: Deepgram
Model: flux-general-en
```

#### Step 6: Set First Message

```
First Message: "{{firm_name}}, this is {{agent_name}}. Hi {{case_details.client_first_name}}, how can I help you today?"
First Message Mode: assistant-speaks-first
```

#### Step 7: Add Tools

Add these 2 tools:

1. **staff_directory_lookup**
   - Type: query
   - Knowledge Base: `Bey_and_associates_staff_directory`

2. **transfer_call**
   - Type: function
   - For transferring to case manager or customer_success

**Note:** `search_case_details` is NOT needed - case_details is pre-loaded from phone lookup.

#### Step 8: Configure Additional Settings

```
Silence Timeout: 30 seconds
Max Duration: 600 seconds
Background Sound: off
Backchanneling: enabled
Response Delay: 0.4 seconds
Words to Interrupt: 2
```

#### Step 9: Configure Backend Webhook

Update your backend to:
1. Perform phone number lookup on incoming calls
2. If match found → Route to this standalone assistant with `case_details` populated
3. If no match → Route to main squad's Greeter Classifier

See `pre_identified_caller/backend_variables.md` for the exact variable structure.

---

### Testing Checklist

- [ ] Case status inquiry → provides status, stops talking
- [ ] Transfer to case manager (business hours) → asks consent → transfers
- [ ] Transfer fails → warm fallback → takes message
- [ ] After hours call → takes message
- [ ] Wrong person on client's phone → routes to customer_success
- [ ] Client asks for case manager phone → provides from case_details
- [ ] Frustrated caller → acknowledges briefly, helps quickly

---

### Files

```
prompts/standalone/
├── README.md                           # This file
└── pre_identified_caller/
    ├── system_prompt.md                # Full system prompt + VAPI config
    └── backend_variables.md            # Variable documentation for backend
```

---

### Relationship to Main Squad

This standalone assistant **does not replace** the Pre-Identified Client agent in the main squad. The main squad can still handle pre-identified callers if the backend routes them there.

The standalone assistant is an **alternative entry point** for firms that want to:
- Simplify the call flow for known clients
- Reduce latency (no greeter classification step)
- Have a dedicated assistant for returning clients
