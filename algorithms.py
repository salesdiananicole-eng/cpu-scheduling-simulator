from collections import deque


def merge_gantt(blocks):
    """Merge adjacent Gantt blocks belonging to the same process (used by SRTF)."""
    if not blocks:
        return []
    merged = [list(blocks[0])]
    for pid, start, end in blocks[1:]:
        if pid == merged[-1][0] and start == merged[-1][2]:
            merged[-1][2] = end
        else:
            merged.append([pid, start, end])
    return [(b[0], b[1], b[2]) for b in merged]


def compute_metrics(processes, completion_times, first_run_times):
    """Compute CT, TAT, WT, RT per process and overall averages."""
    rows = []
    for p in processes:
        pid = p["pid"]
        at = p["at"]
        bt = p["bt"]
        ct = completion_times[pid]
        tat = ct - at
        wt = tat - bt
        rt = first_run_times[pid] - at
        rows.append({
            "pid": pid,
            "at": at,
            "bt": bt,
            "ct": ct,
            "tat": tat,
            "wt": wt,
            "rt": rt,
        })

    n = len(rows)
    averages = {
        "ct": sum(r["ct"] for r in rows) / n if n else 0.0,
        "tat": sum(r["tat"] for r in rows) / n if n else 0.0,
        "wt": sum(r["wt"] for r in rows) / n if n else 0.0,
        "rt": sum(r["rt"] for r in rows) / n if n else 0.0,
    }
    return rows, averages


def schedule_fcfs(processes):
    """First-Come, First-Served (Non-Preemptive)."""
    procs = sorted(processes, key=lambda x: (x["at"], x["index"]))
    time = 0
    gantt = []
    ct, rt = {}, {}

    for p in procs:
        if time < p["at"]:
            gantt.append(("IDLE", time, p["at"]))
            time = p["at"]
        rt[p["pid"]] = time
        start = time
        time += p["bt"]
        ct[p["pid"]] = time
        gantt.append((p["pid"], start, time))

    rows, avgs = compute_metrics(processes, ct, rt)
    return {"name": "FCFS", "gantt": gantt, "rows": rows, "avgs": avgs}


def schedule_sjf(processes):
    """Shortest Job First (Non-Preemptive)."""
    n = len(processes)
    completed = set()
    time = 0
    gantt = []
    ct, rt = {}, {}

    while len(completed) < n:
        available = [
            p for p in processes
            if p["pid"] not in completed and p["at"] <= time
        ]
        if not available:
            next_at = min(p["at"] for p in processes if p["pid"] not in completed)
            gantt.append(("IDLE", time, next_at))
            time = next_at
            continue

        chosen = min(available, key=lambda x: (x["bt"], x["at"], x["index"]))
        rt[chosen["pid"]] = time
        start = time
        time += chosen["bt"]
        ct[chosen["pid"]] = time
        completed.add(chosen["pid"])
        gantt.append((chosen["pid"], start, time))

    rows, avgs = compute_metrics(processes, ct, rt)
    return {"name": "SJF (Non-Preemptive)", "gantt": gantt, "rows": rows, "avgs": avgs}


def schedule_srtf(processes):
    """Shortest Remaining Time First (Preemptive SJF)."""
    n = len(processes)
    rem = {p["pid"]: p["bt"] for p in processes}
    completed = set()
    time = 0
    gantt = []
    ct, rt = {}, {}

    while len(completed) < n:
        available = [
            p for p in processes
            if p["pid"] not in completed and p["at"] <= time
        ]
        if not available:
            next_at = min(p["at"] for p in processes if p["pid"] not in completed)
            gantt.append(("IDLE", time, next_at))
            time = next_at
            continue

        chosen = min(available, key=lambda x: (rem[x["pid"]], x["at"], x["index"]))
        pid = chosen["pid"]
        if pid not in rt:
            rt[pid] = time

        gantt.append((pid, time, time + 1))
        rem[pid] -= 1
        time += 1

        if rem[pid] == 0:
            ct[pid] = time
            completed.add(pid)

    rows, avgs = compute_metrics(processes, ct, rt)
    return {"name": "SRTF (Preemptive)", "gantt": merge_gantt(gantt), "rows": rows, "avgs": avgs}


def schedule_round_robin(processes, quantum):
    """Round Robin (Preemptive) with per-quantum remaining burst time trace."""
    procs = sorted(processes, key=lambda x: (x["at"], x["index"]))
    n = len(procs)
    rem = {p["pid"]: p["bt"] for p in procs}
    in_queue = set()
    queue = deque()
    time = 0
    idx = 0
    completed = 0
    gantt = []
    quantum_trace = []
    ct, rt = {}, {}
    step_num = 1

    while completed < n:
        while idx < n and procs[idx]["at"] <= time:
            queue.append(procs[idx])
            in_queue.add(procs[idx]["pid"])
            idx += 1

        if not queue:
            next_at = procs[idx]["at"]
            gantt.append(("IDLE", time, next_at))
            time = next_at
            continue

        current = queue.popleft()
        pid = current["pid"]
        if pid not in rt:
            rt[pid] = time

        prev_bt = rem[pid]
        exec_time = min(quantum, prev_bt)
        start = time
        time += exec_time
        rem[pid] -= exec_time
        gantt.append((pid, start, time))

        while idx < n and procs[idx]["at"] <= time:
            if procs[idx]["pid"] not in in_queue:
                queue.append(procs[idx])
                in_queue.add(procs[idx]["pid"])
            idx += 1

        if rem[pid] > 0:
            queue.append(current)
            status = f"Preempted (Rem: {rem[pid]})"
        else:
            ct[pid] = time
            completed += 1
            status = "Completed"

        quantum_trace.append({
            "step": f"Q{step_num}",
            "interval": f"{start} -> {time}",
            "pid": pid,
            "prev_bt": prev_bt,
            "used": exec_time,
            "rem_bt": rem[pid],
            "status": status,
        })
        step_num += 1

    rows, avgs = compute_metrics(processes, ct, rt)
    return {
        "name": f"Round Robin (Q={quantum})",
        "quantum": quantum,
        "gantt": gantt,
        "rows": rows,
        "avgs": avgs,
        "trace": quantum_trace,
    }


def generate_short_comparison(results_map, quantum):
    """Build a concise analytical comparison across all 4 simulated algorithms."""
    fcfs = results_map["FCFS"]
    sjf = results_map["SJF"]
    srtf = results_map["SRTF"]
    rr = results_map["RR"]

    all_algos = [fcfs, sjf, srtf, rr]
    best_wt = min(all_algos, key=lambda x: x["avgs"]["wt"])
    best_tat = min(all_algos, key=lambda x: x["avgs"]["tat"])
    best_rt = min(all_algos, key=lambda x: x["avgs"]["rt"])

    lines = [
        f"* Lowest Average Waiting Time: {best_wt['name']} ({best_wt['avgs']['wt']:.2f} units) - "
        f"minimizes idle queue delay by prioritizing shorter jobs.",
        f"* Lowest Average Turnaround Time: {best_tat['name']} ({best_tat['avgs']['tat']:.2f} units) - "
        f"completes processes fastest from arrival to completion.",
        f"* Fastest Average Response Time: {best_rt['name']} ({best_rt['avgs']['rt']:.2f} units) - "
        f"gives processes earliest initial CPU access.",
        f"* Trade-off Summary: FCFS ({fcfs['avgs']['wt']:.2f} avg WT) is simple but prone to the convoy effect "
        f"when long bursts arrive first. Non-preemptive SJF ({sjf['avgs']['wt']:.2f} avg WT) and preemptive SRTF "
        f"({srtf['avgs']['wt']:.2f} avg WT) optimize waiting/turnaround times, while Round Robin (Q={quantum}, "
        f"{rr['avgs']['wt']:.2f} avg WT, {rr['avgs']['rt']:.2f} avg RT) ensures fair time-sharing across all processes.",
    ]
    return "\n".join(lines)