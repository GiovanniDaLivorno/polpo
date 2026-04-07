import asyncio
import collections
import datetime
import json
import os
import re
import subprocess

import websockets

LOG_ROOT = os.environ.get("LOG_ROOT", "/host_var_log")
LOG_FILES = [f.strip() for f in os.environ.get("LOG_FILES", "syslog,messages").split(",") if f.strip()]
JOURNAL_DIRS = [d.strip() for d in os.environ.get("JOURNAL_DIRS", "/host_var_log_journal,/host_run_log_journal").split(",") if d.strip()]
MAX_RESULT_LINES = int(os.environ.get("MAX_RESULT_LINES", "200"))
MAX_SCAN_LINES = int(os.environ.get("MAX_SCAN_LINES", "10000"))

SYSLOG_TIMESTAMP_RE = re.compile(r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})")

MONTH_MAP = {
                "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,  "May": 5,  "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
            }

# Parses syslog timestamps in the format "Mmm dd HH:MM:SS" and returns a datetime object.
def parse_syslog_timestamp(line):
    match = SYSLOG_TIMESTAMP_RE.match(line)
    if not match:
        return None

    now = datetime.datetime.now()
    month = MONTH_MAP.get(match.group("month"))
    if month is None:
        return None

    day = int(match.group("day"))
    time_str = match.group("time")
    try:
        dt = datetime.datetime.strptime(f"{month} {day} {time_str} {now.year}", "%m %d %H:%M:%S %Y")
    except ValueError:
        return None

    if dt > now + datetime.timedelta(days=1):
        dt = dt.replace(year=dt.year - 1)
    return dt

# reads the last N lines of a file without loading the entire file into memory.
def tail_lines(path, max_lines=MAX_SCAN_LINES):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        position = f.tell() - 1
        buffer = bytearray()
        lines = collections.deque()

        while position >= 0 and len(lines) <= max_lines:
            f.seek(position)
            byte = f.read(1)
            if byte == b"\n":
                if buffer:
                    lines.appendleft(buffer[::-1].decode(errors="ignore"))
                    buffer = bytearray()
            else:
                buffer.append(byte[0])
            position -= 1

        if buffer:
            lines.appendleft(buffer[::-1].decode(errors="ignore"))

        return list(lines)[-max_lines:]

def collect_journal_logs(query, minutes):
    query_lower = query.lower().strip()
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=max(minutes, 0))
    since_arg = f"{minutes} minutes ago"

    for journal_dir in JOURNAL_DIRS:
        if not os.path.isdir(journal_dir):
            continue

        cmd = [
            "journalctl",
            "--directory",
            journal_dir,
            "--since",
            since_arg,
            "--no-pager",
            "--output=short-iso",
        ]
        if query_lower:
            cmd += ["--grep", query]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            continue

        logs = [line for line in proc.stdout.splitlines() if line.strip()]
        if logs:
            return logs[:MAX_RESULT_LINES]

    return []


# Collects system logs matching the query and within the specified time range.
def collect_system_logs(query, minutes):
    text_results = []
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=max(minutes, 0))
    query_lower = query.lower().strip()

    for filename in LOG_FILES:
        path = os.path.join(LOG_ROOT, filename)
        if not os.path.isfile(path):
            continue

        try:
            for line in tail_lines(path):
                if query_lower and query_lower not in line.lower():
                    continue

                timestamp = parse_syslog_timestamp(line)
                if timestamp and timestamp < cutoff:
                    continue

                text_results.append(line.rstrip("\n"))
                if len(text_results) >= MAX_RESULT_LINES:
                    return text_results
        except Exception:
            continue

    if text_results:
        return text_results

    journal_results = collect_journal_logs(query, minutes)
    if journal_results:
        return journal_results

    return [
        f"No matching system log entries found for query '{query}' in the last {minutes} minutes."
    ]

# WebSocket handler that processes incoming JSON-RPC requests to fetch logs.
async def handler(websocket):
    async for msg in websocket:
        req = json.loads(msg)

        if req["method"] == "tools.call":
            name = req["params"]["name"]

            if name == "get_logs":
                query = req["params"]["arguments"].get("query", "")
                minutes = int(req["params"]["arguments"].get("minutes", 60))

                logs = collect_system_logs(query, minutes)
                result = {"logs": logs}

                await websocket.send(
                    json.dumps({
                        "jsonrpc": "2.0",
                        "id": req["id"],
                        "result": result,
                    })
                )


async def main():
    async with websockets.serve(handler, "0.0.0.0", 6001):
        await asyncio.Future()


asyncio.run(main())
