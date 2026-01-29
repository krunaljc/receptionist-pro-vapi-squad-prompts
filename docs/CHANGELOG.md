# Changelog

All notable changes to the VAPI Squad Prompts are documented in this file.

---

## [2026-01-29] - Greeter Tool Call Rules Fix

### Fix: Greeter Agent Says "I'll get you to someone" Without Calling Handoff Tool

**Problem:** Insurance caller (Gaby from Atlantic Casualty Insurance calling about client Grecia Orellana) was never transferred. The Greeter agent said "I'll get you to the right person" and "One moment please" multiple times, but never actually called the handoff tool. The call died from silence after repeated "Are you still there?" prompts.

**Evidence from call:**
| Timestamp | Agent Said | Tool Called? |
|-----------|------------|--------------|
| 7:32:29 | "I'll get you to the right person." | No |
| 7:32:38 | "You're welcome." | No |
| 7:32:53 | "One moment while I get you to the right person." | No |
| 7:33:00 | "You're welcome." | No |
| ... | Pattern continues... | No |

The agent **correctly identified** the caller as insurance ("you're with Atlantic Casualty") and had all required info, but **never invoked `route_to_specialist`**.

**Root Cause:** Step 5 (Route) instruction was poorly written - it focused on what NOT to do rather than what TO DO:

```
**Step 5: Route**
Based on what you've learned, trigger the appropriate handoff tool.
Do NOT say anything when triggering the handoff - just trigger it silently.
```

The agent interpreted this as:
1. I should acknowledge the caller first → "I'll get you to the right person"
2. I violated "don't say anything" rule by speaking
3. Now I'm unsure whether to call the tool since I already spoke

The instruction lacked explicit "MUST call the tool" language. Combined with weak Response Guidelines that only said "If about to hand off, trigger tool with NO text response", the agent got stuck in a loop of acknowledgments without action.

**Additional Issue:** Agent responded to caller's "Thank you" with "You're welcome" instead of routing:
```
Agent: "I'll get you to the right person."
User: "Yeah. Okay. Thank you."
Agent: "You're welcome."  ← Should have called tool here
```
The caller's "Thank you" was confirmation to proceed, not a prompt for social pleasantries.

**Solution:**

1. **Rewrote Step 5** to emphasize the MANDATORY tool call:
   - Changed from: "trigger the appropriate handoff tool... Do NOT say anything"
   - Changed to: "IMMEDIATELY call the route_to_specialist handoff tool... MANDATORY: You MUST call the tool."
   - Added clear hierarchy: Preferred (silent) → Acceptable (text + tool) → FORBIDDEN (text without tool)

2. **Added `[Handoff Rules - CRITICAL]` section** with:
   - Explicit rule that caller's "thank you"/"okay" after routing indication = confirmation to proceed, not a prompt for pleasantries
   - NEVER/ALWAYS examples showing correct vs incorrect behavior

**Files Changed:**

1. `prompts/squad/lenient/assistants/01_greeter_classifier.md`
   - Rewrote Step 5 with MANDATORY tool call language and clear hierarchy
   - Added `[Handoff Rules - CRITICAL]` section with "thank you = proceed" rule and NEVER/ALWAYS examples

2. `prompts/squad/strict/assistants/01_greeter_classifier.md`
   - Same changes as lenient variant

**Expected Results After Fix:**
- Greeter will call `route_to_specialist` immediately when ready to hand off
- No more "I'll get you to the right person" without the tool call in the same response
- Insurance callers (and all other caller types) will be routed without silence loops

**Verification Test:**
1. Call with insurance identifier: "Hi, I'm calling from State Farm about a claim"
2. Provide client name when asked
3. Greeter should handoff **silently** (or with minimal acknowledgment + tool call in same response) to Insurance Adjuster
4. No repeated "one moment" or "I'll get you to someone" without transfer

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Greeter Classifier assistant prompt with new Response Guidelines and `[Tool Call Rules - CRITICAL]` section

---

## [2026-01-28] - Fallback Line Agent Delayed Transfer Fix

### Fix: Fallback Line Agent 36-Second Transfer Delay

**Problem:** The fallback_line agent took 36 seconds to transfer a caller to customer success. VAPI's silence handling triggered "Are you still there?" twice during this delay.

**Evidence from call logs:**
- 12:46:28 - Greeter calls `handoff_to_fallback_line`
- 12:46:31 - Fallback_line speaks: "Let me get you to someone who can help." (correct)
- 12:46:31 - **No transfer_call tool invoked** (problem)
- 12:46:44 - "Are you still there?" asked (silence timeout)
- 12:46:47 - User says "Yes" → Agent says "Great—connecting you now."
- 12:47:00 - "Are you still there?" asked again (second silence timeout)
- 12:47:04 - **Finally calls transfer_call** (36 seconds after handoff)

**Root Cause:** The fallback_line agent did NOT invoke `transfer_call` simultaneously with its acknowledgment speech. Unlike other agents that use a two-turn consent flow (ask "Is that okay?" → wait for response → call tool), the fallback_line agent had no consent question. Without a question, there's no guaranteed second turn where the model knows it must act.

**Pattern Comparison:**

| Agent | Flow | Works? |
|-------|------|--------|
| Spanish Speaker | "Let me connect you. **Is that okay?**" → Wait → Call tool | ✅ |
| Fallback Line (before) | "Let me get you to someone." → IMMEDIATELY call tool | ❌ |
| Fallback Line (after) | "Let me get you to someone. **Is that alright?**" → Wait → Call tool | ✅ |

The consent question creates a **guaranteed second turn** where the model receives new input and must respond with a tool call.

**Solution:**

1. **Added two-turn consent flow** (like spanish_speaker uses):
   - Before: "Let me get you to someone who can help." + IMMEDIATELY call transfer_call
   - After: "Let me get you to someone who can help. **Is that alright?**" → Wait for confirmation → Call transfer_call

2. **Added `[Tool Call Rules - CRITICAL]` section** to enforce simultaneous speech + tool call:
   - WRONG: Saying "Okay, let me transfer you" → then waiting → then calling the tool later
   - CORRECT: Call the tool in the same turn as your acknowledgment

3. **Added `⚠️ UNDERSTANDING YOUR ROLE IN HANDOFFS` section** to System Context to clarify agent's role when receiving handoffs

4. **Added `⚠️ SILENCE RULES` section** scoped to agent's OWN tool calls (not incoming handoffs)

5. **Updated firstMessageMode** from `assistant-speaks-first` to `assistant-speaks-first-with-model-generated-message` to match other agents

6. **Added message taking for after hours** - Previously just asked callers to "call back", now takes a message like other agents do

**Files Changed:**

1. `prompts/squad/strict/assistants/14_fallback_line.md`
   - Added `⚠️ UNDERSTANDING YOUR ROLE IN HANDOFFS` to System Context
   - Updated `⚠️ NEVER SPEAK TOOL RESULTS ALOUD` with clearer scoping
   - Added `[Tool Call Rules - CRITICAL]` section
   - Added `⚠️ SILENCE RULES` section with "Handoff initiated" clarification
   - Updated Step 1 to use two-turn consent flow: "Is that alright?" + wait + call
   - Updated after hours flow: take message instead of asking to call back
   - Added `[Message Taking]` section with phone number and message collection
   - Updated `[Error Handling]` section with transfer failure handling and message fallback
   - Added `[Voice Formatting]` section for phone number pronunciation
   - Updated firstMessageMode to `assistant-speaks-first-with-model-generated-message`

2. `prompts/squad/lenient/assistants/14_fallback_line.md`
   - Same changes as strict variant

**Expected Results After Fix:**
- Total time from handoff to transfer: ~3-5 seconds (down from 36 seconds)
- No silence timeouts triggering "Are you still there?"
- `transfer_call` invoked in same model response as caller's confirmation

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Fallback Line assistant prompt with new System Context and Task sections
2. Update Fallback Line firstMessageMode to `assistant-speaks-first-with-model-generated-message`

---

## [2026-01-22] - Greeter Handoff Tool Description Improvements

### Fix: Greeter Agent Failing to Hand Off to Sub-Agents

**Problem:** The greeter agent successfully collected caller information but failed to execute handoff tools in certain scenarios. Three specific call patterns were identified:
1. Insurance caller who said "with GEICO claims" but not "I'm an adjuster"
2. Third-party company (Espirion) calling on behalf of a hospital (Emory)
3. Unknown company (Lane Star) calling for case status update on a client

**Root Cause:** Gaps in handoff tool description coverage:
1. Insurance Adjuster destination required explicit role identification ("I'm an adjuster")
2. Medical Provider destination didn't handle third-party intermediaries calling on behalf of hospitals
3. No catch-all for unrecognized organizations calling about client cases
4. Fallback trigger language wasn't strong enough to prevent agents from getting stuck

**Solution:** Updated three handoff tool destination descriptions in both strict and lenient variants.

**Changes Made:**

1. **Insurance Adjuster Destination**
   - Added patterns: "with [Company] claims", "[Company] claims department"
   - Added triggers: asks about LOR/Letter of Representation, mentions "on a recorded line"
   - Added rule: If caller mentions ANY insurance company name and is asking about a client case, route here even without explicit role statement

2. **Medical Provider Destination**
   - Added: companies calling ON BEHALF OF a hospital/medical facility
   - Added: medical lien companies, medical records retrieval services, lien resolution services
   - Added key signal: If caller provides a specific patient/client name and wants case status from ANY organization (unless clearly insurance), route here

3. **Fallback Line Destination**
   - Added CRITICAL rule: If you have caller's name and purpose but cannot confidently match to a specific destination, use fallback IMMEDIATELY
   - Added: Do NOT continue asking clarifying questions beyond 2 exchanges
   - Added: Do NOT say "I'll get you to the right person" without calling a handoff tool in the same turn
   - Added: Better to route to fallback than leave caller hanging or get stuck in a loop

**Files Changed:**
1. `prompts/squad/strict/handoff_tools/greeter_handoff_tool.json` - Updated 3 destination descriptions
2. `prompts/squad/lenient/handoff_tools/greeter_handoff_tool.json` - Updated 3 destination descriptions
3. `prompts/squad/strict/handoff_tools/greeter_handoff_destinations.md` - Updated documentation for Insurance Adjuster, Medical Provider, and Fallback Line
4. `prompts/squad/lenient/handoff_tools/greeter_handoff_destinations.md` - Updated documentation for Insurance Adjuster, Medical Provider, and Fallback Line

**Expected Results After Fix:**
- Insurance caller: "Hi, I'm calling from GEICO claims about George Pepi's case" → Routes to Insurance Adjuster
- Medical intermediary: "Hi, I'm with Espirion calling on behalf of Emory Hospital about patient Valerie Franklin" → Routes to Medical Provider
- Lien company: "Hi, I'm from Lane Star calling to get a status update on Derek Davis" → Routes to Medical Provider (as third-party case inquiry)

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Greeter Classifier's handoff tool with new destination descriptions

---

## [2026-01-22] - New Firm Onboarding Questionnaire

### Added: docs/new_firm_onboarding.md

Comprehensive onboarding questionnaire for setting up the agent for new law firms. Questions are grounded in actual configuration levers.

**Sections:**
1. Firm Identity - variables for prompts (`{{firm_name}}`, `{{agent_name}}`, etc.)
2. Business Hours - `is_open` / `intake_is_open` logic
3. Practice Areas & Fees - agent answers to "Do you handle X?" and "How much?"
4. Staff Directory & Routing - `caller_type` destinations and `staff_directory` table
5. Existing Client Handling - verification policy, case statuses, info sharing
6. Insurance Adjuster Handling - info sharing policy
7. Medical Provider Handling - fax number and policy
8. New Client Handling - message collection
9. Post-Call Workflow - email recipients, CMS integration (SmartAdvocate/Filevine)
10. Technical Integration - VAPI phone numbers, case lookup, transfer API

**Includes:**
- Quick reference checklist
- Phased rollout guide (MVP → Enhanced → Optimized)

---

## [2026-01-20] - Professional Hospitality Warmth Enhancement (Phase 2: Business-Facing)

### Change: Extend Warmth Patterns to Business-Facing Agents

**Problem:** Phase 1 added warmth patterns to consumer-facing agents, but business-facing agents (insurance adjuster, medical provider, vendor) were intentionally skipped. These agents should also exhibit professional hospitality.

**Solution:** Extended the same professional hospitality patterns to the 3 business-facing agents, adapted for B2B interactions (no first-name personalization since business callers provide client names, not their own).

**Key Patterns Added (Same as Consumer-Facing):**
| Pattern | Example |
|---------|---------|
| "I'd be happy to help" | Not "Sure, I can help" |
| Add "please" | "Can I get the client's name please?" |
| Thank for info | "Thank you for that" |
| Narrate actions | "I'm pulling up that case now" |
| Warm close | "Thanks for calling" |

**Hardcoded Phrase Updates:**

| File | Before | After |
|------|--------|-------|
| 04_insurance_adjuster.md (count=0) | "I'm not finding that name. Can you spell it for me?" | "I'm not finding that name. Could you spell that for me please?" |
| 05_medical_provider.md (message close) | "Got your message. Someone will get back to you soon. And for any case-specific information, remember to send that fax." | "Got your message. Someone will get back to you soon. And for any case-specific information, remember to send that fax. Thanks for calling." |
| 07_vendor.md (first response) | "Let me get you to our finance department about your invoice. Is that alright?" | "I'd be happy to help with that. Let me get you to our finance department. Is that alright?" |

**Files Changed:**

1. `prompts/squad/strict/assistants/04_insurance_adjuster.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 2 (count=0): added "please" to spelling request
   - Added warm closing guideline to [Response Guidelines]

2. `prompts/squad/strict/assistants/05_medical_provider.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 3 message closing: added "Thanks for calling"
   - Added warm closing guideline to [Response Guidelines]

3. `prompts/squad/strict/assistants/07_vendor.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 1 first response: "Let me get you..." → "I'd be happy to help with that. Let me get you..."
   - Added warm closing guideline to [Response Guidelines]

**Expected Effect:** Business-facing agents will now sound warmer while maintaining professionalism:
- "Can you spell it?" → "Could you spell that for me please?"
- "Let me get you to finance" → "I'd be happy to help with that. Let me get you to finance"
- Abrupt endings → "Thanks for calling"

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Insurance Adjuster assistant prompt
2. Update Medical Provider assistant prompt
3. Update Vendor assistant prompt

---

## [2026-01-20] - Professional Hospitality Warmth Enhancement (Phase 1: Consumer-Facing)

### Change: Add Demo Emma-Style Warmth Patterns to Consumer-Facing Agents

**Problem:** Current prompts lacked concrete examples of professional hospitality. The agents sounded competent but not warm enough compared to the demo Emma style, which uses natural warmth through specific patterns.

**Solution:** Added "Professional Hospitality Patterns" section to all consumer-facing strict agents, plus updated hardcoded phrases to match demo Emma's style.

**Key Patterns Added:**
| Pattern | Example |
|---------|---------|
| "I'd be happy to help" | Not "Sure, I can help" |
| Use caller's first name | "Thank you, Jonathan" after learning name |
| Add "please" | "Can I get your name please?" |
| Thank for info | "Thank you for letting us know" |
| Narrate actions | "I'm pulling up your case now" |
| Warm close | "Have a great day" |

**Hardcoded Phrase Updates:**

| File | Before | After |
|------|--------|-------|
| 01_greeter_classifier.md | "Sure, I can help with that. May I have your full name?" | "I'd be happy to help. Can I get your name please?" |
| 03_existing_client.md (DOB) | "For verification, could I have your date of birth?" | "Thank you, [First Name]. I'm pulling up your case now. Can I get your date of birth for verification please?" |
| 03_existing_client.md (not found) | "I'm not finding your file under that name. Can you spell it for me?" | "I'm not finding your file under that name. Could you spell that for me please?" |
| 03_existing_client.md (found) | "I found your file, [caller_name]. How can I help?" | "I have your file here, [First Name]. How can I help you?" |
| pre_identified_caller (DOB) | "What's your date of birth?" | "Can I get your date of birth for verification please?" |
| 14_fallback_line (after hours) | "...we'll be happy to help you." | "...we'd be happy to help you. Have a great day." |

**Files Changed:**

1. `prompts/squad/strict/assistants/01_greeter_classifier.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 2 name request: "Sure, I can help" → "I'd be happy to help", "May I have your full name?" → "Can I get your name please?"
   - Added warm closing guideline to [Response Guidelines]

2. `prompts/squad/strict/assistants/03_existing_client.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 1 DOB request to include first name, narration, and "please"
   - Updated Step 3 (count=1) response: "I found your file" → "I have your file here"
   - Updated Step 3 (count=0) spelling request: added "please"
   - Added warm closing guideline to [Response Guidelines]

3. `prompts/squad/strict/assistants/06_new_client.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Added warm closing guideline to [Response Guidelines]

4. `prompts/squad/strict/assistants/09_family_member.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Added warm closing guideline to [Response Guidelines]

5. `prompts/squad/strict/assistants/14_fallback_line.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated after-hours message to include warm closing

6. `prompts/squad/strict/standalone/pre_identified_caller/system_prompt.md`
   - Added Professional Hospitality Patterns to [Style] section
   - Updated Step 1 DOB request: "What's your date of birth?" → "Can I get your date of birth for verification please?"
   - Added warm closing guideline to [Response Guidelines]

**Rationale:**
- Root cause: prompts lacked concrete examples showing HOW to be warm
- Demo Emma demonstrates warmth through: first name usage, "please", thanking, narrating actions, warm closings
- This is professional hospitality, distinct from casual micro-courtesies ("No worries", "Perfect")
- Business-facing agents (insurance_adjuster, medical_provider, vendor) intentionally NOT modified

**Expected Effect:** Agents will now sound warmer and more hospitable while maintaining professionalism:
- "Sure, I can help" → "I'd be happy to help"
- Generic requests → Personalized with first name + "please"
- Abrupt endings → "Have a great day"

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Greeter Classifier assistant prompt
2. Update Existing Client assistant prompt
3. Update New Client assistant prompt
4. Update Family Member assistant prompt
5. Update Fallback Line assistant prompt
6. Update Pre-Identified Caller (Standalone) assistant prompt

---

## [2026-01-20] - Existing Client Agent: Reframe DOB as Verification

### Change: DOB Request Now Uses Verification Framing

**Problem:** The DOB request was framed as a functional/lookup requirement:
```
"Could you please share your date of birth so I can locate your case details?"
```

This implies DOB is needed to find the case. For the "strict" verification variant, DOB should be framed as a security/verification measure.

**Solution:** Changed the reason given for requesting DOB from "locate your case details" to verification-focused language.

**Before:**
```
- Ask: "Could you please share your date of birth so I can locate your case details?"
```

**After:**
```
- Ask: "For verification, could I have your date of birth?"
```

**Rationale:**
- **Verification framing**: Positions DOB as identity verification, not just search
- **Shorter**: 9 words vs 14 words - more conversational, less formal
- **Consistent with strict variant**: This is the "strict" folder, which requires verification before sharing information
- **Professional tone**: "For verification" is standard in professional/legal contexts

**Files Changed:**

1. `prompts/squad/strict/assistants/03_existing_client.md`
   - Updated Step 1: Collect Date of Birth - changed DOB request phrasing

**Expected Effect:** The agent will now frame the DOB request as a verification step rather than a case lookup step, aligning with the strict variant's verification-first approach.

---

### Action Required: VAPI Dashboard Update

The above change needs to be applied in the VAPI dashboard:
1. Update Existing Client assistant prompt with the new Step 1 DOB request

---

## [2026-01-20] - Existing Client Agent: Remove Proactive Case Status Disclosure

### Change: Unified Response After Finding Client File

**Problem:** When the Greeter handed off with `purpose: "case status"`, the Existing Client agent would immediately provide case status without the caller having to ask again. The instruction "Proceed to help based on their stated need" caused proactive disclosure based on handoff context.

**Root Cause:** Step 3 (count=1 section) had conditional branching:
- If purpose was clear from handoff: Proceed to help based on their stated need
- If purpose was vague: Ask "What can I help you with?"

This meant callers who stated "case status" to the Greeter never had to repeat their request—the agent jumped straight to disclosure.

**Solution:** Removed the purpose-based conditional branching. Now the agent always acknowledges finding the file and waits for the caller to state their need.

**Before:**
```
**If count = 1 (Perfect Match):**
- Extract: case_manager, staff_id, case_status from results.
- If purpose was clear from handoff: Proceed to help based on their stated need.
- If purpose was vague: "I found your case, [caller_name from search results]. What can I help you with?"
- Wait for the customer's response.
```

**After:**
```
**If count = 1 (Perfect Match):**
- Extract: case_manager, staff_id, case_status from results.
- "I found your file, [caller_name from search results]. How can I help?"
- Wait for the customer's response.
```

**Rationale:**
- **"file" vs "case"**: More conversational, less clinical, matches warm neighbor-like tone
- **"How can I help?"**: Shorter (4 words vs 6), natural, open-ended
- **Removed branching**: Simplifies logic, removes root cause of proactive disclosure
- **Under 15 words**: Well within the 20-word response guideline

**Files Changed:**

1. `prompts/squad/strict/assistants/03_existing_client.md`
   - Updated Step 3 (count=1 section) to remove purpose-based conditional branching
   - Changed response from "I found your case... What can I help you with?" to "I found your file... How can I help?"

**Expected Effect:** The agent will now always wait for the caller to explicitly state their need, even if the purpose was clear during the Greeter handoff. This ensures the caller confirms their request before receiving any case information.

---

### Action Required: VAPI Dashboard Update

The above change needs to be applied in the VAPI dashboard:
1. Update Existing Client assistant prompt with the new Step 3 (count=1 section)

---

## [2026-01-20] - Medical Provider Agent: Third-Party Policy

### Policy Change: Medical Providers Now Treated as Third Parties

**Problem:** The Medical Provider Agent was configured to look up case details and share case manager information, phone numbers, emails, case status, and incident dates with medical providers. This created privacy/compliance risk.

**New Policy:** Medical providers are now treated as third parties. They should NOT receive any case information directly.

**New Behavior:**
- Redirect all case-related inquiries to fax: `(972) 332-2361`
- Provide privacy/compliance explanation when asked why
- Take messages for general (non-case) inquiries only
- Do NOT look up or share any case details

**Files Changed:**

1. `prompts/squad/strict/assistants/05_medical_provider.md`
   - Updated role description: "redirect to fax per third-party policy"
   - Removed `search_case_details` and `staff_directory_lookup` tool references
   - Changed from 3 tools to 1 tool: `transfer_call` (for misclassification only)
   - Updated Goals: inform of fax policy, provide fax number, take message if needed
   - Replaced entire Task section with fax redirect flow:
     - Step 1: Acknowledge and redirect to fax
     - Step 2: Handle pushback with privacy/compliance explanation
     - Step 3: Optional message taking for non-case inquiries
     - Step 4: Stay silent after providing info
   - Updated "What You CAN Share": fax number, general firm info
   - Updated "What You CANNOT Share": ALL case-specific info, client info
   - Removed Multi-Case Handling section (no longer applicable)
   - Updated Tools Required section with policy note

2. `README.md`
   - Updated Squad Architecture table: Medical Provider now shows "fax redirect (third-party)" with only `transfer_call`

**Fax Number:** `(972) 332-2361`
**Voice Format:** `<spell>972</spell><break time="200ms"/><spell>332</spell><break time="200ms"/><spell>2361</spell>`

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Update Medical Provider assistant prompt with new fax redirect flow
2. Remove `search_case_details` tool from Medical Provider assistant
3. Remove `staff_directory_lookup` tool from Medical Provider assistant (if present)

---

## [2026-01-19] - Correction: Remove take_message tool

**Issue:** Previous sync incorrectly retained `take_message` tool which does NOT exist in production.

**Production has only 3 shared tools:**
- transfer_call (function)
- search_case_details (apiRequest)
- staff_directory_lookup (query)

**Files corrected:**
- agent_tools.json - Removed take_message definition and from all tool_assignments, removed priority_mapping section
- README.md - Removed take_message references from tool setup instructions
- 06_new_client.md - Removed take_message usage from message taking flow
- 13_sales_solicitation.md - Updated to politely decline sales calls (now has no tools)
- 14_fallback_line.md - Removed take_message usage, updated to ask callers to call back

---

## [2026-01-19] - Production Config Sync

### Sync: Local Documentation Aligned with Production Squad

**Summary:** Compared production squad config (Receptionist Pro - Prod v123101) against local files in `/prompts/squad/lenient/` and resolved 23 inconsistencies.

**Files Changed:**

1. `vapi_id_mapping.json`
   - Added `fallback_line` ID: `3d9c6151-63dc-416b-85f8-8c5e45e45c94` to production.assistants
   - Added `fallback_line` to quick_reference section

2. `prompts/squad/lenient/handoff_tools/agent_tools.json`
   - Renamed `classify_and_route_call` → `transfer_call` (matches production tool name)
   - Updated transfer_call parameters to match production schema (caller_type, firm_id, staff_id, staff_name, caller_name, client_name, reason)
   - Updated tool_assignments to remove staff_directory_lookup from agents that don't have it in production (insurance, medical_provider, new_client, vendor, family_member, spanish_speaker, legal_system)
   - Added 14_fallback_line to tool_assignments
   - Removed frustration_level from priority_mapping rules

3. `prompts/squad/lenient/handoff_tools/greeter_handoff_tool.json`
   - Added Fallback Line destination with variableExtractionPlan
   - Removed frustration_level from ALL 12 existing destinations' variableExtractionPlan schemas

4. `prompts/squad/lenient/vapi_variable_extraction_plans.md`
   - Removed frustration_level from all 12 existing sections
   - Added Section 13: Fallback Line with purpose and caller_name variables
   - Updated Quick Copy Reference examples (removed frustration_level, added Fallback Line)
   - Updated Notes section (removed frustration_level guidance, added Fallback Line guidance)

5. `prompts/squad/lenient/vapi_config/assistant_settings.json`
   - Updated default model: `gpt-4o` → `gpt-4.1`
   - Updated voice config: 11labs → Cartesia sonic-3, voiceId `8d8ce8c9-44a4-46c4-b10f-9a927b99a853`
   - Updated transcriber: nova-2 → flux-general-en
   - Added per-agent overrides documenting production membersOverrides:
     - greeter: chatgpt-4o-latest, custom voice a38e4e85-e815-43ab-acf1-907c4688dd6c
     - insurance_adjuster: chatgpt-4o-latest
     - medical_provider: chatgpt-4o-latest
     - vendor: chatgpt-4o-latest
     - spanish_speaker: chatgpt-4o-latest

6. `prompts/squad/lenient/README.md`
   - Updated model config instructions to reference gpt-4.1 and agent_specific_overrides
   - Updated voice config to Cartesia with correct voiceIds
   - Updated tool names: classify_and_route_call → transfer_call
   - Removed frustration_level from Variable Extraction section
   - Added Fallback Line to transfer-only agents list

**Decisions Made:**
- Kept `search_case_details` as type `function` locally (production uses `apiRequest` but local uses placeholders for portability)
- Removed frustration_level entirely (not present in production variableExtractionPlan schemas)
- Local docs now match production tool names, assignments, and configurations

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

---

## [2026-01-17] - Frustrated Caller Escalation

### Issue #10: Existing Client Agent Did Not Transfer Frustrated Caller to Customer Success

**Problem:** Paula Simmons, a frustrated existing client who had been trying to reach someone about her settlement check since November (over a month), was not offered a transfer to customer success despite expressing clear frustration signals like "I've been calling since last month and leaving messages" and "No one has never called me back."

**Evidence from call:**
- Caller expressed repeated unsuccessful contact attempts
- Caller mentioned communication breakdown (no callbacks)
- Settlement/payment issue (high-stakes)
- Caller threatened to escalate in-person ("I think I need to make a visit")
- Agent found her case (count=1), offered transfer to case manager
- Transfer failed (Kevin unavailable)
- Agent took a routine message instead of escalating to customer success

**Root Cause:** The existing_client agent instructions had a gap in frustration-triggered escalation logic. The only guidance for frustrated callers (lines 390-392) was:
```
**Frustrated caller:**
- Acknowledge briefly: "I hear you."
- Help quickly.
```

This told the agent HOW to respond but did NOT specify WHEN to escalate to customer_success. The "caller frustrated" trigger on line 259 only applied during the multiple-match disambiguation flow (count > 1), not when a single match was found.

**Solution:** Added explicit frustration-triggered escalation logic that recognizes communication breakdown patterns and routes to customer success.

**Files Changed:**

1. `prompts/squad/assistants/03_existing_client.md`
   - [Goals]: Added 4th goal: "Escalate frustrated callers with communication breakdowns to customer_success"
   - [Error Handling]: Replaced generic "Frustrated caller" section with "Frustrated caller (HIGH PRIORITY ESCALATION)" that includes:
     - Explicit frustration signals to recognize (repeated calls, unreturned messages, waiting weeks/months)
     - Trigger conditions (communication breakdown, settlement/payment delays, extended wait times)
     - During hours: Escalate to customer_success with apology and offer to transfer
     - After hours: Mark as urgent, take message with urgency flag
     - Explicit instruction: "DO NOT simply take a routine message when a caller expresses ongoing communication failures"

2. `prompts/squad/assistants/04_insurance_adjuster.md`
   - [Goals]: Added 4th goal: "Escalate frustrated callers with communication breakdowns to the insurance department"
   - [Error Handling]: Replaced generic "Frustrated caller" section with "Frustrated caller (HIGH PRIORITY ESCALATION)" that includes:
     - Explicit frustration signals to recognize (repeated calls, unreturned messages, waiting weeks/months)
     - Trigger conditions (communication breakdown, extended wait times for documents like LOR, delayed responses)
     - During hours: Escalate to insurance department with apology and offer to transfer
     - After hours: Mark as urgent, take message with urgency flag
     - Explicit instruction: "DO NOT simply take a routine message when a caller expresses ongoing communication failures"

---

### Action Required: VAPI Dashboard Update

The above prompt changes (Issue #10) need to be copied to the VAPI dashboard to take effect at runtime:
- Update the Existing Client assistant prompt with the new [Goals] section and [Frustrated caller (HIGH PRIORITY ESCALATION)] section
- Update the Insurance Adjuster assistant prompt with the new [Goals] section and [Frustrated caller (HIGH PRIORITY ESCALATION)] section

---

## [2026-01-17] - Fallback Line Agent

### Feature: Fallback Line Agent for Uncertain Routing

**Problem:** When the greeter cannot figure out what to do next, it may get stuck in a loop instead of gracefully resolving the call. There was no fallback mechanism for:
1. Callers requesting general help ("operator", "receptionist", "someone")
2. Unclear caller purpose after multiple clarifying questions
3. Conversations going in circles

**Principle:** Resolving with fallback to customer success or taking a message is better than getting stuck in a loop.

**Solution:** Created a new Fallback Line agent (#14) that acts as a safety net when the greeter is uncertain how to proceed.

**Behavior:**
- During hours (`intake_is_open = true`): Transfer immediately to customer success
- After hours (`intake_is_open = false`): Take a message, promise callback

**Files Created:**

1. `prompts/squad/assistants/14_fallback_line.md`
   - New agent with `transfer_call` and `take_message` tools
   - Warm, reassuring style as the "safety net"
   - Business hours logic for routing vs message-taking
   - Error handling for transfer failures

**Files Changed:**

1. `prompts/squad/assistants/01_greeter_classifier.md`
   - Removed Step 4.5 (Handle "General Help" Requests) - logic moved to handoff tool description
   - Added Step 6: Fallback for Uncertainty with explicit triggers:
     - Caller's purpose unclear after 2 clarifying questions
     - Responses don't match any known caller type
     - About to repeat a question already asked
     - Genuinely uncertain which destination is correct
   - Updated destination count from 12 to 13

2. `prompts/squad/handoff_tools/greeter_handoff_destinations.md`
   - Updated Direct Staff Request section: "front desk", "operator", etc. → route to fallback_line (was customer_success)
   - Updated Direct Staff Request section: role without specific name → route to fallback_line (was customer_success)
   - Added Section 13: Fallback Line Agent with full description covering:
     - General help requests trigger
     - Uncertain routing trigger
     - Variables expected (caller_name, purpose optional; frustration_level required)
   - Added row 13 to Quick Reference Table

---

### Action Required: VAPI Dashboard Update

The above changes need to be applied in the VAPI dashboard:
1. Create new "Fallback Line" assistant with the prompt from `14_fallback_line.md`
2. Configure with `transfer_call` and `take_message` tools
3. Set firstMessage to empty string with "assistant-speaks-first" mode
4. Update Greeter Classifier assistant prompt (Step 6 added)
5. Add fallback_line as 13th destination in the greeter's handoff tool
