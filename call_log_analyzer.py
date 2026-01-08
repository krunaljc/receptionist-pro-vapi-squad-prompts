#!/usr/bin/env python3
"""
Call Log Analyzer for Existing Clients
Analyzes call logs to identify existing client interactions, routing patterns,
answer rates, and callback behaviors.

Features:
- Resumable processing with progress checkpoints
- Streaming output (results written as processed)
- Kill & restart support
"""

import csv
import re
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

CALL_LOG_PATH = "/Users/krunalc/Downloads/CallLog_20260105-131447.csv"
CLIENT_DATA_PATH = "/Users/krunalc/Downloads/Supabase Snippet Firm Case Details (1).csv"
OUTPUT_PATH = "/Users/krunalc/Downloads/existing_client_call_analysis.csv"
PROGRESS_FILE = "/Users/krunalc/Downloads/call_analysis_progress.json"

MAINLINE_NUMBER = "4043444448"

# Staff directory with phone numbers and roles
STAFF_DIRECTORY = {
    "5043235280": {"name": "Jennifer Greene", "role": "lawyer"},
    "5042085861": {"name": "Steven Lane", "role": "lawyer"},
    "5135474010": {"name": "Anita Washington", "role": "lawyer"},
    "4043829669": {"name": "John Bey", "role": "lawyer"},  # Note: Also Donte Thompson
    "4047930359": {"name": "Detra Howard-Mitchell", "role": "admin"},
    "5135061515": {"name": "Jim O'Brien", "role": "lawyer"},
    "4042207877": {"name": "Veronica Brown", "role": "paralegal"},
    "4702500756": {"name": "Meaghan Hicks", "role": "paralegal"},
    "4702500776": {"name": "Sasha Wesley", "role": "paralegal"},
    "4045916658": {"name": "Karina Milla", "role": "intake_specialist"},
    "4043691398": {"name": "Jonathan Steele", "role": "lawyer"},
    "5042645165": {"name": "Lillian Breland", "role": "paralegal"},
    "6783795194": {"name": "Endia Miller", "role": "paralegal"},
    "4704124737": {"name": "Susan Spiess", "role": "paralegal"},
    "4045966093": {"name": "Tasha Bodden", "role": "intake_specialist"},
    "4044186226": {"name": "Kaymie Bodden", "role": "intake_specialist"},
    "4708098860": {"name": "Angelo Gonzalez", "role": "intake_specialist"},
    "4046457153": {"name": "Jesse Gonzalez", "role": "intake_specialist"},
    "4045918929": {"name": "Fatima Guzman", "role": "intake_specialist"},
    "4706451748": {"name": "Stephanie Peck", "role": "case_manager"},
    "4045918928": {"name": "Matt McCarren", "role": "admin"},
    "4046925486": {"name": "Michael Sole", "role": "admin"},
    "4042207146": {"name": "Antara Chapman", "role": "case_manager"},
    "4704404520": {"name": "Taylor Middleton", "role": "lawyer"},
    "5139640829": {"name": "Khadeem Gibson", "role": "lawyer"},
    "4042207735": {"name": "Nicholas Obata", "role": "lawyer"},
    "4049373386": {"name": "Horace Braswell", "role": "admin"},
    "5132773686": {"name": "Jaela Kennedy", "role": "paralegal"},
    "4702504154": {"name": "Paul Jang", "role": "paralegal"},
    "4702983258": {"name": "Dionel Reynoso", "role": "intake_specialist"},
    "4706150710": {"name": "Victoria Morales", "role": "case_manager"},
    "4706150715": {"name": "Payge Almon", "role": "case_manager"},
    "5133734064": {"name": "Linda Huff", "role": "case_manager"},
    "4048898965": {"name": "Tyauna Evans", "role": "case_manager"},
    "4706150712": {"name": "Brianna Heckadon", "role": "receptionist"},
    "4709032756": {"name": "Kevin Love", "role": "paralegal"},
    "4784124725": {"name": "Devin McLaughlin", "role": "intake_specialist"},
    "4703397214": {"name": "Brittany Lawson", "role": "admin"},
    "4049032558": {"name": "Keri Waites", "role": "paralegal"},
    "4045929370": {"name": "Lonie Soloranza Pouchie", "role": "case_manager"},
}

# Extension to staff name mapping (extracted from call log patterns)
EXTENSION_TO_STAFF = {
    "7007": {"name": "Susan Spiess", "role": "paralegal"},
    "7008": {"name": "Detra Mitchell", "role": "admin"},
    "7009": {"name": "Kaymie Bodden", "role": "intake_specialist"},
    "7010": {"name": "Jim Obrien", "role": "lawyer"},
    "7011": {"name": "Tyauna Evans", "role": "case_manager"},
    "7013": {"name": "Fatima Guzman", "role": "intake_specialist"},
    "7014": {"name": "Matt McCarren", "role": "admin"},
    "7016": {"name": "Jonathan Steele", "role": "lawyer"},
    "7019": {"name": "Michael Sole", "role": "admin"},
    "7020": {"name": "Karina Milla", "role": "intake_specialist"},
    "7021": {"name": "Donte Thompson", "role": "admin"},
    "7022": {"name": "Jaela Kennedy", "role": "paralegal"},
    "7023": {"name": "Tara Chapman", "role": "case_manager"},
    "7026": {"name": "Devin McLaughlin", "role": "intake_specialist"},
    "7029": {"name": "Horace Braswell", "role": "admin"},
    "7030": {"name": "Tasha Bodden", "role": "intake_specialist"},
    "7031": {"name": "Lonie Pouchie", "role": "case_manager"},
    "7033": {"name": "Khadeem Gibson", "role": "lawyer"},
    "7036": {"name": "Victoria Morales", "role": "case_manager"},
    "7038": {"name": "Anita Washington", "role": "lawyer"},
    "7046": {"name": "Payge Almon", "role": "case_manager"},
    "7048": {"name": "Linda Huff", "role": "case_manager"},
    "7049": {"name": "Angelo Gonzalez", "role": "intake_specialist"},
    "7052": {"name": "Brittany Lawson", "role": "admin"},
    "7053": {"name": "Escalation Line", "role": "escalation"},
    "7060": {"name": "Stephanie Salamanca", "role": "case_manager"},
    "7062": {"name": "Taylor Middleton", "role": "lawyer"},
    "7065": {"name": "Dionel Reynoso", "role": "intake_specialist"},
    "7068": {"name": "Jesse Gonzalez", "role": "intake_specialist"},
    "7069": {"name": "Nick Obata", "role": "lawyer"},
    "7074": {"name": "Lillian Breland", "role": "paralegal"},
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def normalize_phone(phone_str):
    """
    Normalize phone number to 10-digit format.
    Examples:
        (404) 344-4448 -> 4043444448
        +14043444448 -> 4043444448
        404-344-4448 -> 4043444448
        7065 -> 7065 (extension, keep as-is)
    """
    if not phone_str:
        return ""

    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone_str))

    # If it's a short number (extension), keep as-is
    if len(digits) <= 4:
        return digits

    # If 11 digits starting with 1, remove the 1
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]

    # If more than 10 digits, take last 10
    if len(digits) > 10:
        digits = digits[-10:]

    return digits


def parse_duration(duration_str):
    """Convert duration string (H:MM:SS) to seconds."""
    if not duration_str:
        return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0


def parse_datetime(date_str, time_str):
    """Parse date and time strings into datetime object."""
    try:
        # Date format: "Wed 12/31/2025"
        # Time format: "8:08 PM"
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if not date_match:
            return None

        month, day, year = date_match.groups()

        # Parse time with AM/PM
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
        if not time_match:
            return None

        hour, minute, ampm = time_match.groups()
        hour = int(hour)
        minute = int(minute)

        if ampm.upper() == 'PM' and hour != 12:
            hour += 12
        elif ampm.upper() == 'AM' and hour == 12:
            hour = 0

        return datetime(int(year), int(month), int(day), hour, minute)
    except Exception as e:
        return None


def is_internal_call(from_phone, to_phone):
    """Check if call is internal (extension to extension)."""
    return (len(from_phone) <= 4 and from_phone.isdigit() and
            len(to_phone) <= 4 and to_phone.isdigit())


def get_staff_from_extension(extension):
    """Get staff info from extension number."""
    ext = extension.split(' - ')[0] if ' - ' in extension else extension
    return EXTENSION_TO_STAFF.get(ext, None)


def get_staff_from_phone(phone):
    """Get staff info from phone number."""
    normalized = normalize_phone(phone)
    return STAFF_DIRECTORY.get(normalized, None)


# =============================================================================
# DATA LOADING
# =============================================================================

def load_client_phones(filepath):
    """Load client phone numbers and build lookup dictionary."""
    print(f"Loading client data from {filepath}...")
    phone_to_client = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            client_name = row.get('client_full_name', '').strip()
            phones_str = row.get('client_phones', '')

            if phones_str and phones_str != 'null':
                try:
                    # Parse JSON array of phone numbers
                    phones = json.loads(phones_str)
                    for phone in phones:
                        normalized = normalize_phone(phone)
                        if normalized and len(normalized) == 10:
                            phone_to_client[normalized] = client_name
                except json.JSONDecodeError:
                    pass

    print(f"  Loaded {len(phone_to_client)} phone-to-client mappings")
    return phone_to_client


def load_call_log(filepath):
    """Load call log and return list of rows with row numbers."""
    print(f"Loading call log from {filepath}...")
    rows = []

    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            # Clean up column names (remove quotes if present)
            cleaned_row = {}
            for k, v in row.items():
                clean_key = k.strip().strip('"')
                cleaned_row[clean_key] = v
            cleaned_row['_row_num'] = i
            rows.append(cleaned_row)

    print(f"  Loaded {len(rows)} call log rows")
    return rows


# =============================================================================
# CALL PROCESSING
# =============================================================================

def process_calls(call_rows, phone_to_client):
    """
    Process call log and extract primary calls with enriched data.
    Returns list of processed call records.
    """
    print("Processing calls...")

    processed_calls = []
    i = 0
    total_rows = len(call_rows)

    while i < total_rows:
        row = call_rows[i]

        # Only process primary call records (Type = "Voice")
        if row.get('Type') != 'Voice':
            i += 1
            continue

        # Collect sub-records for this call
        sub_records = []
        j = i + 1
        while j < total_rows and call_rows[j].get('Type') == '':
            sub_records.append(call_rows[j])
            j += 1

        # Process this call
        call_record = process_single_call(row, sub_records, phone_to_client)
        if call_record:
            processed_calls.append(call_record)

        # Move to next primary call
        i = j

        # Progress update
        if len(processed_calls) % 500 == 0:
            print(f"  Processed {len(processed_calls)} primary calls ({i}/{total_rows} rows)...")

    print(f"  Total primary calls processed: {len(processed_calls)}")
    return processed_calls


def process_single_call(primary_row, sub_records, phone_to_client):
    """Process a single call with its sub-records."""

    direction = primary_row.get('Direction', '')
    from_phone = normalize_phone(primary_row.get('From', ''))
    to_phone = normalize_phone(primary_row.get('To', ''))
    extension = primary_row.get('Extension', '')
    caller_id_name = primary_row.get('Name', '').strip()
    date_str = primary_row.get('Date', '')
    time_str = primary_row.get('Time', '')
    action_result = primary_row.get('Action Result', '')
    duration_raw = primary_row.get('Duration', '')

    # Parse datetime
    call_datetime = parse_datetime(date_str, time_str)

    # Check if internal call
    is_internal = is_internal_call(from_phone, to_phone)

    # Determine if call was answered (check primary + sub-records)
    was_answered = action_result in ['Accepted', 'Call connected']
    if not was_answered:
        for sub in sub_records:
            sub_result = sub.get('Action Result', '')
            if sub_result in ['Accepted', 'Call connected']:
                was_answered = True
                break

    # Determine existing client status
    if direction == 'Incoming':
        check_phone = from_phone
    else:
        check_phone = to_phone

    is_existing_client = check_phone in phone_to_client
    client_name = phone_to_client.get(check_phone, '')

    # Determine destination type and staff
    destination_type = ''
    staff_name = ''
    staff_role = ''

    if direction == 'Incoming':
        if to_phone == MAINLINE_NUMBER:
            destination_type = 'mainline'
        elif is_internal:
            destination_type = 'internal'
        else:
            destination_type = 'direct_line'
            # Try to get staff from To phone or extension
            staff_info = get_staff_from_phone(to_phone) or get_staff_from_extension(extension)
            if staff_info:
                staff_name = staff_info['name']
                staff_role = staff_info['role']
    else:  # Outgoing
        destination_type = 'outbound'
        # Get staff making the call from extension
        if extension:
            staff_info = get_staff_from_extension(extension)
            if staff_info:
                staff_name = staff_info['name']
                staff_role = staff_info['role']

    # Extract extension number
    ext_num = ''
    if extension:
        ext_match = re.match(r'(\d+)', extension)
        if ext_match:
            ext_num = ext_match.group(1)

    return {
        'call_id': primary_row['_row_num'],
        'datetime': call_datetime.isoformat() if call_datetime else '',
        'datetime_obj': call_datetime,  # Keep for callback calculation
        'date': date_str,
        'time': time_str,
        'direction': direction,
        'from_phone': from_phone,
        'to_phone': to_phone,
        'caller_id_name': caller_id_name,
        'is_existing_client': is_existing_client,
        'client_name': client_name,
        'destination_type': destination_type,
        'staff_name': staff_name,
        'staff_role': staff_role,
        'extension': ext_num,
        'call_result': action_result,
        'was_answered': was_answered,
        'duration_raw': duration_raw,
        'duration_seconds': parse_duration(duration_raw),
        'is_internal_call': is_internal,
        # Callback fields - populated later
        'callback_found': False,
        'callback_time_hours': '',
        'callback_datetime': '',
        'callback_by_staff_name': '',
        'callback_by_staff_role': '',
        'callback_by_extension': '',
    }


# =============================================================================
# CALLBACK DETECTION
# =============================================================================

def detect_callbacks(processed_calls):
    """
    For each missed incoming call from existing client,
    find if there was a subsequent callback.
    """
    print("Detecting callbacks...")

    # Build index of outgoing calls by destination phone
    outgoing_by_phone = defaultdict(list)
    for call in processed_calls:
        if call['direction'] == 'Outgoing' and call['to_phone']:
            outgoing_by_phone[call['to_phone']].append(call)

    # Sort outgoing calls by datetime
    for phone in outgoing_by_phone:
        outgoing_by_phone[phone].sort(
            key=lambda x: x['datetime_obj'] if x['datetime_obj'] else datetime.min
        )

    # Find callbacks for missed calls from existing clients
    callback_count = 0
    for call in processed_calls:
        if (call['direction'] == 'Incoming' and
            call['is_existing_client'] and
            not call['was_answered'] and
            call['datetime_obj']):

            caller_phone = call['from_phone']
            call_time = call['datetime_obj']

            # Find first outgoing call to this number after the missed call
            outgoing_calls = outgoing_by_phone.get(caller_phone, [])
            for out_call in outgoing_calls:
                if out_call['datetime_obj'] and out_call['datetime_obj'] > call_time:
                    # Found a callback
                    callback_count += 1
                    time_diff = out_call['datetime_obj'] - call_time
                    hours_diff = time_diff.total_seconds() / 3600

                    call['callback_found'] = True
                    call['callback_time_hours'] = round(hours_diff, 2)
                    call['callback_datetime'] = out_call['datetime']
                    call['callback_by_staff_name'] = out_call['staff_name']
                    call['callback_by_staff_role'] = out_call['staff_role']
                    call['callback_by_extension'] = out_call['extension']
                    break

    print(f"  Found {callback_count} callbacks")
    return processed_calls


# =============================================================================
# OUTPUT
# =============================================================================

def write_output_csv(processed_calls, filepath):
    """Write processed calls to CSV."""
    print(f"Writing output to {filepath}...")

    # Filter to existing client calls only (but keep all for reference)
    # Actually, let's write all calls but mark existing clients

    fieldnames = [
        'call_id', 'datetime', 'date', 'time', 'direction',
        'from_phone', 'to_phone', 'caller_id_name',
        'is_existing_client', 'client_name',
        'destination_type', 'staff_name', 'staff_role', 'extension',
        'call_result', 'was_answered', 'duration_raw', 'duration_seconds',
        'is_internal_call',
        'callback_found', 'callback_time_hours', 'callback_datetime',
        'callback_by_staff_name', 'callback_by_staff_role', 'callback_by_extension'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for call in processed_calls:
            # Remove internal datetime_obj before writing
            row = {k: v for k, v in call.items() if k != 'datetime_obj'}
            writer.writerow(row)

    print(f"  Written {len(processed_calls)} calls")


def print_summary_statistics(processed_calls):
    """Print summary statistics to console."""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS - EXISTING CLIENT CALLS")
    print("="*80)

    # Filter to existing client incoming calls only
    existing_client_incoming = [c for c in processed_calls
                                if c['is_existing_client'] and c['direction'] == 'Incoming']

    all_existing_client = [c for c in processed_calls if c['is_existing_client']]

    # 1. Total calls from existing clients
    print(f"\n1. TOTAL CALLS FROM EXISTING CLIENTS")
    print(f"   Incoming calls: {len(existing_client_incoming)}")
    print(f"   Total (in+out): {len(all_existing_client)}")

    # 2. Mainline vs Direct line breakdown
    print(f"\n2. DESTINATION BREAKDOWN (Incoming from Existing Clients)")
    mainline = [c for c in existing_client_incoming if c['destination_type'] == 'mainline']
    direct = [c for c in existing_client_incoming if c['destination_type'] == 'direct_line']
    internal = [c for c in existing_client_incoming if c['destination_type'] == 'internal']

    total = len(existing_client_incoming)
    if total > 0:
        print(f"   Mainline:    {len(mainline):5d} ({100*len(mainline)/total:.1f}%)")
        print(f"   Direct Line: {len(direct):5d} ({100*len(direct)/total:.1f}%)")
        print(f"   Internal:    {len(internal):5d} ({100*len(internal)/total:.1f}%)")

    # 3. Answer rate
    print(f"\n3. ANSWER RATE (Existing Client Incoming Calls)")
    answered = [c for c in existing_client_incoming if c['was_answered']]
    if total > 0:
        print(f"   Overall: {len(answered)}/{total} = {100*len(answered)/total:.1f}%")

        # By destination
        if mainline:
            mainline_answered = len([c for c in mainline if c['was_answered']])
            print(f"   Mainline: {mainline_answered}/{len(mainline)} = {100*mainline_answered/len(mainline):.1f}%")
        if direct:
            direct_answered = len([c for c in direct if c['was_answered']])
            print(f"   Direct Line: {direct_answered}/{len(direct)} = {100*direct_answered/len(direct):.1f}%")

    # 4. Frequent callers
    print(f"\n4. FREQUENT CALLERS (3+ calls)")
    client_call_counts = defaultdict(int)
    for c in existing_client_incoming:
        if c['client_name']:
            client_call_counts[c['client_name']] += 1

    frequent = sorted([(name, count) for name, count in client_call_counts.items() if count >= 3],
                     key=lambda x: -x[1])
    for name, count in frequent[:20]:  # Top 20
        print(f"   {count:3d} calls - {name}")
    if len(frequent) > 20:
        print(f"   ... and {len(frequent)-20} more")

    # 5. Potentially ignored clients (50%+ missed)
    print(f"\n5. POTENTIALLY IGNORED CLIENTS (50%+ missed rate, 2+ calls)")
    client_stats = defaultdict(lambda: {'total': 0, 'missed': 0})
    for c in existing_client_incoming:
        if c['client_name']:
            client_stats[c['client_name']]['total'] += 1
            if not c['was_answered']:
                client_stats[c['client_name']]['missed'] += 1

    ignored = []
    for name, stats in client_stats.items():
        if stats['total'] >= 2:
            miss_rate = stats['missed'] / stats['total']
            if miss_rate >= 0.5:
                ignored.append((name, stats['missed'], stats['total'], miss_rate))

    ignored.sort(key=lambda x: (-x[3], -x[2]))
    for name, missed, total, rate in ignored[:20]:
        print(f"   {rate*100:5.1f}% missed ({missed}/{total}) - {name}")
    if len(ignored) > 20:
        print(f"   ... and {len(ignored)-20} more")

    # 6. Callback analysis
    print(f"\n6. CALLBACK ANALYSIS")
    missed_calls = [c for c in existing_client_incoming if not c['was_answered']]
    callbacks = [c for c in missed_calls if c['callback_found']]

    if missed_calls:
        print(f"   Missed calls from existing clients: {len(missed_calls)}")
        print(f"   Callbacks made: {len(callbacks)} ({100*len(callbacks)/len(missed_calls):.1f}%)")

        if callbacks:
            callback_times = [c['callback_time_hours'] for c in callbacks if c['callback_time_hours']]
            if callback_times:
                avg_time = sum(callback_times) / len(callback_times)
                sorted_times = sorted(callback_times)
                median_time = sorted_times[len(sorted_times)//2]

                print(f"\n   Average callback time: {avg_time:.1f} hours")
                print(f"   Median callback time: {median_time:.1f} hours")

                # Distribution
                within_1hr = len([t for t in callback_times if t <= 1])
                hr_1_4 = len([t for t in callback_times if 1 < t <= 4])
                hr_4_24 = len([t for t in callback_times if 4 < t <= 24])
                hr_24_30 = len([t for t in callback_times if 24 < t <= 30])
                hr_30_36 = len([t for t in callback_times if 30 < t <= 36])
                hr_36_42 = len([t for t in callback_times if 36 < t <= 42])
                hr_42_48 = len([t for t in callback_times if 42 < t <= 48])
                hr_48_60 = len([t for t in callback_times if 48 < t <= 60])
                hr_60_72 = len([t for t in callback_times if 60 < t <= 72])
                hr_72_84 = len([t for t in callback_times if 72 < t <= 84])
                hr_84_96 = len([t for t in callback_times if 84 < t <= 96])
                hr_96_108 = len([t for t in callback_times if 96 < t <= 108])
                hr_108_120 = len([t for t in callback_times if 108 < t <= 120])
                over_120hr = len([t for t in callback_times if t > 120])

                total_cb = len(callback_times)
                print(f"\n   Callback time distribution:")
                print(f"   Within 1 hour:   {within_1hr:4d} ({100*within_1hr/total_cb:.1f}%)")
                print(f"   1-4 hours:       {hr_1_4:4d} ({100*hr_1_4/total_cb:.1f}%)")
                print(f"   4-24 hours:      {hr_4_24:4d} ({100*hr_4_24/total_cb:.1f}%)")
                print(f"   24-30 hours:     {hr_24_30:4d} ({100*hr_24_30/total_cb:.1f}%)")
                print(f"   30-36 hours:     {hr_30_36:4d} ({100*hr_30_36/total_cb:.1f}%)")
                print(f"   36-42 hours:     {hr_36_42:4d} ({100*hr_36_42/total_cb:.1f}%)")
                print(f"   42-48 hours:     {hr_42_48:4d} ({100*hr_42_48/total_cb:.1f}%)")
                print(f"   48-60 hours:     {hr_48_60:4d} ({100*hr_48_60/total_cb:.1f}%)")
                print(f"   60-72 hours:     {hr_60_72:4d} ({100*hr_60_72/total_cb:.1f}%)")
                print(f"   72-84 hours:     {hr_72_84:4d} ({100*hr_72_84/total_cb:.1f}%)")
                print(f"   84-96 hours:     {hr_84_96:4d} ({100*hr_84_96/total_cb:.1f}%)")
                print(f"   96-108 hours:    {hr_96_108:4d} ({100*hr_96_108/total_cb:.1f}%)")
                print(f"   108-120 hours:   {hr_108_120:4d} ({100*hr_108_120/total_cb:.1f}%)")
                print(f"   Over 120 hours:  {over_120hr:4d} ({100*over_120hr/total_cb:.1f}%)")

    # 7. Callbacks by staff
    print(f"\n7. CALLBACKS BY STAFF MEMBER")
    staff_callbacks = defaultdict(int)
    for c in callbacks:
        if c['callback_by_staff_name']:
            staff_callbacks[c['callback_by_staff_name']] += 1

    sorted_staff = sorted(staff_callbacks.items(), key=lambda x: -x[1])
    for name, count in sorted_staff[:15]:
        print(f"   {count:4d} callbacks - {name}")

    # 8. Callbacks by role
    print(f"\n8. CALLBACKS BY ROLE")
    role_callbacks = defaultdict(int)
    for c in callbacks:
        if c['callback_by_staff_role']:
            role_callbacks[c['callback_by_staff_role']] += 1

    for role, count in sorted(role_callbacks.items(), key=lambda x: -x[1]):
        print(f"   {count:4d} callbacks - {role}")

    # 9. Staff-level performance for incoming existing client calls
    print(f"\n9. STAFF PERFORMANCE - EXISTING CLIENT INCOMING CALLS")
    print(f"   (Staff who received calls on their direct lines)")
    print(f"\n   {'Staff Name':<25} {'Role':<18} {'Total':>6} {'Answered':>8} {'Missed':>7} {'Rate':>7}")
    print(f"   {'-'*25} {'-'*18} {'-'*6} {'-'*8} {'-'*7} {'-'*7}")

    # Build staff performance stats for direct line calls
    staff_incoming_stats = defaultdict(lambda: {'total': 0, 'answered': 0, 'role': ''})
    for c in existing_client_incoming:
        if c['destination_type'] == 'direct_line' and c['staff_name']:
            staff_incoming_stats[c['staff_name']]['total'] += 1
            staff_incoming_stats[c['staff_name']]['role'] = c['staff_role']
            if c['was_answered']:
                staff_incoming_stats[c['staff_name']]['answered'] += 1

    # Sort by total calls descending
    sorted_staff_incoming = sorted(staff_incoming_stats.items(),
                                    key=lambda x: -x[1]['total'])

    for name, stats in sorted_staff_incoming:
        total = stats['total']
        answered = stats['answered']
        missed = total - answered
        rate = 100 * answered / total if total > 0 else 0
        print(f"   {name:<25} {stats['role']:<18} {total:>6} {answered:>8} {missed:>7} {rate:>6.1f}%")

    # 10. Staff-level callback performance (who calls back missed calls)
    print(f"\n10. STAFF CALLBACK PERFORMANCE")
    print(f"    (For missed calls to their direct lines - did they call back?)")
    print(f"\n    {'Staff Name':<25} {'Role':<18} {'Missed':>7} {'Called Back':>12} {'CB Rate':>8} {'Avg Time':>10}")
    print(f"    {'-'*25} {'-'*18} {'-'*7} {'-'*12} {'-'*8} {'-'*10}")

    # Build staff callback stats
    staff_callback_stats = defaultdict(lambda: {'missed': 0, 'called_back': 0, 'role': '', 'cb_times': [], 'total_incoming': 0})
    for c in existing_client_incoming:
        if c['destination_type'] == 'direct_line' and c['staff_name']:
            staff_callback_stats[c['staff_name']]['total_incoming'] += 1
            staff_callback_stats[c['staff_name']]['role'] = c['staff_role']
            if not c['was_answered']:
                staff_callback_stats[c['staff_name']]['missed'] += 1
                if c['callback_found']:
                    staff_callback_stats[c['staff_name']]['called_back'] += 1
                    if c['callback_time_hours']:
                        staff_callback_stats[c['staff_name']]['cb_times'].append(c['callback_time_hours'])

    # Sort by total incoming calls descending (most calls on top)
    sorted_staff_cb = sorted(staff_callback_stats.items(),
                              key=lambda x: -x[1]['total_incoming'])

    for name, stats in sorted_staff_cb:
        missed = stats['missed']
        called_back = stats['called_back']
        cb_rate = 100 * called_back / missed if missed > 0 else 0
        avg_time = sum(stats['cb_times']) / len(stats['cb_times']) if stats['cb_times'] else 0
        avg_time_str = f"{avg_time:.1f}h" if avg_time > 0 else "N/A"
        print(f"    {name:<25} {stats['role']:<18} {missed:>7} {called_back:>12} {cb_rate:>7.1f}% {avg_time_str:>10}")

    # 10b. Staff callback time distribution (in percentages)
    print(f"\n10b. STAFF CALLBACK TIME DISTRIBUTION (% of callbacks)")
    print(f"     (Sorted by total incoming calls from existing clients)")
    print(f"\n     {'Staff Name':<22} {'Total':>5} {'CB#':>4} {'<1h':>6} {'1-4h':>6} {'4-24h':>6} {'24-48h':>7} {'48-72h':>7} {'72-120h':>8} {'>120h':>7}")
    print(f"     {'-'*22} {'-'*5} {'-'*4} {'-'*6} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*8} {'-'*7}")

    for name, stats in sorted_staff_cb:
        cb_times = stats['cb_times']
        total_cb = len(cb_times)
        if total_cb == 0:
            print(f"     {name:<22} {stats['total_incoming']:>5} {0:>4} {'--':>6} {'--':>6} {'--':>6} {'--':>7} {'--':>7} {'--':>8} {'--':>7}")
            continue

        within_1hr = len([t for t in cb_times if t <= 1])
        hr_1_4 = len([t for t in cb_times if 1 < t <= 4])
        hr_4_24 = len([t for t in cb_times if 4 < t <= 24])
        hr_24_48 = len([t for t in cb_times if 24 < t <= 48])
        hr_48_72 = len([t for t in cb_times if 48 < t <= 72])
        hr_72_120 = len([t for t in cb_times if 72 < t <= 120])
        over_120hr = len([t for t in cb_times if t > 120])

        # Calculate percentages
        pct_1h = 100 * within_1hr / total_cb
        pct_1_4 = 100 * hr_1_4 / total_cb
        pct_4_24 = 100 * hr_4_24 / total_cb
        pct_24_48 = 100 * hr_24_48 / total_cb
        pct_48_72 = 100 * hr_48_72 / total_cb
        pct_72_120 = 100 * hr_72_120 / total_cb
        pct_120 = 100 * over_120hr / total_cb

        print(f"     {name:<22} {stats['total_incoming']:>5} {total_cb:>4} {pct_1h:>5.0f}% {pct_1_4:>5.0f}% {pct_4_24:>5.0f}% {pct_24_48:>6.0f}% {pct_48_72:>6.0f}% {pct_72_120:>7.0f}% {pct_120:>6.0f}%")

    # 11. Role-level summary
    print(f"\n11. ROLE-LEVEL SUMMARY - EXISTING CLIENT INCOMING CALLS")
    print(f"\n    {'Role':<20} {'Total':>7} {'Answered':>9} {'Ans Rate':>9} {'Missed':>7} {'CB Made':>8} {'CB Rate':>8}")
    print(f"    {'-'*20} {'-'*7} {'-'*9} {'-'*9} {'-'*7} {'-'*8} {'-'*8}")

    role_stats = defaultdict(lambda: {'total': 0, 'answered': 0, 'missed': 0, 'callbacks': 0})
    for c in existing_client_incoming:
        if c['destination_type'] == 'direct_line' and c['staff_role']:
            role_stats[c['staff_role']]['total'] += 1
            if c['was_answered']:
                role_stats[c['staff_role']]['answered'] += 1
            else:
                role_stats[c['staff_role']]['missed'] += 1
                if c['callback_found']:
                    role_stats[c['staff_role']]['callbacks'] += 1

    for role, stats in sorted(role_stats.items(), key=lambda x: -x[1]['total']):
        total = stats['total']
        answered = stats['answered']
        missed = stats['missed']
        callbacks = stats['callbacks']
        ans_rate = 100 * answered / total if total > 0 else 0
        cb_rate = 100 * callbacks / missed if missed > 0 else 0
        print(f"    {role:<20} {total:>7} {answered:>9} {ans_rate:>8.1f}% {missed:>7} {callbacks:>8} {cb_rate:>7.1f}%")

    print("\n" + "="*80)
    print(f"Output written to: {OUTPUT_PATH}")
    print("="*80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("="*80)
    print("CALL LOG ANALYZER FOR EXISTING CLIENTS")
    print("="*80)

    # Load data
    phone_to_client = load_client_phones(CLIENT_DATA_PATH)
    call_rows = load_call_log(CALL_LOG_PATH)

    # Process calls
    processed_calls = process_calls(call_rows, phone_to_client)

    # Detect callbacks
    processed_calls = detect_callbacks(processed_calls)

    # Write output
    write_output_csv(processed_calls, OUTPUT_PATH)

    # Print summary
    print_summary_statistics(processed_calls)


if __name__ == "__main__":
    main()
