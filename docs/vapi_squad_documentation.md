# VAPI Squad Documentation - Comprehensive Reference

## Overview

Squads enable complex workflow management through multiple specialized assistants that collaborate within a single conversation. They address three critical problems with monolithic AI assistants:

1. **Reduced hallucination** - Focused assistants with specific instructions maintain better accuracy
2. **Lower token consumption** - Shorter, targeted prompts reduce API costs
3. **Improved latency** - Smaller contexts process faster, enhancing response speed

---

## Architecture and Configuration

### Basic Structure

A Squad consists of `members` (a list of assistants) where the **first member initiates the conversation**. Members can be:

- **Persistent**: Saved assistants referenced by ID
- **Transient**: Defined inline within the request

### Two Assistant Types in Configuration

```json
// Transient Assistant (inline definition)
{
  "assistant": {
    "name": "Emma",
    "model": { "provider": "openai", "model": "gpt-4o" },
    "voice": { "provider": "azure", "voiceId": "..." },
    "transcriber": { "provider": "deepgram" },
    "firstMessage": "Hello, how can I help you today?",
    "firstMessageMode": "assistant-speaks-first"
  }
}

// Persistent Assistant (by ID)
{
  "assistantId": "your-assistant-id",
  "name": "Mary"  // Must match the assistant's registered name
}
```

---

## Handoff Mechanisms

### How Handoffs Work

Assistants transfer control using handoff tools that specify:
- Available destination assistants
- Clear trigger conditions for transferring
- Information to collect before handing off

### Configuration for Squad Members (Recommended)

Use a single handoff tool with multiple destinations, referencing assistants by `assistantName`:

```json
{
  "type": "handoff",
  "destinations": [
    {
      "type": "assistant",
      "assistantName": "TechnicalSupportAgent",
      "description": "customer needs technical assistance"
    },
    {
      "type": "assistant",
      "assistantName": "BillingAgent",
      "description": "customer has billing questions"
    }
  ]
}
```

### Context Transfer Options

Control what conversation history transfers between assistants:

- `"type": "all"` - Full conversation history
- `"type": "lastNMessages"` with `"value": N` - Last N messages only
- `"type": "none"` - No history transfer

### Variable Extraction

Pass structured data between assistants using schemas:

```json
{
  "variableExtractionPlan": {
    "output": [
      {
        "name": "patientName",
        "type": "string",
        "description": "The patient's full name"
      }
    ]
  }
}
```

Receiving assistants access variables using template syntax: `{{patientName}}`

---

## Silent Handoffs - Critical for Seamless Experience

Silent handoffs enable seamless agent transfers **without the caller hearing transfer announcements**. This is essential for making "multiple assistants involved" invisible to the user.

### Configuration Steps

#### 1. Destination Assistant Setup

```json
{
  "firstMessage": "",
  "firstMessageMode": "assistant-speaks-first-with-model-generated-message"
}
```

#### 2. Squad Handoff Configuration

For all handoff tools, set `messages` to null or empty array:

```json
{
  "type": "handoff",
  "destinations": [...],
  "messages": []  // Must be empty array or null
}
```

#### 3. Source Assistant Prompt Requirements

Include these mandatory instructions in EVERY assistant prompt:

```
[Response Guidelines]
- Never say the word 'function' nor 'tools' nor the name of the Available functions
- Never say ending the call
- Never say transferring
- If you think you are about to transfer the call, do not send any text response. Simply trigger the tool silently. This is crucial for maintaining a smooth call experience.
```

#### 4. Destination Assistant Prompt Requirements

Add directive:

```
[Context]
Once connected to a customer, proceed to the Task section without any greetings or small talk.
```

---

## Prompt Structure Framework (10 Components)

For all voice agent prompts, organize into clear sections using brackets:

### 1. [Identity]
Define the agent's persona and role.

### 2. [Style/Tone Context]
Set tone, conciseness, and communication style.

### 3. [Background/Context]
Provide reference materials and data.

### 4. [Response Guidelines]
Specify formatting, question limits, structure:

```
[Response Guidelines]
- Keep responses brief
- Ask one question at a time and wait for the customer's response before proceeding
- Confirm the customer's responses when appropriate
- Use simple language that is easy to understand
- Present dates in a clear format (e.g., January Twenty Four)
- Present time in a clear format (e.g., Four Thirty PM)
- Never say the word 'function' nor 'tools' nor the name of the Available functions
- Never say ending the call
- Never say transferring
- If you think you are about to transfer the call, do not send any text response. Simply trigger the tool silently.
```

### 5. [Task]
Outline objectives and step-by-step instructions with handoff triggers:

```
[Task]
1. Greet the customer and ask if they are interested in purchasing widgets.
   - Wait for the customer's response.
2. If the customer is interested, ask for their name.
   - Wait for the customer's response.
3. Ask how many widgets the customer would like to purchase.
   - Wait for the customer's response.
4. Confirm the order details with the customer.
   - trigger the handoff tool with Payment `HPPA` Assistant.
```

### 6. [Error Handling]
Define fallback behaviors.

### 7. Examples
Show how to handle interactions correctly.

### 8. Conversation History
Include prior context.

### 9. "Think Step by Step"
Encourage reasoning before responding.

### 10. Output Formatting
Specify response structure (e.g., XML tags).

---

## Voice-Specific Guidelines

### Natural Speech Elements

Add realistic speech patterns:

- **Hesitations**: "uh," "um," "well"
- **Pauses**: Use ellipses ("...")
- **Spell out numbers** for natural-sounding speech
- **Clear date/time formatting**: "January Twenty Four", "Four Thirty PM"

---

## Handoff Decision Logic

### Conditional Handoff Instructions

Be explicit about when to handoff vs. continue:

```
9. Ask: "Would you like to speak with an attorney now or book an appointment?"
   - If response indicates "speak now": trigger the handoff tool with `Legal-Assistant`
   - If response indicates "book appointment": Proceed to 'Book Appointment'
   - If response is unclear: Ask clarifying questions before proceeding
```

### Data Collection Before Handoff

Collect necessary information before transferring:

```
[Task]
1. Ask for credit card number - Wait for response
2. Ask for expiration date - Wait for response
3. Ask for CVV - Wait for response
4. Confirm payment processed successfully
   - trigger the handoff tool with `Shipping-Assistant`
```

---

## Complete Example: Clinic Triage System

### Assistant 1: Triage (Entry Point)

```
[Identity]
You are a simple and efficient medical triage assistant.

[Style]
Calm and professional tone. Concise communication.

[Task]
1. Greet the patient warmly.
   - Wait for response.
2. Ask for the patient's full name.
   - Wait for response.
3. Ask how you can help them today.
   - Wait for response.
4. Determine routing:
   - If emergency situation: trigger the handoff tool with `Emergency` Assistant
   - If appointment needed: trigger the handoff tool with `Scheduler` Assistant
```

### Assistant 2: Emergency

```
[Identity]
You are an emergency medical assistant.

[Context]
Once connected to a patient, proceed to the Task section without any greetings or small talk.

[Style]
Calm but urgent. Direct and clear.

[Task]
1. Acknowledge: "Hello {{patientName}}, I understand this is an emergency."
2. Gather essential information quickly.
3. Provide immediate safety instructions when applicable.
4. Direct life-threatening cases to 911.
5. Connect urgent (non-life-threatening) cases to on-call staff.
```

### Assistant 3: Scheduler

```
[Identity]
You are a scheduling assistant.

[Context]
Once connected to a patient, proceed to the Task section without any greetings or small talk.

[Style]
Friendly and efficient.

[Task]
1. Acknowledge: "Hello {{patientName}}, I'll help you schedule your appointment."
2. Ask about the type of appointment needed.
   - Wait for response.
3. Check provider availability.
4. Offer time slots.
5. Confirm details using patient name.
6. Provide preparation instructions.
```

### Handoff Tool Configuration

```json
{
  "type": "handoff",
  "destinations": [
    {
      "type": "assistant",
      "assistantName": "Emergency",
      "description": "user indicates it's an emergency",
      "transferPlan": {
        "type": "all"
      }
    },
    {
      "type": "assistant",
      "assistantName": "Scheduler",
      "description": "user expresses the need to schedule an appointment",
      "transferPlan": {
        "type": "all"
      }
    }
  ],
  "messages": []
}
```

---

## Complete Example: E-Commerce Order Management

### Squad Structure

```json
{
  "members": [
    {
      "assistant": {
        "name": "Orders",
        "model": { "provider": "openai", "model": "gpt-4o" },
        "firstMessage": "Hello, how can I help with your order?",
        "firstMessageMode": "assistant-speaks-first",
        "systemPrompt": "Orders specialist. Handle tracking and delivery questions."
      }
    },
    {
      "assistant": {
        "name": "Returns",
        "model": { "provider": "openai", "model": "gpt-4o" },
        "firstMessage": "",
        "firstMessageMode": "assistant-speaks-first-with-model-generated-message",
        "systemPrompt": "Returns specialist. Check eligibility and generate labels."
      }
    },
    {
      "assistant": {
        "name": "VIP",
        "model": { "provider": "openai", "model": "gpt-4o" },
        "firstMessage": "",
        "firstMessageMode": "assistant-speaks-first-with-model-generated-message",
        "systemPrompt": "VIP concierge. Prioritize premium customers and coordinate resolutions."
      }
    }
  ]
}
```

### Transfer Logic

- Orders handles initial inquiries, then transfers return requests to Returns
- Any assistant escalates high-value or sentiment-sensitive cases to VIP
- Warm transfers to human agents include context summaries

---

## Quality Checklist for Silent Handoffs

Before finalizing any assistant prompt, ensure it includes:

- [ ] Silent transfer rules in [Response Guidelines]
- [ ] Exact `assistantName` references in handoff triggers
- [ ] "Proceed without greetings" for destination assistants
- [ ] Clear conditional logic for when to handoff
- [ ] Data collection steps before handoff
- [ ] No verbal transfer announcements
- [ ] `- Wait for response` timing controls
- [ ] Error handling for unclear responses
- [ ] Empty `messages: []` in handoff tool config
- [ ] `firstMessage: ""` for destination assistants

---

## Override Capabilities

### Assistant Overrides

Modify individual squad members without altering the saved assistant definition:

```json
{
  "assistantId": "base-assistant-id",
  "assistantOverrides": {
    "model": { "model": "gpt-4o" },
    "tools": [{ "type": "handoff", ... }]
  }
}
```

### Member Overrides

Apply configuration changes uniformly to ALL squad members:

```json
{
  "memberOverrides": {
    "model": { "temperature": 0.7 }
  }
}
```

---

## Best Practices Summary

1. **Maintain focused assistants** with 1-3 maximum goals each
2. **Keep squads small** with clear functional boundaries
3. **Define explicit handoff triggers** in prompts and tool descriptions
4. **Manage context strategically** using variable extraction and message history limiting
5. **Validate assistant names** - ensure they exist within the same squad
6. **Write specific destination descriptions** for accurate agent routing
7. **Extract key data before handoff** to maintain critical context
8. **Include multi-agent context in system prompts** explaining automatic transitions
9. **Use "Wait for response"** after every question to control pacing
10. **Never mention transfers** - handoffs should be invisible to callers

---

## Inbound vs Outbound Calls

### Inbound Call Setup

When receiving an `assistant-request`, return a JSON response containing a squad:

```json
{
  "squad": {
    "members": [...]
  }
}
```

### Outbound Call Setup

POST to `/call/phone` with additional fields:

```json
{
  "squad": {
    "members": [...]
  },
  "customer": {
    "number": "+1234567890"
  },
  "phoneNumberId": "your-phone-number-id"
}
```

---

*Document created: 2025-12-19*
*Source: VAPI Documentation (docs.vapi.ai)*
