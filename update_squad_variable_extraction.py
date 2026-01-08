#!/usr/bin/env python3
"""
Update Vapi Squad with Variable Extraction Plans.
This script patches the existing squad to add variableExtractionPlan to handoff destinations.

Usage:
    python update_squad_variable_extraction.py
"""

import os
import requests
import json
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY = os.environ.get("VAPI_SANDBOX_API_KEY", "3678cd88-c4eb-4b0f-a5e7-1275083ecce1")
BASE_URL = "https://api.vapi.ai"
SQUAD_ID = "7ae431c2-2bc4-4cb0-8189-1b04b0131832"

# Assistant IDs from sandbox
SANDBOX_ASSISTANTS = {
    "greeter": "f76c8234-26c4-45f8-ab66-cc34edcf956f",
    "existing_client": "c3019349-729e-42df-a367-48245e75c1ad",
    "insurance": "bd4f1ff5-7555-4e7f-9ea1-c037b6bbec56",
    "medical_provider": "f61ed81a-9835-4903-a86d-cdf010f77951",
    "new_client": "fc2f0561-f714-41cf-adc3-014f356adaa9",
    "vendor": "3ec9d20a-c1c3-40d7-bb90-d517b8158c9c",
    "direct_staff_request": "d5acdcf4-fcfe-4506-b297-b6840dab1579",
    "spanish_speaker": "895dfb0a-5ff4-439c-91e9-3d51ccc346a5",
    "legal_system": "8fcbbf13-8e02-49c0-98d4-a9d0f6ad7b4d",
}

# ============================================================================
# VARIABLE EXTRACTION SCHEMAS (JSON Schema format per Vapi docs)
# ============================================================================

EXTRACTION_SCHEMAS = {
    "insurance": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Why they're calling, be detailed. Examples: 'case status', 'payment status', 'get case manager contact details', 'speak with case manager'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the insurance adjuster calling. REQUIRED - must collect before handoff."
                },
                "client_name": {
                    "type": "string",
                    "description": "Name of the client/claimant/patient the adjuster is calling about. May be empty if not provided yet."
                },
                "organization_name": {
                    "type": "string",
                    "description": "Name of the insurance company. Examples: 'State Farm', 'Progressive', 'GEICO', 'Allstate', 'USAA', 'Farmers', 'Liberty Mutual', 'Nationwide'"
                }
            },
            "required": ["caller_name"]
        }
    },
    "existing_client": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "What the caller wants, be descriptive but do not fabricate. Examples: 'case update', 'speak with case manager', 'get case status', 'question about case', 'settlement details'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Full name of the caller (first and last name). This is REQUIRED - the destination agent uses this to search for the case. Extract exactly as stated by the caller."
                },
                "caller_type": {
                    "type": "string",
                    "description": "Set to 'existing_client'"
                }
            },
            "required": ["caller_name"]
        }
    },
    "medical_provider": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Why they're calling, be descriptive but do not fabricate details. Examples: 'case manager contact', 'case status', 'speak with case manager', 'treatment coordination'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the person calling from the medical facility. REQUIRED - must collect before handoff."
                },
                "caller_type": {
                    "type": "string",
                    "description": "Set to 'medical_provider'"
                },
                "client_name": {
                    "type": "string",
                    "description": "Name of the patient whose case they're calling about. May be empty if not provided yet."
                },
                "organization_name": {
                    "type": "string",
                    "description": "Name of the hospital, clinic, doctor's office, rehab center, or medical facility they're calling from."
                }
            },
            "required": ["caller_name"]
        }
    },
    "new_client": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Type of accident or what they're asking about. Examples: 'car accident', 'slip and fall', 'truck accident', 'motorcycle accident', 'workplace injury', 'medical malpractice', 'I was in an accident', 'need a lawyer'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the person calling. REQUIRED - must collect before handoff"
                },
                "caller_type": {
                    "type": "string",
                    "description": "Set to 'new_case'"
                }
            },
            "required": ["caller_name"]
        }
    },
    "vendor": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "What they're calling about. Examples: 'invoice', 'billing', 'payment status', 'outstanding balance', 'accounts payable'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the person calling. REQUIRED - must collect before handoff."
                },
                "caller_type": {
                    "type": "string",
                    "description": "Set to 'vendor'"
                },
                "organization_name": {
                    "type": "string",
                    "description": "Name of the company or medical facility the caller is from."
                }
            },
            "required": ["caller_name"]
        }
    },
    "direct_staff_request": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Why they want to speak with this person."
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the person calling. REQUIRED - must collect before handoff"
                },
                "target_staff_name": {
                    "type": "string",
                    "description": "The specific staff member's name the caller asked for. REQUIRED - this is the primary reason for this handoff. Examples: 'Sarah Johnson', 'Mr. Thompson', 'John'. May be first name only, last name only, or full name."
                }
            },
            "required": ["caller_name", "target_staff_name"]
        }
    },
    "legal_system": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "What they need. Examples: 'deposition scheduling', 'document service', 'subpoena', 'hearing notice', 'case manager contact', 'speak with attorney'"
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the legal professional calling. REQUIRED - must collect before handoff."
                },
                "caller_type": {
                    "type": "string",
                    "description": "Type of legal system caller. Examples: 'court_reporter', 'defense_attorney', 'court_clerk', 'process_server', 'opposing_counsel', 'attorney'"
                },
                "client_name": {
                    "type": "string",
                    "description": "Name of the client/case they're calling about. May be empty if not provided yet"
                },
                "organization_name": {
                    "type": "string",
                    "description": "Court, law firm, or company name they're calling from. PREFERRED - helps identify caller context."
                }
            },
            "required": ["caller_name"]
        }
    },
    "spanish_speaker": {
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Why they're calling if understood. OPTIONAL - may not be clear due to language barrier."
                },
                "caller_name": {
                    "type": "string",
                    "description": "Name of the caller if provided. OPTIONAL - don't delay transfer to collect. Quick transfer is priority for language barrier situations."
                }
            },
            "required": []
        }
    }
}

# ============================================================================
# HANDOFF TOOL DEFINITIONS WITH VARIABLE EXTRACTION
# ============================================================================

def build_handoff_tools():
    """Build handoff tools with variableExtractionPlan using JSON Schema format."""
    return [
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_insurance"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["insurance"],
                    "description": "Hands off to the Insurance Adjuster agent for callers from insurance companies.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as an insurance adjuster or claims representative\n- Mentions they're from: State Farm, Progressive, GEICO, Allstate, USAA, Farmers, Liberty Mutual, Nationwide, or any other insurance company\n- Says \"I'm calling about a claim\" or \"regarding a claim\"\n- Uses phrases like \"I'm the adjuster on this case\"\n\nIMPORTANT - Insurance + Billing = Still Insurance:\nIf an insurance caller mentions billing, invoices, or payments, they are STILL an insurance adjuster. Do NOT route to Vendor.\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and which insurance company you're with?\"\n3. Wait for their response\n4. Only then call this tool\n\nCollect if possible (but don't block handoff):\n- Organization name (insurance company)\n- Client name (the claimant/patient they're calling about)",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["insurance"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_existing_client"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["existing_client"],
                    "description": "Hands off to the Existing Client agent for callers who identify as current clients.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"I'm a client\" or \"I have a case with you\"\n- Mentions \"my case\", \"my case manager\", \"my settlement\", \"my attorney\"\n- Asks about case status, case updates, or wants to speak with their case manager\n- AND case_details is NULL (phone did not match)\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help with your case. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller is asking about someone ELSE's case (use Family Member instead)\n- Caller is NEW and had an accident (use New Client instead)",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["existing_client"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_medical_provider"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["medical_provider"],
                    "description": "Hands off to the Medical Provider agent for callers from hospitals, clinics, doctor's offices, or medical facilities.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as calling from a hospital, clinic, or doctor's office\n- Mentions patient care, treatment coordination, or medical records\n- Is a nurse, medical assistant, or healthcare provider\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and which facility you're calling from?\"\n3. Wait for their response\n4. Only then call this tool",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["medical_provider"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_new_client"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["new_client"],
                    "description": "Hands off to the New Client agent for potential new clients who were in an accident.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says they were in an accident (car, truck, motorcycle, slip and fall, etc.)\n- Asks about hiring a lawyer or attorney\n- Is NOT an existing client\n- Mentions \"I need help with my case\" but is clearly new\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"I'd be happy to help. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["new_client"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_vendor"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["vendor"],
                    "description": "Hands off to the Vendor agent for invoice and billing inquiries from vendors or medical facilities with billing matters.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"I'm calling about an invoice\" or \"outstanding balance\"\n- Mentions billing, payment status, or accounts payable\n- Is from a medical facility AND specifically mentions billing/payment (not patient care)\n- Asks \"When will we receive payment?\"\n\nIMPORTANT - Medical + Billing = Vendor:\nIf a medical facility caller's purpose is billing/payment, route here. If their purpose is patient care coordination, use Medical Provider instead.\n\nEXCEPTION - Insurance + Billing = Insurance:\nIf the caller is from an insurance company and mentions billing, they are STILL an insurance adjuster. Use Insurance Adjuster instead.\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help with that. May I have your name and company?\"\n3. Wait for their response\n4. Only then call this tool",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["vendor"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_direct_staff"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["direct_staff_request"],
                    "description": "Hands off to the Direct Staff Request agent when a caller asks for a specific staff member by name.\n\nHIGHEST PRIORITY: This destination overrides all other routing logic.\n\nPREREQUISITE: The caller MUST have mentioned a specific staff member's name.\nPREREQUISITE: You should collect the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"Can I speak with [Name]?\" or \"Is [Name] available?\"\n- Asks for someone by first name, last name, or full name\n- Says \"I'm trying to reach [Name]\"\n- Mentions a specific person before stating their purpose\n\nExamples:\n- \"Hi, is Sarah Johnson available?\" → Use this destination\n- \"I need to speak with Mr. Thompson\" → Use this destination\n- \"Can you transfer me to the case manager?\" → Do NOT use (no specific name)\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can try to reach [Name]. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller asks for \"a case manager\" or \"someone in billing\" (generic role, not a name)\n- Caller wants to speak with \"my case manager\" → Use Existing Client to look up their assigned manager",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["direct_staff_request"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_legal_caller"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["legal_system"],
                    "description": "Hands off to the Legal System agent for court reporters, defense attorneys, court clerks, and process servers.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as a court reporter, defense attorney, court clerk, or process server\n- Mentions depositions, subpoenas, court filings, or hearings\n- Is from opposing counsel's office\n- Needs to serve documents or schedule legal proceedings\n- References case numbers or court dates\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and where you're calling from?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller is our client asking about their court date → Use Existing Client\n- Caller is from an insurance company → Use Insurance Adjuster",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["legal_system"]
                }
            ]
        },
        {
            "type": "handoff",
            "async": False,
            "function": {
                "name": "handoff_to_spanish_speaker"
            },
            "messages": [],
            "destinations": [
                {
                    "type": "assistant",
                    "assistantId": SANDBOX_ASSISTANTS["spanish_speaker"],
                    "description": "Hands off to the Spanish Speaker agent for callers who speak Spanish.\n\nUse this destination when the caller:\n- Speaks Spanish or asks for Spanish assistance\n- Says \"Habla español?\" or similar\n- Has difficulty communicating in English\n\nThis is a quick handoff - do NOT delay to collect name. Language barrier situations require immediate transfer.",
                    "variableExtractionPlan": EXTRACTION_SCHEMAS["spanish_speaker"]
                }
            ]
        }
    ]


def build_squad_members():
    """Build squad member configurations with handoff tools on greeter."""
    handoff_tools = build_handoff_tools()

    return [
        {
            "assistantId": SANDBOX_ASSISTANTS["greeter"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                },
                "tools:append": handoff_tools
            }
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["existing_client"]
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["insurance"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            }
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["medical_provider"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            }
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["new_client"]
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["vendor"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            }
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["direct_staff_request"]
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["spanish_speaker"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            }
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["legal_system"]
        },
    ]


# ============================================================================
# API FUNCTIONS
# ============================================================================

def get_headers():
    """Get API headers."""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def get_squad(squad_id):
    """Get squad details."""
    response = requests.get(f"{BASE_URL}/squad/{squad_id}", headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting squad: {response.status_code}")
        print(response.text)
        return None


def update_squad(squad_id, payload):
    """Update squad using PATCH."""
    print("\n[DEBUG] Update payload (first 3000 chars):")
    payload_str = json.dumps(payload, indent=2)
    print(payload_str[:3000] + "..." if len(payload_str) > 3000 else payload_str)

    response = requests.patch(
        f"{BASE_URL}/squad/{squad_id}",
        headers=get_headers(),
        json=payload
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"\nError updating squad: {response.status_code}")
        print(response.text)
        return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("Update Squad with Variable Extraction Plans")
    print("=" * 60)

    print(f"\nSquad ID: {SQUAD_ID}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")

    # Get current squad
    print("\n[1/3] Fetching current squad configuration...")
    current_squad = get_squad(SQUAD_ID)
    if not current_squad:
        print("Failed to fetch squad. Exiting.")
        sys.exit(1)

    print(f"Current squad name: {current_squad.get('name')}")
    print(f"Current members: {len(current_squad.get('members', []))}")

    # Build update payload
    print("\n[2/3] Building update payload with variableExtractionPlan...")
    members = build_squad_members()

    update_payload = {
        "members": members,
        "membersOverrides": {
            "model": {
                "provider": "openai",
                "model": "gpt-4.1"
            },
            "transcriber": {
                "provider": "deepgram",
                "model": "flux-general-en",
                "language": "en"
            }
        }
    }

    # Update squad
    print("\n[3/3] Updating squad...")
    result = update_squad(SQUAD_ID, update_payload)

    if result:
        print("\n" + "=" * 60)
        print("SUCCESS! Squad updated with variable extraction plans.")
        print("=" * 60)
        print(f"\nSquad ID: {result.get('id')}")
        print(f"Squad Name: {result.get('name')}")

        # Save result
        output_file = "sandbox_squad_config_updated.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nUpdated config saved to: {output_file}")

        # Show extraction plan summary
        print("\n" + "-" * 60)
        print("Variable Extraction Plans Added:")
        print("-" * 60)
        for name, schema in EXTRACTION_SCHEMAS.items():
            props = list(schema["schema"]["properties"].keys())
            required = schema["schema"].get("required", [])
            print(f"  {name}:")
            print(f"    Properties: {', '.join(props)}")
            print(f"    Required: {', '.join(required) if required else 'none'}")

    else:
        print("\nFailed to update squad. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
