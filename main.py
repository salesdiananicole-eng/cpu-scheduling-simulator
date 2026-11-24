import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque


# ==============================================================================
# CPU SCHEDULING ALGORITHMS ENGINE (FCFS, SJF, SRTF, ROUND ROBIN)
# ==============================================================================

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

        while idx < n and procs[idx]["at"] < time:
            if procs[idx]["pid"] not in in_queue:
                queue.append(procs[idx])
                in_queue.add(procs[idx]["pid"])
            idx += 1

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


# ==============================================================================
# TKINTER GUI APPLICATION (CODEHS / LINUX COMPATIBLE)
# ==============================================================================

class CPUSchedulerApp:
    PALETTE = [
        "#93C5FD",  # Blue
        "#86EFAC",  # Green
        "#FDBA74",  # Orange
        "#F9A8D4",  # Pink
        "#C4B5FD",  # Purple
        "#FDE047",  # Yellow
        "#5EEAD4",  # Teal
        "#FCA5A5",  # Red
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Topic 1: CPU Scheduling Simulator (FCFS, SJF, SRTF, Round Robin)")
        self.root.geometry("940x650")
        self.root.minsize(640, 480)
        self.root.configure(bg="#EEF2F6")

        self.process_rows = []
        self.results_cache = {}
        self.pid_color_map = {}

        self._configure_styles()
        self._build_layout()
        self.load_rr_sample()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=23, font=("Arial", 9))
        style.configure(
            "Treeview.Heading",
            font=("Arial", 9, "bold"),
            background="#E5E7EB",
            foreground="#111827",
        )
        style.configure("TNotebook", background="#FFFFFF", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Arial", 9, "bold"), padding=[10, 4])
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#1D63DC"), ("!selected", "#E5E7EB")],
            foreground=[("selected", "#FFFFFF"), ("!selected", "#1F2937")],
        )

    def _build_layout(self):
        container = tk.Frame(self.root, bg="#EEF2F6", padx=12, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        # ======================================================================
        # TOP INPUT PANEL
        # ======================================================================
        top_frame = tk.Frame(container, bg="#EEF2F6")
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Left Card: Simulation Parameters
        param_card = tk.Frame(
            top_frame, bg="#FFFFFF", bd=1, relief="solid",
            highlightbackground="#D1D5DB", highlightthickness=1, padx=12, pady=8
        )
        param_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        tk.Label(
            param_card, text="Simulation Parameters:", font=("Arial", 10, "bold"),
            bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w", pady=(0, 6))

        # Number of processes input
        num_row = tk.Frame(param_card, bg="#FFFFFF")
        num_row.pack(fill=tk.X, pady=2)
        tk.Label(
            num_row, text="Number of Processes:", font=("Arial", 9),
            bg="#FFFFFF", fg="#374151"
        ).pack(side=tk.LEFT)
        self.num_proc_var = tk.StringVar(value="4")
        tk.Entry(
            num_row, textvariable=self.num_proc_var, width=5,
            font=("Arial", 9), justify="center", relief="solid", bd=1
        ).pack(side=tk.LEFT, padx=(6, 4))
        tk.Button(
            num_row, text="Apply", font=("Arial", 8, "bold"),
            bg="#E0F2FE", fg="#0369A1", relief="flat", padx=6, pady=1,
            cursor="hand2", command=self.apply_process_count
        ).pack(side=tk.LEFT)

        # RR Time Quantum input
        tq_row = tk.Frame(param_card, bg="#FFFFFF")
        tq_row.pack(fill=tk.X, pady=5)
        tk.Label(
            tq_row, text="RR Time Quantum (Q):", font=("Arial", 9),
            bg="#FFFFFF", fg="#374151"
        ).pack(side=tk.LEFT)
        self.tq_var = tk.StringVar(value="3")
        tk.Entry(
            tq_row, textvariable=self.tq_var, width=5,
            font=("Arial", 9), justify="center", relief="solid", bd=1
        ).pack(side=tk.LEFT, padx=(6, 0))

        # Focus View Dropdown
        view_row = tk.Frame(param_card, bg="#FFFFFF")
        view_row.pack(fill=tk.X, pady=(3, 5))
        tk.Label(
            view_row, text="Focus View:", font=("Arial", 9),
            bg="#FFFFFF", fg="#374151"
        ).pack(side=tk.LEFT)
        self.view_var = tk.StringVar(value="All Algorithms (Compare)")
        self.view_combo = ttk.Combobox(
            view_row,
            textvariable=self.view_var,
            values=[
                "All Algorithms (Compare)",
                "FCFS",
                "SJF (Non-Preemptive)",
                "SRTF (Preemptive)",
                "Round Robin (RR)",
            ],
            state="readonly",
            width=21,
            font=("Arial", 8),
        )
        self.view_combo.pack(side=tk.LEFT, padx=(6, 0))
        self.view_combo.bind("<<ComboboxSelected>>", self._on_dropdown_select)

        # Sample Presets
        preset_row = tk.Frame(param_card, bg="#FFFFFF")
        preset_row.pack(fill=tk.X, pady=(3, 0))
        tk.Label(
            preset_row, text="Presets:", font=("Arial", 8, "bold"),
            bg="#FFFFFF", fg="#6B7280"
        ).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(
            preset_row, text="4-Process Sample", font=("Arial", 8),
            bg="#F3F4F6", fg="#1F2937", relief="groove", padx=5, pady=1,
            command=self.load_rr_sample
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            preset_row, text="FCFS Sample", font=("Arial", 8),
            bg="#F3F4F6", fg="#1F2937", relief="groove", padx=5, pady=1,
            command=self.load_fcfs_sample
        ).pack(side=tk.LEFT)

        # Middle Card: Process Information Table
        proc_card = tk.Frame(
            top_frame, bg="#FFFFFF", bd=1, relief="solid",
            highlightbackground="#D1D5DB", highlightthickness=1, padx=12, pady=8
        )
        proc_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        proc_top = tk.Frame(proc_card, bg="#FFFFFF")
        proc_top.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            proc_top, text="Process Information:", font=("Arial", 10, "bold"),
            bg="#FFFFFF", fg="#111827"
        ).pack(side=tk.LEFT)

        row_btns = tk.Frame(proc_top, bg="#FFFFFF")
        row_btns.pack(side=tk.RIGHT)
        tk.Button(
            row_btns, text="+ Add", font=("Arial", 8, "bold"),
            bg="#E0F2FE", fg="#0369A1", relief="flat", padx=7, pady=1,
            cursor="hand2", command=self.add_process_row
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            row_btns, text="- Remove", font=("Arial", 8, "bold"),
            bg="#FEE2E2", fg="#B91C1C", relief="flat", padx=7, pady=1,
            cursor="hand2", command=self.remove_process_row
        ).pack(side=tk.LEFT)

        hdr = tk.Frame(proc_card, bg="#F9FAFB", pady=3)
        hdr.pack(fill=tk.X)
        for text, width in [("Process ID", 12), ("Arrival Time", 14), ("Burst Time", 14)]:
            tk.Label(
                hdr, text=text, width=width, font=("Arial", 8, "bold"),
                bg="#F9FAFB", fg="#4B5563"
            ).pack(side=tk.LEFT, padx=4)

        scroll_box = tk.Frame(proc_card, bg="#FFFFFF", height=105)
        scroll_box.pack(fill=tk.BOTH, expand=True)
        scroll_box.pack_propagate(False)

        self.proc_canvas = tk.Canvas(scroll_box, bg="#FFFFFF", highlightthickness=0)
        proc_sb = ttk.Scrollbar(scroll_box, orient="vertical", command=self.proc_canvas.yview)
        self.proc_list_frame = tk.Frame(self.proc_canvas, bg="#FFFFFF")

        self.proc_list_frame.bind(
            "<Configure>",
            lambda e: self.proc_canvas.configure(scrollregion=self.proc_canvas.bbox("all"))
        )
        self.proc_canvas.create_window((0, 0), window=self.proc_list_frame, anchor="nw")
        self.proc_canvas.configure(yscrollcommand=proc_sb.set)

        self.proc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        proc_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Right Action Button
        action_col = tk.Frame(top_frame, bg="#EEF2F6")
        action_col.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(
            action_col,
            text="Run Simulation",
            font=("Arial", 10, "bold"),
            bg="#1D63DC",
            fg="#FFFFFF",
            activebackground="#1E40AF",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
            command=self.run_all_simulations,
        ).pack(pady=42)

        # ======================================================================
        # BOTTOM RESULTS PANEL
        # ======================================================================
        results_card = tk.Frame(
            container, bg="#FFFFFF", bd=1, relief="solid",
            highlightbackground="#D1D5DB", highlightthickness=1
        )
        results_card.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(results_card, bg="#1D63DC", padx=12, pady=6)
        title_bar.pack(fill=tk.X)
        tk.Label(
            title_bar,
            text="Results - All Algorithms Simulated (FCFS, SJF, SRTF, Round Robin)",
            font=("Arial", 10, "bold"),
            bg="#1D63DC",
            fg="#FFFFFF",
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(results_card)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 4))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tab_compare = tk.Frame(self.notebook, bg="#FFFFFF")
        self.tab_fcfs = tk.Frame(self.notebook, bg="#FFFFFF")
        self.tab_sjf = tk.Frame(self.notebook, bg="#FFFFFF")
        self.tab_srtf = tk.Frame(self.notebook, bg="#FFFFFF")
        self.tab_rr = tk.Frame(self.notebook, bg="#FFFFFF")

        self.notebook.add(self.tab_compare, text="All Algorithms & Comparison")
        self.notebook.add(self.tab_fcfs, text="FCFS")
        self.notebook.add(self.tab_sjf, text="SJF")
        self.notebook.add(self.tab_srtf, text="SRTF")
        self.notebook.add(self.tab_rr, text="Round Robin (Quantum Trace)")

        self._build_comparison_tab()
        self.algo_widgets = {
            "FCFS": self._build_single_algo_tab(self.tab_fcfs, "FCFS", is_rr=False),
            "SJF": self._build_single_algo_tab(self.tab_sjf, "SJF", is_rr=False),
            "SRTF": self._build_single_algo_tab(self.tab_srtf, "SRTF", is_rr=False),
            "RR": self._build_single_algo_tab(self.tab_rr, "RR", is_rr=True),
        }

        status_banner = tk.Frame(results_card, bg="#DCFCE7", pady=6, padx=12)
        status_banner.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 8))
        self.status_var = tk.StringVar(value="Simulation Completed!")
        tk.Label(
            status_banner,
            textvariable=self.status_var,
            font=("Arial", 9, "bold"),
            bg="#DCFCE7",
            fg="#166534",
        ).pack()

    # --------------------------------------------------------------------------
    # TAB BUILDERS
    # --------------------------------------------------------------------------

    def _build_comparison_tab(self):
        wrapper = tk.Frame(self.tab_compare, bg="#FFFFFF", padx=6, pady=5)
        wrapper.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(wrapper, bg="#FFFFFF")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            left_col, text="Gantt Charts / Timelines per Algorithm:",
            font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w", pady=(0, 4))

        self.overview_gantts = {}
        for key, label in [
            ("FCFS", "1. FCFS"),
            ("SJF", "2. SJF (Non-Preemptive)"),
            ("SRTF", "3. SRTF (Preemptive)"),
            ("RR", "4. Round Robin"),
        ]:
            row = tk.Frame(left_col, bg="#F9FAFB", bd=1, relief="solid", padx=5, pady=2)
            row.pack(fill=tk.X, pady=2)

            lbl_var = tk.StringVar(value=label)
            tk.Label(
                row, textvariable=lbl_var, width=20, anchor="w",
                font=("Arial", 8, "bold"), bg="#F9FAFB", fg="#1F2937"
            ).pack(side=tk.LEFT)

            cv = tk.Canvas(row, height=44, bg="#F9FAFB", highlightthickness=0)
            cv.pack(side=tk.LEFT, fill=tk.X, expand=True)
            cv.bind("<Configure>", lambda e, k=key: self._redraw_overview_gantt(k))
            self.overview_gantts[key] = {"canvas": cv, "label_var": lbl_var}

        right_col = tk.Frame(wrapper, bg="#FFFFFF")
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.comp_header_var = tk.StringVar(value="Algorithm Comparison (RR Quantum = 3):")
        tk.Label(
            right_col, textvariable=self.comp_header_var,
            font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w", pady=(0, 4))

        cols = ("Algorithm", "Avg CT", "Avg TAT", "Avg WT", "Avg RT")
        self.comp_tree = ttk.Treeview(right_col, columns=cols, show="headings", height=4)
        for c in cols:
            self.comp_tree.heading(c, text=c)
            self.comp_tree.column(c, width=135 if c == "Algorithm" else 65, anchor="center")
        self.comp_tree.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            right_col, text="Short Comparison:",
            font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w", pady=(2, 3))

        self.comp_text = tk.Text(
            right_col, height=7, wrap="word", font=("Arial", 9),
            bg="#F8FAFC", fg="#1E293B", relief="solid", bd=1, padx=6, pady=5
        )
        self.comp_text.pack(fill=tk.BOTH, expand=True)
        self.comp_text.configure(state="disabled")

    def _build_single_algo_tab(self, parent, algo_key, is_rr=False):
        wrapper = tk.Frame(parent, bg="#FFFFFF", padx=6, pady=5)
        wrapper.pack(fill=tk.BOTH, expand=True)

        gantt_title_var = tk.StringVar(value=f"Gantt Chart ({algo_key}):")
        tk.Label(
            wrapper, textvariable=gantt_title_var,
            font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w")

        gantt_cv = tk.Canvas(wrapper, height=68, bg="#FFFFFF", highlightthickness=0)
        gantt_cv.pack(fill=tk.X, pady=(2, 6))
        gantt_cv.bind("<Configure>", lambda e, k=algo_key: self._redraw_single_gantt(k))

        split = tk.Frame(wrapper, bg="#FFFFFF")
        split.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(split, bg="#FFFFFF")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8 if is_rr else 0))

        tk.Label(
            left, text="Per-Process Metrics:",
            font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
        ).pack(anchor="w", pady=(0, 3))

        cols = ("Process ID", "AT", "BT", "CT", "TAT", "WT", "RT")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=5)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=72 if c == "Process ID" else 50, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        avg_bar = tk.Frame(left, bg="#F8FAFC", bd=1, relief="solid", padx=8, pady=5)
        avg_bar.pack(fill=tk.X, pady=(5, 0))

        avg_vars = {
            "ct": tk.StringVar(value="0.00"),
            "tat": tk.StringVar(value="0.00"),
            "wt": tk.StringVar(value="0.00"),
            "rt": tk.StringVar(value="0.00"),
        }
        for label, key in [
            ("Avg CT:", "ct"),
            ("Avg TAT:", "tat"),
            ("Avg WT:", "wt"),
            ("Avg RT:", "rt"),
        ]:
            tk.Label(
                avg_bar, text=label, font=("Arial", 8, "bold"),
                bg="#F8FAFC", fg="#374151"
            ).pack(side=tk.LEFT, padx=(0, 2))
            tk.Label(
                avg_bar, textvariable=avg_vars[key], font=("Arial", 8, "bold"),
                bg="#F8FAFC", fg="#1D63DC"
            ).pack(side=tk.LEFT, padx=(0, 10))

        rr_tree = None
        rr_hdr_var = None
        if is_rr:
            right = tk.Frame(split, bg="#FFFFFF")
            right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            rr_hdr_var = tk.StringVar(value="Round Robin Quantum Execution & Remaining Burst Time:")
            tk.Label(
                right, textvariable=rr_hdr_var,
                font=("Arial", 9, "bold"), bg="#FFFFFF", fg="#111827"
            ).pack(anchor="w", pady=(0, 3))

            rr_cols = ("Quantum", "Time", "Process", "Prev BT", "Used", "Rem BT", "Status")
            rr_tree = ttk.Treeview(right, columns=rr_cols, show="headings", height=7)
            widths = {
                "Quantum": 58,
                "Time": 68,
                "Process": 58,
                "Prev BT": 55,
                "Used": 45,
                "Rem BT": 55,
                "Status": 125,
            }
            for c in rr_cols:
                rr_tree.heading(c, text=c)
                rr_tree.column(c, width=widths[c], anchor="center")
            rr_tree.pack(fill=tk.BOTH, expand=True)

        return {
            "gantt_title": gantt_title_var,
            "canvas": gantt_cv,
            "tree": tree,
            "avg_vars": avg_vars,
            "rr_tree": rr_tree,
            "rr_hdr": rr_hdr_var,
        }

    # --------------------------------------------------------------------------
    # PROCESS ROW CONTROLS & PRESETS
    # --------------------------------------------------------------------------

    def add_process_row(self, pid=None, at="0", bt="5"):
        idx = len(self.process_rows) + 1
        pid_text = pid if pid is not None else f"P{idx}"

        row = tk.Frame(self.proc_list_frame, bg="#FFFFFF", pady=2)
        row.pack(fill=tk.X)

        pid_var = tk.StringVar(value=pid_text)
        at_var = tk.StringVar(value=str(at))
        bt_var = tk.StringVar(value=str(bt))

        for var, w in [(pid_var, 12), (at_var, 14), (bt_var, 14)]:
            tk.Entry(
                row, textvariable=var, width=w, font=("Arial", 9),
                justify="center", relief="solid", bd=1
            ).pack(side=tk.LEFT, padx=4)

        self.process_rows.append({"frame": row, "pid": pid_var, "at": at_var, "bt": bt_var})
        self.num_proc_var.set(str(len(self.process_rows)))

    def remove_process_row(self):
        if len(self.process_rows) <= 1:
            messagebox.showwarning("Minimum Processes", "At least 1 process is required.")
            return
        row = self.process_rows.pop()
        row["frame"].destroy()
        self.num_proc_var.set(str(len(self.process_rows)))

    def apply_process_count(self):
        try:
            target = int(self.num_proc_var.get().strip())
            if target < 1 or target > 20:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Count", "Enter a number of processes between 1 and 20.")
            return

        while len(self.process_rows) < target:
            self.add_process_row(at="0", bt="4")
        while len(self.process_rows) > target:
            row = self.process_rows.pop()
            row["frame"].destroy()
        self.num_proc_var.set(str(len(self.process_rows)))

    def clear_rows(self):
        for r in self.process_rows:
            r["frame"].destroy()
        self.process_rows.clear()

    def load_rr_sample(self):
        self.clear_rows()
        self.tq_var.set("3")
        for pid, at, bt in [("P1", 0, 7), ("P2", 1, 4), ("P3", 2, 3), ("P4", 3, 5)]:
            self.add_process_row(pid, at, bt)
        self.run_all_simulations()

    def load_fcfs_sample(self):
        self.clear_rows()
        self.tq_var.set("3")
        for pid, at, bt in [("P1", 0, 24), ("P2", 0, 3), ("P3", 0, 3)]:
            self.add_process_row(pid, at, bt)
        self.run_all_simulations()

    # --------------------------------------------------------------------------
    # TAB & DROPDOWN SYNCHRONIZATION
    # --------------------------------------------------------------------------

    def _on_dropdown_select(self, event=None):
        mapping = {
            "All Algorithms (Compare)": 0,
            "FCFS": 1,
            "SJF (Non-Preemptive)": 2,
            "SRTF (Preemptive)": 3,
            "Round Robin (RR)": 4,
        }
        idx = mapping.get(self.view_var.get(), 0)
        self.notebook.select(idx)

    def _on_tab_changed(self, event=None):
        reverse_map = [
            "All Algorithms (Compare)",
            "FCFS",
            "SJF (Non-Preemptive)",
            "SRTF (Preemptive)",
            "Round Robin (RR)",
        ]
        idx = self.notebook.index(self.notebook.select())
        if 0 <= idx < len(reverse_map):
            self.view_var.set(reverse_map[idx])

    # --------------------------------------------------------------------------
    # SIMULATION & RENDERING
    # --------------------------------------------------------------------------

    def _parse_inputs(self):
        processes = []
        seen_pids = set()
        for idx, row in enumerate(self.process_rows):
            pid = row["pid"].get().strip()
            if not pid:
                raise ValueError(f"Row {idx + 1}: Process ID cannot be empty.")
            if pid in seen_pids:
                raise ValueError(f"Duplicate Process ID '{pid}'. Each Process ID must be unique.")
            seen_pids.add(pid)

            try:
                at = int(row["at"].get().strip())
                bt = int(row["bt"].get().strip())
            except ValueError:
                raise ValueError(f"{pid}: Arrival Time and Burst Time must be integers.")

            if at < 0:
                raise ValueError(f"{pid}: Arrival Time cannot be negative.")
            if bt <= 0:
                raise ValueError(f"{pid}: Burst Time must be greater than 0.")

            processes.append({"index": idx, "pid": pid, "at": at, "bt": bt})

        try:
            quantum = int(self.tq_var.get().strip())
        except ValueError:
            raise ValueError("RR Time Quantum must be a valid integer.")
        if quantum <= 0:
            raise ValueError("RR Time Quantum must be greater than 0.")

        return processes, quantum

    def run_all_simulations(self):
        try:
            processes, quantum = self._parse_inputs()
        except ValueError as err:
            messagebox.showerror("Input Error", str(err))
            return

        self.results_cache = {
            "FCFS": schedule_fcfs(processes),
            "SJF": schedule_sjf(processes),
            "SRTF": schedule_srtf(processes),
            "RR": schedule_round_robin(processes, quantum),
        }
        self.pid_color_map = {
            p["pid"]: self.PALETTE[i % len(self.PALETTE)]
            for i, p in enumerate(processes)
        }
        self.pid_color_map["IDLE"] = "#E5E7EB"

        # 1. Update Overview & Comparison Tab
        self.comp_header_var.set(f"Algorithm Comparison (Processes = {len(processes)}, RR Quantum = {quantum}):")
        self.overview_gantts["RR"]["label_var"].set(f"4. Round Robin (Q={quantum})")

        for item in self.comp_tree.get_children():
            self.comp_tree.delete(item)

        for key in ("FCFS", "SJF", "SRTF", "RR"):
            res = self.results_cache[key]
            av = res["avgs"]
            self.comp_tree.insert(
                "", "end",
                values=(
                    res["name"],
                    f"{av['ct']:.2f}",
                    f"{av['tat']:.2f}",
                    f"{av['wt']:.2f}",
                    f"{av['rt']:.2f}",
                ),
            )
            self._redraw_overview_gantt(key)

        summary_text = generate_short_comparison(self.results_cache, quantum)
        self.comp_text.configure(state="normal")
        self.comp_text.delete("1.0", tk.END)
        self.comp_text.insert("1.0", summary_text)
        self.comp_text.configure(state="disabled")

        # 2. Update Individual Algorithm Tabs
        for key in ("FCFS", "SJF", "SRTF", "RR"):
            res = self.results_cache[key]
            w = self.algo_widgets[key]
            w["gantt_title"].set(f"Gantt Chart / Timeline - {res['name']}:")
            self._redraw_single_gantt(key)

            for item in w["tree"].get_children():
                w["tree"].delete(item)
            for r in res["rows"]:
                w["tree"].insert(
                    "", "end",
                    values=(r["pid"], r["at"], r["bt"], r["ct"], r["tat"], r["wt"], r["rt"])
                )

            for m_key in ("ct", "tat", "wt", "rt"):
                w["avg_vars"][m_key].set(f"{res['avgs'][m_key]:.2f}")

            if key == "RR":
                w["rr_hdr"].set(f"Round Robin Trace (Time Quantum = {quantum}) - Each Quantum & Remaining BT:")
                for item in w["rr_tree"].get_children():
                    w["rr_tree"].delete(item)
                for step in res["trace"]:
                    w["rr_tree"].insert(
                        "", "end",
                        values=(
                            step["step"],
                            step["interval"],
                            step["pid"],
                            step["prev_bt"],
                            step["used"],
                            step["rem_bt"],
                            step["status"],
                        ),
                    )

        self.status_var.set(
            f"Simulated All 4 Algorithms (FCFS, SJF, SRTF, RR with Q={quantum}) for {len(processes)} Processes!"
        )

    def _draw_gantt_on_canvas(self, canvas, gantt, bar_height=34, top_pad=4):
        canvas.delete("all")
        if not gantt:
            return

        w = max(canvas.winfo_width(), 300)
        pad_x = 12
        usable_w = w - 2 * pad_x
        total_duration = gantt[-1][2] - gantt[0][1]
        if total_duration <= 0:
            return

        n_blocks = len(gantt)
        min_w = 22
        if n_blocks * min_w > usable_w:
            widths = [usable_w / n_blocks] * n_blocks
        else:
            rem_w = usable_w - n_blocks * min_w
            widths = [min_w + ((end - start) / total_duration) * rem_w for _, start, end in gantt]

        curr_x = pad_x
        canvas.create_text(
            curr_x, top_pad + bar_height + 10,
            text=str(gantt[0][1]), font=("Arial", 8, "bold"), fill="#374151"
        )

        for i, (pid, start, end) in enumerate(gantt):
            bw = widths[i]
            fill_color = self.pid_color_map.get(pid, "#93C5FD")
            canvas.create_rectangle(
                curr_x, top_pad, curr_x + bw, top_pad + bar_height,
                fill=fill_color, outline="#4B5563", width=1
            )
            canvas.create_text(
                curr_x + bw / 2, top_pad + bar_height / 2,
                text=pid, font=("Arial", 8, "bold"), fill="#111827"
            )
            curr_x += bw
            canvas.create_text(
                curr_x, top_pad + bar_height + 10,
                text=str(end), font=("Arial", 8, "bold"), fill="#374151"
            )

    def _redraw_overview_gantt(self, key):
        if key in self.results_cache:
            cv = self.overview_gantts[key]["canvas"]
            self._draw_gantt_on_canvas(cv, self.results_cache[key]["gantt"], bar_height=22, top_pad=3)

    def _redraw_single_gantt(self, key):
        if key in self.results_cache:
            cv = self.algo_widgets[key]["canvas"]
            self._draw_gantt_on_canvas(cv, self.results_cache[key]["gantt"], bar_height=36, top_pad=6)


if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSchedulerApp(root)
    root.mainloop()