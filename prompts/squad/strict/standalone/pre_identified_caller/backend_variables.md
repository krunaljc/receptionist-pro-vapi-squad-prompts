# Backend Variables for Pre-Identified Caller Assistant

This document specifies the variables that the backend webhook must pass when routing a pre-identified caller to this standalone assistant.

---

## Required Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `firm_name` | string | Yes | The law firm name (e.g., "McCraw Law Group") |
| `firm_id` | number | Yes | Firm identifier used for API calls |
| `agent_name` | string | Yes | AI receptionist name (e.g., "Emma", "Sarah") |
| `is_open` | boolean | Yes | Whether the office is currently open for business |
| `intake_is_open` | boolean | Yes | Whether the intake team is currently available |
| `case` | object | Yes | Pre-loaded case information from phone lookup |

---

## case Object Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_full_name` | string | Yes | Full name of the client (e.g., "Marcus Johnson") |
| `client_first_name` | string | Yes | First name only, used in greeting (e.g., "Marcus") |
| `case_manager` | string | Yes | Assigned case manager's name (e.g., "Paige Thompson") |
| `staff_id` | number | Yes | Case manager's staff ID, used for transfers |
| `case_status` | string | Yes | Current status of the case (e.g., "Active - Treatment") |
| `case_type` | string | Yes | Type of case (e.g., "Auto Accident", "Slip and Fall") |
| `incident_date` | string | Yes | Date of the incident (e.g., "2024-09-15") |
| `case_phase_updated_at` | string | Yes | Last status update timestamp (e.g., "2024-12-20") |
| `case_manager_phone` | string | Recommended | Case manager's direct phone number |
| `case_manager_email` | string | Recommended | Case manager's email address |

---

## Example Payload

```json
{
  "firm_name": "McCraw Law Group",
  "firm_id": 1,
  "agent_name": "Emma",
  "is_open": true,
  "intake_is_open": true,
  "case": {
    "client_full_name": "Marcus Johnson",
    "client_first_name": "Marcus",
    "case_manager": "Paige Thompson",
    "staff_id": 1234,
    "case_status": "Active - Treatment",
    "case_type": "Auto Accident",
    "incident_date": "2024-09-15",
    "case_phase_updated_at": "2024-12-20",
    "case_manager_phone": "972-555-1234",
    "case_manager_email": "paige.thompson@mccrawlawgroup.com"
  }
}
```

---

## Notes

1. **Phone Lookup**: The backend should perform phone number lookup when an inbound call arrives. If the caller's phone matches an existing client record, populate `case` and route to this standalone assistant instead of the main squad.

2. **Fallback**: If `case` cannot be populated (no match found), route the call to the main squad's Greeter Classifier instead.

3. **Hours Status**: `is_open` and `intake_is_open` determine whether transfers are offered or messages are taken.

4. **client_first_name**: This field is specifically used in the greeting. Extract from `client_full_name` if not stored separately.

5. **staff_id**: Critical for the `transfer_call` tool to route the transfer to the correct case manager.
