#!/usr/bin/env python3
"""
VAPI Structured Output Runner
Fetches calls for phone +1 (947) 214-9549 since Dec 30, 2025 3:40 PM Atlanta time
and runs all structured outputs on them.
"""

import requests
import json
from datetime import datetime
import time
import sys

API_KEY = "49f35b20-ce20-4b24-9835-1e8248f988eb"
BASE_URL = "https://api.vapi.ai"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Dec 30, 2025 3:40 PM Atlanta (EST) = Dec 30, 2025 8:40 PM UTC
START_DATE = "2025-12-30T20:40:00Z"
# Target phone number ID for +1 (947) 214-9549
TARGET_PHONE_ID = "808540aa-c7d7-49ef-97ec-1094b2550b58"

def get_calls():
    """Fetch all calls since the start date."""
    url = f"{BASE_URL}/call"
    params = {
        "createdAtGe": START_DATE,
        "limit": 100
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_structured_outputs():
    """Fetch all available structured outputs."""
    url = f"{BASE_URL}/structured-output"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def run_structured_output(structured_output_id, call_id):
    """Run a structured output on a specific call."""
    url = f"{BASE_URL}/structured-output/run"
    payload = {
        "structuredOutputId": structured_output_id,
        "callIds": [call_id],  # Must be an array
        "previewEnabled": True  # Preview mode - executes immediately without updating call artifact
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.json()

def main():
    print("=" * 80)
    print("VAPI STRUCTURED OUTPUT RUNNER")
    print("=" * 80)
    print(f"\nTarget Phone: +1 (947) 214-9549")
    print(f"Since: Dec 30, 2025 3:40 PM Atlanta (EST)")
    print(f"UTC: {START_DATE}\n")

    # Step 1: Get all calls and filter
    print("-" * 40)
    print("STEP 1: FETCHING & FILTERING CALLS")
    print("-" * 40)

    all_calls = get_calls()
    calls = [c for c in all_calls if c.get('phoneNumberId') == TARGET_PHONE_ID]

    print(f"\nTotal calls found: {len(all_calls)}")
    print(f"Calls for +1 (947) 214-9549: {len(calls)}")
    print()

    for i, call in enumerate(calls, 1):
        call_id = call.get('id', 'N/A')
        customer = call.get('customer', {})
        phone = customer.get('number', 'N/A')
        created_at = call.get('createdAt', 'N/A')
        status = call.get('status', 'N/A')
        ended_reason = call.get('endedReason', 'N/A')

        duration = None
        if call.get('startedAt') and call.get('endedAt'):
            try:
                start = datetime.fromisoformat(call['startedAt'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(call['endedAt'].replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
            except:
                pass

        print(f"{i}. Call ID: {call_id}")
        print(f"   Customer Phone: {phone}")
        print(f"   Created: {created_at}")
        print(f"   Status: {status} | Reason: {ended_reason}")
        if duration:
            print(f"   Duration: {duration:.0f}s ({duration/60:.1f} min)")
        print()

    # Step 2: Get structured outputs
    print("-" * 40)
    print("STEP 2: AVAILABLE STRUCTURED OUTPUTS")
    print("-" * 40)

    structured_outputs_response = get_structured_outputs()
    structured_outputs = structured_outputs_response.get('results', [])

    print(f"\nFound {len(structured_outputs)} structured outputs:\n")

    for i, so in enumerate(structured_outputs, 1):
        print(f"{i}. {so.get('name', 'N/A')}")
        print(f"   ID: {so.get('id', 'N/A')}")
        print(f"   Type: {so.get('type', 'N/A')}")
        print()

    # Step 3: Run structured outputs on each call
    print("-" * 40)
    print("STEP 3: RUNNING STRUCTURED OUTPUTS")
    print("-" * 40)

    results = []

    for idx, call in enumerate(calls, 1):
        call_id = call.get('id')
        customer_phone = call.get('customer', {}).get('number', 'N/A')
        created_at = call.get('createdAt', 'N/A')

        print(f"\n{'='*60}")
        print(f"[{idx}/{len(calls)}] CALL: {call_id}")
        print(f"Customer: {customer_phone}")
        print(f"Created: {created_at}")
        print(f"{'='*60}")
        sys.stdout.flush()

        call_results = {
            'call_id': call_id,
            'phone': customer_phone,
            'created_at': created_at,
            'structured_outputs': {}
        }

        for so in structured_outputs:
            so_id = so.get('id')
            so_name = so.get('name')

            print(f"\n  -> Running: {so_name}...", end=" ")
            sys.stdout.flush()

            try:
                result = run_structured_output(so_id, call_id)
                call_results['structured_outputs'][so_name] = result

                # Pretty print result
                if 'value' in result:
                    print(f"\n     Result: {json.dumps(result['value'], indent=6)}")
                else:
                    print(f"\n     Result: {json.dumps(result, indent=6)}")
            except Exception as e:
                call_results['structured_outputs'][so_name] = {'error': str(e)}
                print(f"\n     Error: {e}")

            sys.stdout.flush()
            time.sleep(0.3)  # Small delay to avoid rate limiting

        results.append(call_results)

        # Save intermediate results
        with open("structured_output_results.json", 'w') as f:
            json.dump(results, f, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nProcessed {len(calls)} calls with {len(structured_outputs)} structured outputs each")
    print(f"Total structured output runs: {len(calls) * len(structured_outputs)}")
    print(f"\nResults saved to: structured_output_results.json")

if __name__ == "__main__":
    main()
