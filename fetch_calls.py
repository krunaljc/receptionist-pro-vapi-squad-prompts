#!/usr/bin/env python3
"""
Fetch VAPI calls and extract search_case_details tool calls.
Identifies client_name and case counts for each search.
"""

import requests
import json
import csv
import re
from datetime import datetime

VAPI_API_KEY = "8916824e-1381-4368-9602-34b762749405"
BASE_URL = "https://api.vapi.ai"

CALL_IDS = [
    "019b8062-3f97-7223-a794-940ed3607f5d",
    "019b8022-72fc-755e-8679-4dc68a944965",
    "019b7c33-9f12-7448-bb92-3aed25cf2825",
    "019b7613-6179-7ccd-bb9c-a509ca2fe86d",
    "019b75a1-da9b-7337-a8d4-37e77ae6d4a6",
    "019b7590-74a4-7446-b42c-7928159839e0",
    "019b7561-e008-7ccd-bb28-6d311de40d09",
    "019b7561-6d56-7ffe-9bba-bf62ccce415f",
    "019b74d9-f86b-799a-8861-e1115bf0c386",
    "019b74c3-e396-799e-9edf-9faf5e398ccf",
    "019b74a0-a9df-7000-822c-795e4b6ef0de",
    "019b71ee-32a2-7330-8e25-3d26eb8c5aac",
]

def fetch_call(call_id):
    """Fetch full call details from VAPI API."""
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/call/{call_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching call {call_id}: {response.status_code}")
        return None

def extract_search_case_details(call_data):
    """Extract all search_case_details tool calls and their results from a call."""
    results = []
    call_id = call_data.get("id", "")
    customer_phone = call_data.get("customer", {}).get("number", "")
    call_date = call_data.get("createdAt", "")

    messages = call_data.get("messages", [])

    # Find all search_case_details tool calls and match them with results
    tool_calls = {}
    tool_results = {}

    for msg in messages:
        role = msg.get("role", "")

        # Tool calls
        if role == "tool_calls":
            for tc in msg.get("toolCalls", []):
                func = tc.get("function", {})
                if func.get("name") == "search_case_details":
                    tool_call_id = tc.get("id")
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                        client_name = args.get("client_name", "")
                        tool_calls[tool_call_id] = {
                            "client_name": client_name,
                            "args": args
                        }
                    except json.JSONDecodeError:
                        pass

        # Tool call results
        if role == "tool_call_result" and msg.get("name") == "search_case_details":
            tool_call_id = msg.get("toolCallId")
            result_str = msg.get("result", "{}")
            try:
                result = json.loads(result_str)
                count = result.get("count", 0)
                success = result.get("success", False)
                case_data = result.get("case", result.get("cases", []))
                tool_results[tool_call_id] = {
                    "count": count,
                    "success": success,
                    "case_data": case_data
                }
            except json.JSONDecodeError:
                pass

    # Match tool calls with results
    for tool_call_id, tc_data in tool_calls.items():
        result_data = tool_results.get(tool_call_id, {})
        results.append({
            "call_id": call_id,
            "customer_phone": customer_phone,
            "call_date": call_date,
            "client_name": tc_data["client_name"],
            "count": result_data.get("count", "N/A"),
            "success": result_data.get("success", False),
            "multiple_cases": result_data.get("count", 0) > 1
        })

    return results

def main():
    all_results = []

    print("Fetching calls from VAPI API...")
    for i, call_id in enumerate(CALL_IDS):
        print(f"  [{i+1}/{len(CALL_IDS)}] Fetching {call_id}...")
        call_data = fetch_call(call_id)
        if call_data:
            searches = extract_search_case_details(call_data)
            if searches:
                all_results.extend(searches)
                for s in searches:
                    print(f"    -> Found search: client_name='{s['client_name']}', count={s['count']}")
            else:
                print(f"    -> No search_case_details calls found")
        else:
            print(f"    -> Failed to fetch call")

    # Write to CSV
    csv_path = "search_case_details_results.csv"
    print(f"\nWriting results to {csv_path}...")

    with open(csv_path, "w", newline="") as f:
        fieldnames = ["call_id", "customer_phone", "call_date", "client_name", "count", "success", "multiple_cases"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"Done! Found {len(all_results)} search_case_details calls across {len(CALL_IDS)} calls.")

    # Summary
    multi_case_clients = [r for r in all_results if r["multiple_cases"]]
    if multi_case_clients:
        print(f"\nClients with MORE than 1 case returned:")
        for r in multi_case_clients:
            print(f"  - {r['client_name']}: {r['count']} cases")
    else:
        print("\nNo clients had more than 1 case returned.")

    # Write JSON for reference
    json_path = "search_case_details_results.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Also saved JSON to {json_path}")

if __name__ == "__main__":
    main()
