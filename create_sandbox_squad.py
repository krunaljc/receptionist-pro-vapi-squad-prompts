#!/usr/bin/env python3
"""
Create Vapi Squad for Sandbox Environment.
This script creates a squad with all 9 assistants and configures handoff destinations.

Usage:
    python create_sandbox_squad.py

Prerequisites:
    - Set VAPI_SANDBOX_API_KEY environment variable OR update the API_KEY below
    - All 9 assistants must already exist in the sandbox account
"""

import os
import requests
import json
import sys

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Sandbox API Key - set via environment variable or update directly here
API_KEY = os.environ.get("VAPI_SANDBOX_API_KEY", "3678cd88-c4eb-4b0f-a5e7-1275083ecce1")

BASE_URL = "https://api.vapi.ai"

# Assistant IDs from sandbox (created earlier)
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

# Squad configuration
SQUAD_NAME = "Receptionist Pro - Sandbox v1"

# ============================================================================
# HANDOFF TOOL CONFIGURATION (FROM PRODUCTION)
# ============================================================================

def build_handoff_tools():
    """Build handoff tools for the greeter.

    Note: variableExtractionPlan removed due to Vapi API validation error.
    The production squad config uses an array format for properties that the
    squad creation API doesn't accept. Variable extraction can be configured
    in the Vapi Dashboard after squad creation if needed.
    """
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
                    "description": "Hands off to the Insurance Adjuster agent for callers from insurance companies.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as an insurance adjuster or claims representative\n- Mentions they're from: State Farm, Progressive, GEICO, Allstate, USAA, Farmers, Liberty Mutual, Nationwide, or any other insurance company\n- Says \"I'm calling about a claim\" or \"regarding a claim\"\n- Uses phrases like \"I'm the adjuster on this case\"\n\nIMPORTANT - Insurance + Billing = Still Insurance:\nIf an insurance caller mentions billing, invoices, or payments, they are STILL an insurance adjuster. Do NOT route to Vendor.\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and which insurance company you're with?\"\n3. Wait for their response\n4. Only then call this tool\n\nCollect if possible (but don't block handoff):\n- Organization name (insurance company)\n- Client name (the claimant/patient they're calling about)"
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
                    "description": "Hands off to the Existing Client agent for callers who identify as current clients.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"I'm a client\" or \"I have a case with you\"\n- Mentions \"my case\", \"my case manager\", \"my settlement\", \"my attorney\"\n- Asks about case status, case updates, or wants to speak with their case manager\n- AND case_details is NULL (phone did not match)\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help with your case. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller is asking about someone ELSE's case (use Family Member instead)\n- Caller is NEW and had an accident (use New Client instead)"
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
                    "description": "Hands off to the Medical Provider agent for callers from hospitals, clinics, doctor's offices, or medical facilities.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as calling from a hospital, clinic, or doctor's office\n- Mentions patient care, treatment coordination, or medical records\n- Is a nurse, medical assistant, or healthcare provider\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and which facility you're calling from?\"\n3. Wait for their response\n4. Only then call this tool"
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
                    "description": "Hands off to the New Client agent for potential new clients who were in an accident.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says they were in an accident (car, truck, motorcycle, slip and fall, etc.)\n- Asks about hiring a lawyer or attorney\n- Is NOT an existing client\n- Mentions \"I need help with my case\" but is clearly new\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"I'd be happy to help. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool"
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
                    "description": "Hands off to the Vendor agent for invoice and billing inquiries from vendors or medical facilities with billing matters.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"I'm calling about an invoice\" or \"outstanding balance\"\n- Mentions billing, payment status, or accounts payable\n- Is from a medical facility AND specifically mentions billing/payment (not patient care)\n- Asks \"When will we receive payment?\"\n\nIMPORTANT - Medical + Billing = Vendor:\nIf a medical facility caller's purpose is billing/payment, route here. If their purpose is patient care coordination, use Medical Provider instead.\n\nEXCEPTION - Insurance + Billing = Insurance:\nIf the caller is from an insurance company and mentions billing, they are STILL an insurance adjuster. Use Insurance Adjuster instead.\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help with that. May I have your name and company?\"\n3. Wait for their response\n4. Only then call this tool"
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
                    "description": "Hands off to the Direct Staff Request agent when a caller asks for a specific staff member by name.\n\nHIGHEST PRIORITY: This destination overrides all other routing logic.\n\nPREREQUISITE: The caller MUST have mentioned a specific staff member's name.\nPREREQUISITE: You should collect the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Says \"Can I speak with [Name]?\" or \"Is [Name] available?\"\n- Asks for someone by first name, last name, or full name\n- Says \"I'm trying to reach [Name]\"\n- Mentions a specific person before stating their purpose\n\nExamples:\n- \"Hi, is Sarah Johnson available?\" → Use this destination\n- \"I need to speak with Mr. Thompson\" → Use this destination\n- \"Can you transfer me to the case manager?\" → Do NOT use (no specific name)\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can try to reach [Name]. May I have your name?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller asks for \"a case manager\" or \"someone in billing\" (generic role, not a name)\n- Caller wants to speak with \"my case manager\" → Use Existing Client to look up their assigned manager"
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
                    "description": "Hands off to the Legal System agent for court reporters, defense attorneys, court clerks, and process servers.\n\nPREREQUISITE: You MUST have the caller's name before calling this tool.\n\nUse this destination when the caller:\n- Identifies as a court reporter, defense attorney, court clerk, or process server\n- Mentions depositions, subpoenas, court filings, or hearings\n- Is from opposing counsel's office\n- Needs to serve documents or schedule legal proceedings\n- References case numbers or court dates\n\nIf the caller has not provided their name yet:\n1. Do NOT call this tool\n2. First ask: \"Sure, I can help. May I have your name and where you're calling from?\"\n3. Wait for their response\n4. Only then call this tool\n\nDo NOT use this destination if:\n- Caller is our client asking about their court date → Use Existing Client\n- Caller is from an insurance company → Use Insurance Adjuster"
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
                    "description": "Hands off to the Spanish Speaker agent for callers who speak Spanish.\n\nUse this destination when the caller:\n- Speaks Spanish or asks for Spanish assistance\n- Says \"Habla español?\" or similar\n- Has difficulty communicating in English\n\nThis is a quick handoff - do NOT delay to collect name. Language barrier situations require immediate transfer."
                }
            ]
        }
    ]


# ============================================================================
# SQUAD MEMBER CONFIGURATION
# ============================================================================

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
            },
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["existing_client"],
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["insurance"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            },
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["medical_provider"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            },
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["new_client"],
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["vendor"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            },
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["direct_staff_request"],
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["spanish_speaker"],
            "assistantOverrides": {
                "model": {
                    "model": "gpt-4.1",
                    "provider": "openai"
                }
            },
            
            
        },
        {
            "assistantId": SANDBOX_ASSISTANTS["legal_system"],
            
            
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


def list_squads():
    """List existing squads."""
    response = requests.get(f"{BASE_URL}/squad", headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error listing squads: {response.status_code}")
        print(response.text)
        return []


def create_squad(name, members):
    """Create a new squad."""
    payload = {
        "name": name,
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

    print("\n[DEBUG] Squad payload:")
    print(json.dumps(payload, indent=2)[:2000] + "..." if len(json.dumps(payload)) > 2000 else json.dumps(payload, indent=2))

    response = requests.post(
        f"{BASE_URL}/squad",
        headers=get_headers(),
        json=payload
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error creating squad: {response.status_code}")
        print(response.text)
        return None


def delete_squad(squad_id):
    """Delete a squad by ID."""
    response = requests.delete(
        f"{BASE_URL}/squad/{squad_id}",
        headers=get_headers()
    )

    if response.status_code in [200, 204]:
        return True
    else:
        print(f"Error deleting squad: {response.status_code}")
        print(response.text)
        return False


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    print("=" * 60)
    print("VAPI Sandbox Squad Creator")
    print("=" * 60)

    # Check API key
    if API_KEY == "YOUR_SANDBOX_API_KEY_HERE":
        print("\nERROR: Please set your sandbox API key!")
        print("Either:")
        print("  1. Set VAPI_SANDBOX_API_KEY environment variable")
        print("  2. Update API_KEY in this script")
        sys.exit(1)

    print(f"\nUsing API Key: {API_KEY[:10]}...{API_KEY[-4:]}")

    # Check for existing squads
    print("\n[1/3] Checking existing squads...")
    existing_squads = list_squads()

    if existing_squads:
        print(f"Found {len(existing_squads)} existing squad(s):")
        for sq in existing_squads:
            print(f"  - {sq.get('name', 'Unnamed')} (ID: {sq.get('id')})")

        # Check if our squad already exists
        for sq in existing_squads:
            if sq.get('name') == SQUAD_NAME:
                print(f"\nSquad '{SQUAD_NAME}' already exists!")
                user_input = input("Delete and recreate? (y/n): ").strip().lower()
                if user_input == 'y':
                    print(f"Deleting squad {sq.get('id')}...")
                    if delete_squad(sq.get('id')):
                        print("Deleted successfully.")
                    else:
                        print("Failed to delete. Exiting.")
                        sys.exit(1)
                else:
                    print("Keeping existing squad. Exiting.")
                    sys.exit(0)
    else:
        print("No existing squads found.")

    # Build squad configuration
    print("\n[2/3] Building squad configuration...")
    members = build_squad_members()
    print(f"Configured {len(members)} squad members:")
    for m in members:
        name = m.get('assistantName', 'Unknown')
        aid = m['assistantId'][:8] + "..."
        is_start = "START" if m.get('isStartMember') else ""
        has_tools = "with handoff tools" if m.get('assistantOverrides', {}).get('tools:append') else ""
        print(f"  - {name}: {aid} {is_start} {has_tools}")

    # Create squad
    print("\n[3/3] Creating squad...")
    result = create_squad(SQUAD_NAME, members)

    if result:
        print("\n" + "=" * 60)
        print("SUCCESS! Squad created.")
        print("=" * 60)
        print(f"\nSquad ID: {result.get('id')}")
        print(f"Squad Name: {result.get('name')}")
        print(f"\nMembers: {len(result.get('members', []))}")

        # Save result to file
        output_file = "sandbox_squad_config.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nFull config saved to: {output_file}")

        print("\n" + "-" * 60)
        print("NEXT STEPS:")
        print("-" * 60)
        print("1. Go to Vapi Dashboard > Squads")
        print("2. Find your squad and verify the configuration")
        print("3. Configure a phone number to use this squad")
        print("4. Test with sample calls for each caller type")

    else:
        print("\nFailed to create squad. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
