# Changelog

All notable changes to the VAPI Squad Prompts are documented in this file.

---

## [2026-01-02] - Call Quality Improvements

### Issue #1: Existing Client with New Matter Routed Incorrectly

**Problem:** An existing client (Ashley) called about opening a NEW medical malpractice case, but was routed to the Existing Client agent instead of the New Client agent. The system prioritized "I have a case with you" over "I want representation for a new case."

**Root Cause:** The handoff routing logic didn't handle the edge case where an existing client calls about a new/different legal matter.

**Files Changed:**

1. `squad_prompts_v3/handoff_tools/greeter_handoff_destinations.md`
   - Added to Existing Client "Do NOT use" section: existing client wanting representation for a NEW/DIFFERENT matter should go to New Client
   - Added to New Client triggers: existing clients opening a new/separate case
   - Added Priority Override Rule #6: "Existing Client + New Matter = New Client"

2. `squad_prompts_v3/assistants/06_new_client.md`
   - Updated Role description to include existing clients with new matters
   - Added [Special Context: Existing Client with New Matter] section
   - Fixed Misclassification Handling to distinguish between existing case inquiry vs new matter

---

### Issue #2: Greeter Collects Only First Name Before Handoff

**Problem:** When caller said only "Ashley", the Greeter immediately handed off without asking for last name. This caused the case search to return 6 matches instead of 1, requiring additional disambiguation.

**Root Cause:** The Greeter prompt only asked "May I have your name?" without specifying first AND last name, and didn't follow up when only first name was provided.

**Files Changed:**

1. `squad_prompts_v3/assistants/01_greeter_classifier.md`
   - Updated Step 2 title to "Get caller's FULL name (first AND last)"
   - Changed prompt from "May I have your name?" to "May I have your full name?"
   - Added instruction: if caller gives only first name, ask "And your last name?"
   - Added example showing the full name collection flow

2. `squad_prompts_v3/handoff_tools/greeter_handoff_destinations.md`
   - Updated Existing Client prerequisite: "You MUST have the caller's FULL name (first AND last)"
   - Updated Existing Client instructions to ask for last name if only first provided
   - Updated New Client prerequisite: "You MUST have the caller's FULL name (first AND last)"
   - Updated New Client instructions to ask for last name if only first provided

---

### Issue #3: Agent Fabricated Case Manager Name for Unhandled Scenario

**Problem:** Existing client (Melody Bedford) called to "reschedule appointment" - agent fabricated "Rushikesh" as case manager name without ever calling `search_case_details`. The agent improvised badly for a scenario it didn't know how to handle.

**Root Cause:** The Existing Client agent prompt only defined handling for case status, case manager contact, and speaking with case manager. When purpose didn't match these, the agent had no fallback instruction and hallucinated data.

**Solution:** For purposes that don't match handled scenarios, route directly to Customer Success (no case lookup, no clarifying questions, no staff names mentioned).

**Files Changed:**

1. `squad_prompts_v3/assistants/03_existing_client.md`
   - Added Step 0: Check if purpose requires case lookup
   - Handled purposes: case status, speak with case manager, case manager contact, questions about case
   - Unhandled purposes: Route immediately to Customer Success (during hours) or take message (after hours)

2. `squad_prompts_v3/assistants/02_pre_identified_client.md`
   - Added same Step 0 fallback logic for pre-identified clients

---

### Action Required: VAPI Dashboard Update

The above prompt changes need to be copied to the VAPI dashboard to take effect at runtime:
- Update the Greeter Classifier assistant prompt
- Update the New Client assistant prompt
- Update the Existing Client assistant prompt
- Update the Pre-Identified Client assistant prompt
- Update the handoff tool descriptions for all affected destinations

---

### Issue #4: Agent Said "Let me get you to someone" Without Making Transfer Call

**Problem:** Direct Staff agent received `target_staff_name: Lawyer` (a role, not a name) and output "Let me get you to someone who can assist with rescheduling your appointment. One moment, please." without calling any tool. This caused the "silence death" scenario where the system waited for user input and the call stalled.

**Root Cause:** The prompts had no fallback for when agents are uncertain or confused. When the model didn't know what to do, it improvised by outputting text without a tool call.

**Solution:** Added "[Fallback Principle - WHEN IN DOUBT]" section to all agents with `transfer_call`. Core principle: "When you don't know what to do, transfer to customer_success."

**Files Changed:**

1. `squad_prompts_v3/assistants/02_pre_identified_client.md` - Added fallback principle
2. `squad_prompts_v3/assistants/03_existing_client.md` - Added fallback principle
3. `squad_prompts_v3/assistants/04_insurance_adjuster.md` - Added fallback principle
4. `squad_prompts_v3/assistants/05_medical_provider.md` - Added fallback principle
5. `squad_prompts_v3/assistants/06_new_client.md` - Added fallback principle
6. `squad_prompts_v3/assistants/07_vendor.md` - Added fallback principle
7. `squad_prompts_v3/assistants/08_direct_staff_request.md` - Added fallback principle
8. `squad_prompts_v3/assistants/09_family_member.md` - Added fallback principle
9. `squad_prompts_v3/assistants/10_spanish_speaker.md` - Added fallback principle
10. `squad_prompts_v3/assistants/11_referral_source.md` - Added fallback principle
11. `squad_prompts_v3/assistants/12_legal_system.md` - Added fallback principle

---

### Action Required: VAPI Dashboard Update

The above prompt changes (Issue #4) need to be copied to the VAPI dashboard to take effect at runtime:
- Update all 11 assistant prompts listed above with the new fallback principle section

---

## [2026-01-05] - Spelling Protocol & Multi-Client Handling Improvements

### Issue #7: Agent Asks for Multiple Client Names Upfront Instead of One at a Time

**Problem:** When a caller from Medicare Recovery Solutions said "I'm following up regarding two of our clients," the agent asked "May I have the names of the clients?" (plural) and prompted for the second name when only one was provided. The ideal behavior is to handle one client at a time.

**Root Cause:** No explicit "one client at a time" instruction in the prompts. The LLM defaulted to being "helpful" by trying to collect all names upfront.

**Files Changed:**

1. `squad_prompts_v3/assistants/01_greeter_classifier.md`
   - Added "ONE CLIENT AT A TIME" rule to Step 4
   - Instructs agent to say "Sure, let's start with the first one. What's the client's name?"

2. `squad_prompts_v3/assistants/05_medical_provider.md`
   - Updated Multi-Case Handling section to handle one client at a time
   - Removed automatic transfer to customer_success for multiple cases

3. `squad_prompts_v3/assistants/04_insurance_adjuster.md`
   - Same changes as Medical Provider

---

### Issue #8: Agent Ignores Spelled Names and Uses Transcription Instead

**Problem:** When callers spell names letter-by-letter (e.g., "Graves, g-r-a-v-e-s"), the agent uses the transcribed spoken name ("Grace") instead of the spelled version ("Graves"). Also, agent calls search_case_details prematurely while caller is still spelling.

**Evidence:**
- Caller: "Graves, g-r-a-v-e-s" → Agent searched "Grace"
- Caller: "m i k i m i a" → Agent searched "Miki"
- Agent called search_case_details while caller was still spelling first name

**Root Cause:**
1. No instruction that spelled names are authoritative over transcription
2. No "wait for caller to finish speaking" rule
3. Spelling protocol only activated after failed search, not proactively when caller spells upfront

**Solution:** Added three new rules to all agents that collect names:
1. "SPELLED NAMES ARE AUTHORITATIVE" - Use what they spell, not what transcription heard
2. "DO NOT SEARCH WHILE CALLER IS SPEAKING" - Wait for caller to finish
3. Expanded spelling protocol to cover proactive spelling (caller spells without being asked)

**Files Changed:**

1. `squad_prompts_v3/assistants/01_greeter_classifier.md`
   - Added "SPELLED NAMES ARE AUTHORITATIVE" rule
   - Added "WAIT FOR COMPLETE NAME" rule

2. `squad_prompts_v3/assistants/05_medical_provider.md`
   - Added "DO NOT SEARCH WHILE CALLER IS SPEAKING" rule to Step 1
   - Expanded spelling protocol to cover proactive spelling

3. `squad_prompts_v3/assistants/04_insurance_adjuster.md`
   - Same changes as Medical Provider

4. `squad_prompts_v3/assistants/03_existing_client.md`
   - Added "DO NOT SEARCH WHILE CALLER IS SPEAKING" rule to Step 1
   - Expanded spelling protocol to cover proactive spelling

5. `squad_prompts_v3/assistants/12_legal_system.md`
   - Added "DO NOT SEARCH WHILE CALLER IS SPEAKING" rule to Step 2
   - Expanded spelling protocol to cover proactive spelling

6. `squad_prompts_v3/assistants/08_direct_staff_request.md`
   - Added "DO NOT SEARCH WHILE CALLER IS SPEAKING" rule to Step 1
   - Expanded spelling protocol to cover proactive spelling for staff_directory_lookup

---

### Action Required: VAPI Dashboard Update

The above prompt changes need to be copied to the VAPI dashboard to take effect at runtime:
- Update Greeter Classifier assistant prompt
- Update Medical Provider assistant prompt
- Update Insurance Adjuster assistant prompt
- Update Existing Client assistant prompt
- Update Legal System assistant prompt
- Update Direct Staff Request assistant prompt

---

## [2026-01-05] - Handoff Silence Bug Fix & Staff Directory Lookup Improvements

### Issue #6: Specialized Agent Goes Silent After Receiving Handoff

**Problem:** After Greeter handed off to the New Client agent, the New Client agent returned an empty response (`"content":""`, only 2 completion tokens). The caller heard nothing, and the call eventually timed out due to silence. The caller experienced this as being "put on hold" with no one ever picking up.

**Evidence from call logs:**
- 04:06:14 - Greeter calls `handoff_to_new_client`, tool returns "Handoff initiated"
- 04:06:17 - New Client agent makes LLM request, receives empty response
- Call dies from silence

**Root Cause:** The silence instruction in the prompt was ambiguous about **who** made the tool call:

```
⚠️ AFTER transfer_call SUCCEEDS = SAY NOTHING
When transfer_call returns "Transfer executed" or similar success:
- DO NOT speak any text - silence is correct
```

When the New Client agent received the handoff, its conversation history contained:
```json
{"role":"tool","content":"Handoff initiated."}
```

The LLM saw this tool result and pattern-matched it to the "say nothing after tool success" rule - even though:
1. That rule was meant for `transfer_call`, not incoming `handoff_to_*`
2. The tool call was made by the PREVIOUS agent (Greeter), not the New Client agent itself

Combined with `"firstMessage": ""` (empty) and instructions saying "DO NOT GREET THE CALLER", the LLM concluded it should output nothing.

**Solution:** Rewrote the silence instructions to explicitly scope them to the agent's OWN tool calls, and clarify that seeing "Handoff initiated" in history means the agent MUST speak (it's the destination, not the initiator).

**Before:**
```
⚠️ AFTER transfer_call SUCCEEDS = SAY NOTHING
When transfer_call returns "Transfer executed" or similar success:
- DO NOT speak any text - silence is correct
...
The conversation history contains "Handoff initiated" from an earlier agent-to-agent handoff. This is NOT something you should say. NEVER repeat it.
```

**After:**
```
⚠️ SILENCE RULES - ONLY APPLY TO YOUR OWN TOOL CALLS:

When YOU call transfer_call and it returns success ("Transfer executed" or similar):
- SAY NOTHING - silence is correct
- The transfer is happening - any text you output will interrupt it
- Do NOT say "Transfer executed", "Connecting you now", etc.

IMPORTANT - "Handoff initiated" in conversation history:
- This is from the PREVIOUS agent (Greeter) handing the call TO YOU
- You ARE the destination agent now - you MUST speak to continue the conversation
- The silence rule does NOT apply here - that was someone else's tool call
- Never repeat "Handoff initiated" aloud, but DO speak your first response to the caller
```

Also added to the handoff understanding section:
```
- You MUST speak to continue the conversation - the caller is waiting for you
```

**Files Changed:**

1. `squad_prompts_v3/assistants/02_pre_identified_client.md` - Fixed silence rule scoping
2. `squad_prompts_v3/assistants/03_existing_client.md` - Fixed silence rule scoping
3. `squad_prompts_v3/assistants/04_insurance_adjuster.md` - Fixed silence rule scoping
4. `squad_prompts_v3/assistants/05_medical_provider.md` - Fixed silence rule scoping
5. `squad_prompts_v3/assistants/06_new_client.md` - Fixed silence rule scoping
6. `squad_prompts_v3/assistants/07_vendor.md` - Fixed silence rule scoping
7. `squad_prompts_v3/assistants/08_direct_staff_request.md` - Fixed silence rule scoping
8. `squad_prompts_v3/assistants/09_family_member.md` - Fixed silence rule scoping
9. `squad_prompts_v3/assistants/10_spanish_speaker.md` - Fixed silence rule scoping
10. `squad_prompts_v3/assistants/11_referral_source.md` - Fixed silence rule scoping
11. `squad_prompts_v3/assistants/12_legal_system.md` - Fixed silence rule scoping

**Expected Effect:** Specialized agents will now correctly distinguish between:
- Incoming handoffs (from Greeter) → Agent MUST speak to continue the conversation
- Outgoing transfers (agent's own `transfer_call`) → Agent should stay silent while transfer completes

This prevents the "silence death" scenario where callers hear nothing after being handed off.

---

### Action Required: VAPI Dashboard Update

The above prompt changes (Issue #6) need to be copied to the VAPI dashboard to take effect at runtime:
- Update all 11 specialized assistant prompts with the new silence rule scoping

---

### Issue #5: Direct Staff Request Agent Searches with Role Names Instead of Person Names

**Problem:** When caller said "Lawyer" but then "I don't know" when asked for the specific name, the Greeter incorrectly handed off to Direct Staff Request with `target_staff_name: "Lawyer"`. The Direct Staff Request agent then called `staff_directory_lookup("Lawyer")` which returned 0 results, causing the call to spiral with repeated questions and eventually stalling.

**Root Cause:**
1. Greeter handoff logic didn't handle the scenario where caller mentions a role ("lawyer") and then says "I don't know" when asked for the specific name
2. Direct Staff Request prompt instructed "Call staff_directory_lookup IMMEDIATELY with whatever name you have" - which included non-names like "Lawyer"
3. No handling for general help requests ("front desk", "operator", "human") which should go to customer_success, not Direct Staff Request

**Files Changed:**

1. `squad_prompts_v3/assistants/01_greeter_classifier.md`
   - Added Step 4.5: Handle "General Help" Requests
   - Routes "front desk", "operator", "representative", "receptionist", "human", "a person", "someone" directly to customer_success

2. `squad_prompts_v3/handoff_tools/greeter_handoff_destinations.md`
   - Expanded Direct Staff Request "Do NOT use" section:
     - Added general help requests (front desk, operator, human, etc.) → route to customer_success
     - Added role + "I don't know" scenario → route to customer_success
   - Added "Role vs Name Detection" guidance with list of common roles/titles
   - Clarified that only ACTUAL person's names should trigger Direct Staff Request

3. `squad_prompts_v3/assistants/08_direct_staff_request.md`
   - Added Step 0: Check if target_staff_name is a Person's Name (CRITICAL)
   - Added list of common NON-NAME values (lawyer, attorney, case manager, front desk, etc.)
   - If target_staff_name matches any role → immediate transfer to customer_success without searching
   - Acts as safety net if Greeter incorrectly hands off with a role name

---

### Action Required: VAPI Dashboard Update

The above prompt changes need to be copied to the VAPI dashboard to take effect at runtime:
- Update the Greeter Classifier assistant prompt (Step 4.5)
- Update the Direct Staff Request assistant prompt (Step 0)
- Update the handoff tool descriptions for Direct Staff Request destination

---

### Issue #9: Agent Asks for Message Twice During Message-Taking Flow

**Problem:** When transfer to case manager failed (outside business hours), the agent asked for the caller's message twice:
1. First: "What would you like me to tell him?" (immediately after transfer failed)
2. Second: "What's the message you'd like me to pass to the lawyer?" (after collecting callback number)

The caller had already provided their message in response to the first question, but the agent re-asked after collecting the phone number.

**Evidence from call:**
- 11:49:00 - Transfer fails, agent says "What would you like me to tell him?"
- 11:49:09 - Caller explains their situation (this IS the message)
- 11:49:22 - Agent asks "What's your callback number?"
- 11:49:30 - Agent asks "What's the message you'd like me to pass to the lawyer?" ← WRONG

**Root Causes:**
1. Error handling section asked for message first, but message-taking protocol asked for phone first (sequence conflict)
2. No explicit tracking or guidance to recognize caller's response as "the message"
3. LLM treated caller's explanation as context/background, not the actual message content

**Solution:**
1. Updated error handling to ask for message immediately AND include worked examples showing the complete conversation flow
2. Reordered message-taking protocol: message first, then callback number
3. Added explicit anti-pattern example showing the wrong behavior to avoid
4. Added gentle probe for vague "just call me back" responses
5. Added guidance for handling "lawyer" requests (stay with case manager routing)

**Files Changed:**

1. `squad_prompts_v3/assistants/03_existing_client.md`
   - [Error Handling]: Added complete worked example of transfer-fail → message-taking flow
   - [Error Handling]: Added explicit warning that caller's response IS the message
   - [Error Handling]: Added example for handling vague responses with gentle probe
   - [Message Taking - Inline]: Reordered to message-first, then callback number
   - [Message Taking - Inline]: Added anti-pattern example showing what NOT to do
   - [Message Taking - Inline]: Added handling for "lawyer" requests

---

### Action Required: VAPI Dashboard Update

The above prompt changes (Issue #9) need to be copied to the VAPI dashboard to take effect at runtime:
- Update the Existing Client assistant prompt with the new [Error Handling] and [Message Taking - Inline] sections
