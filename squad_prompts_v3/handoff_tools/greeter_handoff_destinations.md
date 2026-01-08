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
Hands off to the Existing Client agent for callers who identify as current clients but were NOT pre-identified by phone lookup.

PREREQUISITE: You MUST have the caller's FULL name (first AND last) before calling this tool.

Use this destination when the caller:
- Says "I'm a client" or "I have a case with you"
- Mentions "my case", "my case manager", "my settlement", "my attorney"
- Asks about case status, case updates, or wants to speak with their case manager
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
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Full name of the caller - MUST collect before handoff |
| purpose | Yes | What they're calling about (case update, speak to case manager, etc.) |
| frustration_level | Yes | 0-3 scale based on tone |

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

IMPORTANT - Insurance + Billing = Still Insurance:
If an insurance caller mentions billing, invoices, or payments, they are STILL an insurance adjuster. Do NOT route to Vendor.

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name and which insurance company you're with?"
3. Wait for their response
4. Only then call this tool

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
| frustration_level | Yes | 0-3 scale |

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

Do NOT use this destination if:
- Caller mentions billing, invoices, or payments → Use Vendor instead
- Caller is from an insurance company → Use Insurance Adjuster instead

If the caller has not provided their name yet:
1. Do NOT call this tool
2. First ask: "Sure, I can help. May I have your name and which facility you're calling from?"
3. Wait for their response
4. Only then call this tool

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
| frustration_level | Yes | 0-3 scale |

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
| frustration_level | Yes | 0-3 scale (often elevated due to recent accident) |

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
4. Only then call this tool
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the caller - MUST collect before handoff |
| organization_name | Preferred | Company/facility name |
| purpose | Yes | Invoice inquiry, payment status, etc. |
| frustration_level | Yes | 0-3 scale |

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
- Caller asks for "front desk", "operator", "representative", "receptionist", "human", "a person", "someone" → These are general help requests, route to customer_success
- Caller mentions a role/title (lawyer, attorney, paralegal, billing, etc.) AND says "I don't know" or cannot provide a specific person's name when asked

IMPORTANT - Role vs Name Detection:
These are ROLES/GENERAL REQUESTS, not names: "lawyer", "attorney", "case manager", "front desk", "receptionist", "operator", "human", "representative", "paralegal", "billing", "accounting", "someone", "anyone"
Only use this destination when caller provides an ACTUAL person's name (first name, last name, or full name).

If caller says a role but doesn't know the specific name → Route to customer_success (they'll help find the right person)
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| target_staff_name | Yes | The staff member's name the caller asked for - MUST have this |
| caller_name | Yes | Caller's name - ask before handoff |
| purpose | Optional | Why they want to speak with this person |
| frustration_level | Yes | 0-3 scale |

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
```

**Variables Expected:**
| Variable | Required | Description |
|----------|----------|-------------|
| caller_name | Yes | Name of the person calling (the family member) - MUST collect |
| client_name | Yes | Name of the actual client whose case it is - MUST collect |
| purpose | Yes | What they're calling about |
| frustration_level | Yes | 0-3 scale |

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
| frustration_level | Yes | Often elevated due to language barrier |

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
| frustration_level | Yes | 0-3 scale |

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
4. Only then call this tool

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
| frustration_level | Yes | 0-3 scale |

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
| frustration_level | Yes | Usually 0-1 |

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

---

## Priority Override Rules

1. **Direct Staff Request = HIGHEST** - If caller asks for someone by name, route there first
2. **Pre-ID Client = AUTO** - If case_details exists, route there automatically
3. **Insurance + Billing = Insurance** - Never route insurance to Vendor
4. **Medical + Billing = Vendor** - Medical billing goes to Vendor, not Medical Provider
5. **Spanish = QUICK** - Don't delay Spanish speakers collecting info
6. **Existing Client + New Matter = New Client** - If caller has an existing case BUT wants representation for a NEW/DIFFERENT matter, route to New Client (new intake), not Existing Client

---

## Frustration Level Scale

| Level | Indicators | Message Priority |
|-------|------------|------------------|
| 0 | Calm, patient, neutral tone | standard |
| 1 | Slightly rushed, minor impatience | standard |
| 2 | Noticeably frustrated, short responses, sighing | high |
| 3 | Angry, upset, demanding, emotional distress | urgent |
