# Greeter Handoff Tool Destinations

**Tool Type:** Handoff
**Tool Name:** `route_to_specialist`
**Used By:** Greeter/Classifier Agent (01)

Copy each destination's description into the VAPI dashboard handoff tool configuration.

---

## 1. Pre-Identified Client Agent

**Assistant Name:** `Pre-Identified Client`

**Description:**
```
Hands off to the Pre-Identified Client agent for callers whose phone number matched an existing client record.

PREREQUISITE: case_details must be available in context (phone lookup returned a match).

This handoff happens automatically at the START of the call when:
1. The inbound phone number matched a client in the system
2. case_details object is populated with client information

Do NOT use this destination if:
- case_details is null or empty
- The caller says they are NOT the person on file
- The caller is calling on behalf of someone else

If caller says "That's not me" or "I'm calling for someone else":
1. Do NOT hand off to this agent
2. Ask: "No problem. Who am I speaking with?"
3. Route to appropriate agent based on their actual identity
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| case_details | Yes | Pre-loaded from phone lookup (client_full_name, case_manager, case_status, etc.) |
| caller_name | Auto | Populated from case_details.client_full_name |

---

## 2. Existing Client Agent

**Assistant Name:** `Existing Client`

**Description:**
```
Hands off to the Existing Client agent for callers who EXPLICITLY identify as current clients but were NOT pre-identified by phone lookup.

PREREQUISITE: You MUST have the caller's FULL name (first AND last) before calling this tool.

⚠️ AMBIGUOUS CASE INQUIRIES - MUST DISAMBIGUATE FIRST:
If caller says generic "case status", "case update", or "checking on a case" WITHOUT explicit self-identification:
1. Do NOT assume they are a client
2. First ask: "Are you a current client of the firm?"
3. Only route here if they confirm "Yes"
4. If they say "No" → Ask "Who are you calling about?" and route appropriately (family_member, insurance_adjuster, etc.)

Use this destination when the caller:
- Says "I'm a client" or "I have a case with you"
- Mentions "MY case", "MY case manager", "MY settlement", "MY attorney" (the word "MY" is the key signal)
- Confirms they are a client when asked
- AND case_details is NULL (phone did not match)

If the caller has not provided their FULL name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help with your case. May I have your full name?"
3. Wait for their response
4. If they give only first name, ask: "And your last name?"
5. Wait for their response
6. Only then call this tool with the full name

Do NOT use this destination if:
- case_details is populated (use Pre-Identified Client instead)
- Caller is asking about someone ELSE's case (use Family Member instead)
- Caller is NEW and had an accident (use New Client instead)
- Caller is an existing client but wants representation for a NEW/DIFFERENT legal matter
  (e.g., "I have a car accident case with you, but I want to open a medical malpractice case")
  → Use New Client instead - treat them as a new intake for the new matter
- Caller is an existing client but describes a NEW accident/injury they JUST experienced
  (e.g., "I'm a client, but I was just in a car accident yesterday", "I have a case with you, but I slipped and fell last week")
  → Use New Client instead - this is a new potential case that needs intake evaluation
  → Key signal: They describe something that HAPPENED (new incident) vs asking about something that EXISTS (their current case)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Full name of the caller - MUST collect before handoff |
| purpose | Yes | What they're calling about (case update, speak to case manager, etc.) |

---

## 3. Insurance Adjuster Agent

**Assistant Name:** `Insurance Adjuster`

**Description:**
```
Hands off to the Insurance Adjuster agent for callers from insurance companies.

PREREQUISITE: You MUST have the caller's name before calling this tool.

Use this destination when the caller:
- Identifies as an insurance adjuster or claims representative
- Mentions they're from: State Farm, Progressive, GEICO, Allstate, USAA, Farmers, Liberty Mutual, Nationwide, or any other insurance company
- Says "I'm calling about a claim" or "regarding a claim"
- Uses phrases like "I'm the adjuster on this case"

Additional patterns that indicate insurance caller:
- Says "with [Company] claims" or "[Company] claims department" (even without saying "I'm an adjuster")
- Asks about LOR (Letter of Representation) or lien acknowledgment
- Mentions "on a recorded line" (common insurance practice)
- Mentions any insurance company name while asking about a client case

If caller mentions an insurance company name and is asking about a client case, route here even if they don't explicitly say "I'm an adjuster".

IMPORTANT - Insurance + Billing = Still Insurance:
If an insurance caller mentions billing, invoices, or payments, they are STILL an insurance adjuster. Do NOT route to Vendor.

TOOL CALL RULE: When routing criteria are met and you have caller name + organization, call this handoff IMMEDIATELY with NO text output. Do NOT say "I'll get you to the right person" or "One moment" - just call the tool silently.

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name and which insurance company you're with?"
3. Wait for their response
4. First name + organization is SUFFICIENT - do not insist on last name
5. Only then call this tool

Collect if possible (but don't block handoff):
- Organization name (insurance company)
- Client name (the claimant/patient they're calling about)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the adjuster - MUST collect before handoff |
| organization_name | Preferred | Insurance company name |
| client_name | Optional | The client/claimant they're calling about |
| purpose | Yes | What they need (case status, case manager contact, etc.) |

---

## 4. Medical Provider Agent

**Assistant Name:** `Medical Provider`

**Description:**
```
Hands off to the Medical Provider agent for hospitals, clinics, and rehab centers calling about patient cases (NOT billing).

PREREQUISITE: You MUST have the caller's name before calling this tool.

Use this destination when the caller:
- Identifies as calling from a hospital, clinic, doctor's office, rehab center, or medical facility
- Is asking about a patient who is a client of the firm
- Needs case manager contact information
- Needs case status for treatment coordination

Also route here for third-party medical services:
- Companies calling ON BEHALF OF a hospital or medical facility (e.g., "I'm with Espirion calling on behalf of Emory Hospital")
- Medical lien companies (e.g., "Lane Star", "MedLien", etc.)
- Medical records retrieval services
- Lien resolution or lien management companies
- Any caller mentioning a patient/client name who wants case information or status update (unless clearly insurance)

Always route here for these specific organizations (regardless of stated purpose):
- Any hospital or ER room
- American Medical Response (AMR)
- Optum
- Elevate Financial
- Rawlings
- Intellivo
- Medcap
- Movedocs
- Gain or Gain Servicing

Key signal: If caller provides a specific patient/client name and wants case status from ANY organization, route here regardless of whether you recognize their organization name.

Do NOT use this destination if:
- Caller mentions billing, invoices, or payments → Use Vendor instead
- Caller is from an insurance company → Use Insurance Adjuster instead

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name and which facility you're calling from?"
3. Wait for their response
4. First name + facility name is SUFFICIENT - do not insist on last name
5. Only then call this tool

Collect if possible:
- Organization name (hospital/clinic name)
- Client name (the patient they're calling about)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the caller - MUST collect before handoff |
| organization_name | Preferred | Hospital/clinic name |
| client_name | Preferred | Patient name they're calling about |
| purpose | Yes | What they need |

---

## 5. New Client Agent

**Assistant Name:** `New Client`

**Description:**
```
Hands off to the New Client agent for people who had an accident and may need legal representation.

PREREQUISITE: You MUST have the caller's FULL name (first AND last) before calling this tool.

Use this destination when the caller:
- Says "I was in an accident" or "I had an accident"
- Asks "Do you handle [type] cases?" (car accidents, slip and fall, medical malpractice, etc.)
- Says "I need a lawyer" or "I'm looking for an attorney"
- Asks "Do I have a case?"
- Describes an injury or incident that just happened
- Is clearly a potential new client, not an existing one
- Is an EXISTING client who wants to open a NEW/SEPARATE case for a different matter
  (e.g., "I have a car accident case with you, but I want representation for a medical malpractice case")
  → Treat them as a new intake for the new matter
- Caller describes a NEW accident/injury/incident that happened to a FAMILY MEMBER
  (e.g., "My daughter had surgery complications", "My husband was hit by a car", "My mom fell at the grocery store")
  → The injured party does NOT have to be the person calling
  → What matters: Is this a NEW potential case that needs intake evaluation?
- Caller is an EXISTING client but describes a NEW accident/injury they just experienced
  (e.g., "I'm a client, but I was in an accident yesterday", "I have a case with you but I just slipped and fell")

If the caller has not provided their FULL name yet:
1. Do NOT call this tool
2. First ask: "I'm sorry to hear that. May I have your full name?"
3. Wait for their response
4. If they give only first name, ask: "And your last name?"
5. Wait for their response
6. Only then call this tool with the full name

Do NOT use this destination if:
- Caller says "I'm already a client" → Use Existing Client instead
- Caller is calling about someone else's accident → Clarify if they're the injured party or family member
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the caller - MUST collect before handoff |
| purpose | Yes | Type of accident or what they're asking about |

---

## 6. Vendor Agent

**Assistant Name:** `Vendor`

**Description:**
```
Hands off to the Vendor agent for invoice and billing inquiries from vendors or medical facilities with billing matters.

PREREQUISITE: You MUST have the caller's name before calling this tool.

Use this destination when the caller:
- Says "I'm calling about an invoice" or "outstanding balance"
- Mentions billing, payment status, or accounts payable
- Is from a medical facility AND specifically mentions billing/payment (not patient care)
- Asks "When will we receive payment?"

IMPORTANT - Medical + Billing = Vendor:
If a medical facility caller's purpose is billing/payment, route here. If their purpose is patient care coordination, use Medical Provider instead.

EXCEPTION - Insurance + Billing = Insurance:
If the caller is from an insurance company and mentions billing, they are STILL an insurance adjuster. Use Insurance Adjuster instead.

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help with that. May I have your name and company?"
3. Wait for their response
4. First name + company name is SUFFICIENT - do not insist on last name
5. Only then call this tool
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the caller - MUST collect before handoff |
| organization_name | Preferred | Company/facility name |
| purpose | Yes | Invoice inquiry, payment status, etc. |

---

## 7. Direct Staff Request Agent

**Assistant Name:** `Direct Staff Request`

**Description:**
```
Hands off to the Direct Staff Request agent when a caller asks for a specific staff member by name.

HIGHEST PRIORITY: This destination overrides all other routing logic.

PREREQUISITE: The caller MUST have mentioned a specific staff member's name.
PREREQUISITE: You should collect the caller's name before calling this tool.

Use this destination when the caller:
- Says "Can I speak with [Name]?" or "Is [Name] available?"
- Asks for someone by first name, last name, or full name
- Says "I'm trying to reach [Name]"
- Mentions a specific person before stating their purpose

Examples:
- "Hi, is Sarah Johnson available?" → Use this destination
- "I need to speak with Mr. Thompson" → Use this destination
- "Can you transfer me to the case manager?" → Do NOT use (no specific name)

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can try to reach [Name]. May I have your name?"
3. Wait for their response
4. Only then call this tool

Do NOT use this destination if:
- Caller asks for "a case manager" or "someone in billing" (generic role, not a name)
- Caller wants to speak with "my case manager" → Use Existing Client to look up their assigned manager
- Caller asks for "front desk", "operator", "representative", "receptionist", "human", "a person", "someone" → These are general help requests, route to fallback_line
- Caller mentions a role/title (lawyer, attorney, paralegal, billing, etc.) AND says "I don't know" or cannot provide a specific person's name when asked

IMPORTANT - Role vs Name Detection:
These are ROLES/GENERAL REQUESTS, not names: "lawyer", "attorney", "case manager", "front desk", "receptionist", "operator", "human", "representative", "paralegal", "billing", "accounting", "someone", "anyone"
Only use this destination when caller provides an ACTUAL person's name (first name, last name, or full name).

If caller says a role but doesn't know the specific name → Route to fallback_line (they'll help find the right person)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| target_staff_name | Yes | The staff member's name the caller asked for - MUST have this |
| caller_name | Yes | Caller's name - ask before handoff |
| purpose | Optional | Why they want to speak with this person |

---

## 8. Family Member Agent

**Assistant Name:** `Family Member`

**Description:**
```
Hands off to the Family Member agent when someone is calling about another person's case (third-party inquiry).

PREREQUISITE: You MUST have BOTH the caller's name AND the client's name before calling this tool.

Use this destination when the caller:
- Says "I'm calling about my [mom/dad/son/daughter/spouse]'s case"
- Mentions a family relationship: "my husband is a client", "my mother's attorney"
- Caller's name is DIFFERENT from the client they're asking about
- Is inquiring on behalf of someone else

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name?"
3. Then ask: "And what is [the client]'s full name?"
4. Only then call this tool

Do NOT use this destination if:
- Caller IS the client (same person) → Use Existing Client or Pre-ID Client
- Caller refuses to identify themselves
- Caller describes a NEW accident/injury/incident involving their family member
  → This is a potential new case - use New Client instead
  → Family Member is ONLY for inquiries about EXISTING cases at the firm
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the person calling (the family member) - MUST collect |
| client_name | Yes | Name of the actual client whose case it is - MUST collect |
| purpose | Yes | What they're calling about |

---

## 9. Spanish Speaker Agent

**Assistant Name:** `Spanish Speaker`

**Description:**
```
Hands off to the Spanish Speaker agent for callers who speak Spanish and need assistance in Spanish.

NO PREREQUISITE for caller name - transfer quickly to get them help.

Use this destination when the caller:
- Speaks Spanish when the call connects
- Asks "¿Habla español?" or "Spanish please?"
- Is clearly struggling with English
- Requests a Spanish-speaking representative

This is a quick-transfer scenario:
1. You do NOT need to collect the caller's name first
2. Transfer as quickly as possible to reduce frustration
3. If you can, say "Momento, por favor" before transferring

Do NOT use this destination if:
- Caller speaks English fluently, even with an accent
- Caller is bilingual and comfortable in English
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Optional | If provided, pass it along |
| purpose | Optional | If understood, pass it along |

---

## 10. Referral Source Agent

**Assistant Name:** `Referral Source`

**Description:**
```
Hands off to the Referral Source agent for callers who referred someone to the firm and have questions about their referral.

PREREQUISITE: You MUST have the caller's name before calling this tool.

Use this destination when the caller:
- Says "I referred [someone] to you"
- Asks about "my referral" or "referral fee"
- Mentions they sent a client to the firm
- Is following up on a referral they made

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help with your referral inquiry. May I have your name?"
3. Wait for their response
4. If possible, also ask: "And who did you refer to us?"
5. Only then call this tool

Do NOT use this destination if:
- Caller is the person who WAS referred (they're a new/existing client, not the referrer)
- Caller is asking about referring someone in the future (general inquiry)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the referrer - MUST collect before handoff |
| client_name | Preferred | Name of the person they referred |
| purpose | Yes | What they're asking about (referral fee, status, etc.) |

---

## 11. Legal System Agent

**Assistant Name:** `Legal System`

**Description:**
```
Hands off to the Legal System agent for court reporters, defense attorneys, court clerks, and process servers.

PREREQUISITE: You MUST have the caller's name before calling this tool.

Use this destination when the caller:
- Identifies as a court reporter, defense attorney, court clerk, or process server
- Mentions depositions, subpoenas, court filings, or hearings
- Is from opposing counsel's office
- Needs to serve documents or schedule legal proceedings
- References case numbers or court dates

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name and where you're calling from?"
3. Wait for their response
4. First name + organization is SUFFICIENT - do not insist on last name
5. Only then call this tool

Do NOT use this destination if:
- Caller is our client asking about their court date → Use Existing Client
- Caller is from an insurance company → Use Insurance Adjuster
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the caller - MUST collect before handoff |
| organization_name | Preferred | Court, law firm, or company name |
| client_name | Preferred | The case/client they're calling about |
| purpose | Yes | Deposition scheduling, document service, etc. |

---

## 12. Sales Solicitation Agent

**Assistant Name:** `Sales Solicitation`

**Description:**
```
Hands off to the Sales Solicitation agent for vendors trying to sell products or services to the firm.

PREREQUISITE: None - you can transfer sales calls quickly.

Use this destination when the caller:
- Says "I'd like to introduce myself" or "introduce our company"
- Mentions "our services" or "our platform"
- Is clearly pitching a product or service
- Asks to speak with a "decision maker" or "office manager" to sell something
- Mentions partnerships, demos, or trials for a product

This is a low-priority transfer - the Sales agent will take a message only (no transfers to staff).

You do NOT need to collect detailed information:
1. If they give their name, pass it along
2. If not, just transfer - the Sales agent will collect what's needed

Do NOT use this destination if:
- Caller is an existing vendor with an invoice question → Use Vendor
- Caller is a legitimate business partner (not selling)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Optional | If provided |
| organization_name | Optional | Company they're representing |
| purpose | Optional | What they're selling |

---

## 13. Fallback Line Agent

**Assistant Name:** `Fallback Line`

**Description:**
```
Hands off to the Fallback Line agent for general help requests OR when you cannot determine appropriate routing.

This is your SAFETY NET - use it for general assistance and to prevent getting stuck in loops.

Use this destination when:

**General Help Requests:**
- Caller asks for: "front desk", "operator", "representative", "receptionist", "human", "a person", "someone"
- These are NOT staff name requests - they're requests for general assistance
- Do NOT use Direct Staff Request for these

**Uncertain Routing:**
- After 2 clarifying questions, caller's purpose is still unclear
- Caller's responses don't match any known caller type patterns
- You find yourself about to repeat a question you already asked
- You're genuinely uncertain which destination is correct
- The conversation is going in circles

CRITICAL - USE FALLBACK TO AVOID GETTING STUCK:
- If you have collected the caller's name and purpose but cannot confidently match them to a specific destination, use fallback IMMEDIATELY
- Do NOT continue asking clarifying questions beyond 2 exchanges
- Do NOT say "I'll get you to the right person" without calling a handoff tool in the same turn
- Better to route to fallback than leave the caller hanging or get stuck in a loop

This is NOT a failure - it's the correct action for general help requests and when classification is genuinely difficult.

You do NOT need to collect specific information before handoff:
1. Pass whatever you have (caller_name if collected, purpose if understood)
2. The Fallback Line agent will handle getting them to the right place

Do NOT use this destination if:
- You have enough information to route to a specific agent (e.g., existing client, insurance adjuster, new client, etc.)
- Caller asks for a specific staff member by name (use Direct Staff Request)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Optional | If collected |
| purpose | Optional | Best understanding of why they're calling |

---

## Quick Reference Table

| # | Agent | Required Variables | Key Trigger Phrases |
|---|-------|-------------------|---------------------|
| 1 | Pre-ID Client | case_details (auto) | Phone matched existing client |
| 2 | Existing Client | caller_name, purpose | "my case", "my case manager" |
| 3 | Insurance Adjuster | caller_name, organization | "adjuster", "State Farm", "claim" |
| 4 | Medical Provider | caller_name, organization | Hospital/clinic + patient inquiry |
| 5 | New Client | caller_name, purpose | "had an accident", "need a lawyer" |
| 6 | Vendor | caller_name, organization | "invoice", "billing", "payment" |
| 7 | Direct Staff Request | target_staff_name | "Can I speak with [Name]?" |
| 8 | Family Member | caller_name, client_name | "my mom's case", "my son's attorney" |
| 9 | Spanish Speaker | (none required) | Spanish spoken, "¿Habla español?" |
| 10 | Referral Source | caller_name, client_name | "I referred", "referral fee" |
| 11 | Legal System | caller_name, organization | "court reporter", "deposition", "subpoena" |
| 12 | Sales Solicitation | (none required) | "our services", "decision maker" |
| 13 | Fallback Line | (none required) | "operator", "receptionist", uncertain routing |

---

## Priority Override Rules

1. **Direct Staff Request = HIGHEST** - If caller asks for someone by name, route there first
2. **Pre-ID Client = AUTO** - If case_details exists, route there automatically
3. **Insurance + Billing = Insurance** - Never route insurance to Vendor
4. **Medical + Billing = Vendor** - Medical billing goes to Vendor, not Medical Provider
5. **Spanish = QUICK** - Don't delay Spanish speakers collecting info
6. **Existing Client + New Matter = New Client** - If caller has an existing case BUT wants representation for a NEW/DIFFERENT matter, route to New Client (new intake), not Existing Client

7. **New Case = HIGHEST PRIORITY (Non-Professional Callers)** - If ANY non-professional caller describes a NEW accident, injury, or incident that could be a legal matter, route to New Client (intake). This takes priority over:
   - Family member relationship → Route to New Client, not Family Member
   - Existing client status → Route to New Client, not Existing Client

   Key signal: Caller describes something that HAPPENED (an incident/injury) vs asking about something that EXISTS (a case already with the firm).

   Examples:
   - "My daughter had surgery complications" → New Client (new incident)
   - "I'm a client but I was just in a car accident" → New Client (new incident)
   - "My husband was hit by a car yesterday" → New Client (new incident)
   - "I'm calling about my mom's case" → Family Member (existing case)
   - "I want an update on my case" → Existing Client (existing case)

