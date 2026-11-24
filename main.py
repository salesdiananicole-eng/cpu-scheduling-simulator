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

# ==============================================================================
# TKINTER GUI APPLICATION (GITHUB DARK MODE THEME)
# ==============================================================================

class CPUSchedulerApp:
    GH = {
        "canvas": "#0D1117",        # Main GitHub dark background
        "card": "#161B22",          # Elevated card / box surface
        "subtle": "#21262D",        # Headers, inputs, secondary buttons
        "hover": "#30363D",         # Hover / active borders
        "border": "#30363D",        # Signature 1px GitHub dark border
        "text": "#F0F6FC",          # Crisp primary text
        "text_body": "#E6EDF3",     # Standard body text
        "muted": "#8B949E",         # Secondary labels
        "green": "#238636",         # GitHub primary green button
        "green_hover": "#2EA043",   # GitHub button hover
        "green_bg": "#12261E",      # GitHub dark success banner fill
        "green_fg": "#3FB950",      # GitHub bright green status text
        "blue": "#1F6FEB",          # GitHub active tab / selection blue
        "blue_link": "#58A6FF",     # GitHub accent blue
        "red_fg": "#F85149",        # GitHub danger red text
    }

    PALETTE = [
        "#58A6FF",  # GitHub Blue
        "#3FB950",  # GitHub Green
        "#D29922",  # GitHub Amber
        "#F778BA",  # GitHub Pink
        "#A371F7",  # GitHub Purple
        "#39C5CF",  # GitHub Cyan
        "#FFA657",  # GitHub Orange
        "#FF7B72",  # GitHub Coral
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Topic 1: CPU Scheduling Simulator (FCFS, SJF, SRTF, Round Robin)")
        self.root.geometry("880x690+25+10")
        self.root.minsize(680, 520)
        self.root.configure(bg=self.GH["canvas"])

        self.process_rows = []
        self.results_cache = {}
        self.pid_color_map = {}

        self._configure_styles()
        self._build_layout()
        self.load_rr_sample()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=self.GH["card"],
            fieldbackground=self.GH["card"],
            foreground=self.GH["text_body"],
            bordercolor=self.GH["border"],
            lightcolor=self.GH["border"],
            darkcolor=self.GH["border"],
            rowheight=24,
            font=("Arial", 9),
        )
        style.map(
            "Treeview",
            background=[("selected", self.GH["blue"])],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 9, "bold"),
            background=self.GH["subtle"],
            foreground=self.GH["text"],
            bordercolor=self.GH["border"],
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", self.GH["hover"])])

        style.configure("TNotebook", background=self.GH["card"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Arial", 9, "bold"), padding=[10, 5])
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.GH["blue"]), ("!selected", self.GH["subtle"])],
            foreground=[("selected", "#FFFFFF"), ("!selected", self.GH["muted"])],
        )

        style.configure(
            "TCombobox",
            fieldbackground=self.GH["canvas"],
            background=self.GH["subtle"],
            foreground=self.GH["text"],
            arrowcolor=self.GH["muted"],
            bordercolor=self.GH["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.GH["canvas"])],
            foreground=[("readonly", self.GH["text"])],
        )

        style.configure(
            "Vertical.TScrollbar",
            background="#484F58",
            troughcolor="#0D1117",
            bordercolor="#30363D",
            arrowcolor="#E6EDF3",
            width=12,
        )
        style.map(
                "Vertical.TScrollbar",
                background=[("active", "#6E7681"), ("pressed", "#8B949E")],
            )

    def _build_layout(self):
        G = self.GH
        container = tk.Frame(self.root, bg=G["canvas"], padx=12, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        # ======================================================================
        # TOP INPUT PANEL
        # ======================================================================
        top_frame = tk.Frame(container, bg=G["canvas"])
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Left Card: Simulation Parameters
        param_card = tk.Frame(
            top_frame, bg=G["card"], bd=0,
            highlightbackground=G["border"], highlightthickness=1, padx=12, pady=8
        )
        param_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        tk.Label(
            param_card, text="Simulation Parameters", font=("Arial", 10, "bold"),
            bg=G["card"], fg=G["text"]
        ).pack(anchor="w", pady=(0, 6))

        # Number of processes input
        num_row = tk.Frame(param_card, bg=G["card"])
        num_row.pack(fill=tk.X, pady=2)
        tk.Label(
            num_row, text="Number of Processes:", font=("Arial", 9),
            bg=G["card"], fg=G["muted"]
        ).pack(side=tk.LEFT)
        self.num_proc_var = tk.StringVar(value="4")
        tk.Entry(
            num_row, textvariable=self.num_proc_var, width=5,
            font=("Arial", 9), justify="center", relief="flat",
            bg=G["canvas"], fg=G["text"], insertbackground=G["text"],
            highlightbackground=G["border"], highlightthickness=1
        ).pack(side=tk.LEFT, padx=(6, 4))
        tk.Button(
            num_row, text="Apply", font=("Arial", 8, "bold"),
            bg=G["subtle"], fg=G["blue_link"], activebackground=G["hover"],
            activeforeground=G["text"], relief="flat", padx=7, pady=2,
            highlightbackground=G["border"], highlightthickness=1,
            cursor="hand2", command=self.apply_process_count
        ).pack(side=tk.LEFT)

        # RR Time Quantum input
        tq_row = tk.Frame(param_card, bg=G["card"])
        tq_row.pack(fill=tk.X, pady=5)
        tk.Label(
            tq_row, text="RR Time Quantum (Q):", font=("Arial", 9),
            bg=G["card"], fg=G["muted"]
        ).pack(side=tk.LEFT)
        self.tq_var = tk.StringVar(value="3")
        tk.Entry(
            tq_row, textvariable=self.tq_var, width=5,
            font=("Arial", 9), justify="center", relief="flat",
            bg=G["canvas"], fg=G["text"], insertbackground=G["text"],
            highlightbackground=G["border"], highlightthickness=1
        ).pack(side=tk.LEFT, padx=(6, 0))

        # Focus View Dropdown
        view_row = tk.Frame(param_card, bg=G["card"])
        view_row.pack(fill=tk.X, pady=(3, 5))
        tk.Label(
            view_row, text="Focus View:", font=("Arial", 9),
            bg=G["card"], fg=G["muted"]
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

        # Middle Card: Process Information Table
        proc_card = tk.Frame(
            top_frame, bg=G["card"], bd=0,
            highlightbackground=G["border"], highlightthickness=1, padx=12, pady=8
        )
        proc_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        proc_top = tk.Frame(proc_card, bg=G["card"])
        proc_top.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            proc_top, text="Process Information", font=("Arial", 10, "bold"),
            bg=G["card"], fg=G["text"]
        ).pack(side=tk.LEFT)

        row_btns = tk.Frame(proc_top, bg=G["card"])
        row_btns.pack(side=tk.RIGHT)
        tk.Button(
            row_btns, text="+ Add", font=("Arial", 8, "bold"),
            bg=G["subtle"], fg=G["green_fg"], activebackground=G["hover"],
            activeforeground=G["green_fg"], relief="flat", padx=7, pady=2,
            highlightbackground=G["border"], highlightthickness=1,
            cursor="hand2", command=self.add_process_row
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            row_btns, text="- Remove", font=("Arial", 8, "bold"),
            bg=G["subtle"], fg=G["red_fg"], activebackground=G["hover"],
            activeforeground=G["red_fg"], relief="flat", padx=7, pady=2,
            highlightbackground=G["border"], highlightthickness=1,
            cursor="hand2", command=self.remove_process_row
        ).pack(side=tk.LEFT)

        hdr = tk.Frame(proc_card, bg=G["subtle"], pady=3)
        hdr.pack(fill=tk.X)
        for text, width in [("Process ID", 12), ("Arrival Time", 14), ("Burst Time", 14)]:
            tk.Label(
                hdr, text=text, width=width, font=("Arial", 8, "bold"),
                bg=G["subtle"], fg=G["muted"]
            ).pack(side=tk.LEFT, padx=4)

        scroll_box = tk.Frame(proc_card, bg=G["card"], height=105)
        scroll_box.pack(fill=tk.BOTH, expand=True)
        scroll_box.pack_propagate(False)

        proc_sb = ttk.Scrollbar(scroll_box, orient="vertical")
        self.proc_canvas = tk.Canvas(
            scroll_box, bg=G["card"], highlightthickness=0, yscrollcommand=proc_sb.set
        )
        proc_sb.configure(command=self.proc_canvas.yview)

        # Pack scrollbar FIRST so it never gets squeezed off-screen
        proc_sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        self.proc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.proc_list_frame = tk.Frame(self.proc_canvas, bg=G["card"])
        self.proc_list_frame.bind(
            "<Configure>",
            lambda e: self.proc_canvas.configure(scrollregion=self.proc_canvas.bbox("all"))
        )
        self.proc_canvas.create_window((0, 0), window=self.proc_list_frame, anchor="nw")

        # Enable touchpad/mouse-wheel scrolling anywhere inside Process Information
        proc_card.bind("<Enter>", self._bind_proc_wheel)
        proc_card.bind("<Leave>", self._unbind_proc_wheel)

        # Pack scrollbar FIRST so it always stays visible on the right
        proc_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.proc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.proc_list_frame = tk.Frame(self.proc_canvas, bg=G["card"])
        self.proc_list_frame.bind(
            "<Configure>",
            lambda e: self.proc_canvas.configure(scrollregion=self.proc_canvas.bbox("all"))
        )
        self.proc_canvas.create_window((0, 0), window=self.proc_list_frame, anchor="nw")

        for w in (self.proc_canvas, self.proc_list_frame):
            w.bind("<MouseWheel>", self._on_proc_scroll)
            w.bind("<Button-4>", self._on_proc_scroll)
            w.bind("<Button-5>", self._on_proc_scroll)

        # Right Action Button (GitHub Signature Green)
        action_col = tk.Frame(top_frame, bg=G["canvas"])
        action_col.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(
            action_col,
            text="Run Simulation",
            font=("Arial", 10, "bold"),
            bg=G["green"],
            fg="#FFFFFF",
            activebackground=G["green_hover"],
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
            container, bg=G["card"], bd=0,
            highlightbackground=G["border"], highlightthickness=1
        )
        results_card.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(results_card, bg=G["subtle"], padx=12, pady=6)
        title_bar.pack(fill=tk.X)
        tk.Label(
            title_bar,
            text="Results  •  All Algorithms Simulated (FCFS, SJF, SRTF, Round Robin)",
            font=("Arial", 10, "bold"),
            bg=G["subtle"],
            fg=G["text"],
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(results_card)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 4))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tab_compare = tk.Frame(self.notebook, bg=G["card"])
        self.tab_fcfs = tk.Frame(self.notebook, bg=G["card"])
        self.tab_sjf = tk.Frame(self.notebook, bg=G["card"])
        self.tab_srtf = tk.Frame(self.notebook, bg=G["card"])
        self.tab_rr = tk.Frame(self.notebook, bg=G["card"])

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

        status_banner = tk.Frame(
            results_card, bg=G["green_bg"], pady=6, padx=12,
            highlightbackground=G["green"], highlightthickness=1
        )
        status_banner.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 8))
        self.status_var = tk.StringVar(value="Simulation Completed!")
        tk.Label(
            status_banner,
            textvariable=self.status_var,
            font=("Arial", 9, "bold"),
            bg=G["green_bg"],
            fg=G["green_fg"],
        ).pack()

    # --------------------------------------------------------------------------
    # TAB BUILDERS
    # --------------------------------------------------------------------------

    def _build_comparison_tab(self):
        G = self.GH
        wrapper = tk.Frame(self.tab_compare, bg=G["card"], padx=8, pady=6)
        wrapper.pack(fill=tk.BOTH, expand=True)

        # FULL-WIDTH ALGORITHM COMPARISON TABLE
        top_comp = tk.Frame(wrapper, bg=G["card"])
        top_comp.pack(fill=tk.X, pady=(0, 8))

        self.comp_header_var = tk.StringVar(value="Algorithm Comparison (RR Quantum = 3):")
        tk.Label(
            top_comp, textvariable=self.comp_header_var,
            font=("Arial", 10, "bold"), bg=G["card"], fg=G["text"]
        ).pack(anchor="w", pady=(0, 4))

        cols = ("Algorithm", "Avg CT", "Avg TAT", "Avg WT", "Avg RT")
        self.comp_tree = ttk.Treeview(top_comp, columns=cols, show="headings", height=4)
        for c in cols:
            self.comp_tree.heading(c, text=c)
            self.comp_tree.column(c, width=210 if c == "Algorithm" else 130, anchor="center")
        self.comp_tree.pack(fill=tk.X)

        # BOTTOM SPLIT: GANTT CHARTS (LEFT) + SCROLLABLE SHORT COMPARISON (RIGHT)
        bottom_split = tk.Frame(wrapper, bg=G["card"])
        bottom_split.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(bottom_split, bg=G["card"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            left_col, text="Gantt Charts / Timelines per Algorithm:",
            font=("Arial", 9, "bold"), bg=G["card"], fg=G["text"]
        ).pack(anchor="w", pady=(0, 4))

        self.overview_gantts = {}
        for key, label in [
            ("FCFS", "1. FCFS"),
            ("SJF", "2. SJF (Non-Preemptive)"),
            ("SRTF", "3. SRTF (Preemptive)"),
            ("RR", "4. Round Robin"),
        ]:
            row = tk.Frame(
                left_col, bg=G["canvas"], bd=0,
                highlightbackground=G["border"], highlightthickness=1, padx=6, pady=2
            )
            row.pack(fill=tk.X, pady=2)

            lbl_var = tk.StringVar(value=label)
            tk.Label(
                row, textvariable=lbl_var, width=20, anchor="w",
                font=("Arial", 8, "bold"), bg=G["canvas"], fg=G["text_body"]
            ).pack(side=tk.LEFT)

            cv = tk.Canvas(row, height=38, bg=G["canvas"], highlightthickness=0)
            cv.pack(side=tk.LEFT, fill=tk.X, expand=True)
            cv.bind("<Configure>", lambda e, k=key: self._redraw_overview_gantt(k))
            self.overview_gantts[key] = {"canvas": cv, "label_var": lbl_var}

        right_col = tk.Frame(bottom_split, bg=G["card"])
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_col, text="Short Comparison:",
            font=("Arial", 9, "bold"), bg=G["card"], fg=G["text"]
        ).pack(anchor="w", pady=(0, 4))

        text_frame = tk.Frame(right_col, bg=G["card"])
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical")
        self.comp_text = tk.Text(
            text_frame, height=8, wrap="word", font=("Arial", 9),
            bg=G["canvas"], fg=G["text_body"], relief="flat", padx=8, pady=6,
            highlightbackground=G["border"], highlightthickness=1,
            yscrollcommand=text_scroll.set
        )
        text_scroll.configure(command=self.comp_text.yview)

        self.comp_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.comp_text.configure(state="disabled")

    def _build_single_algo_tab(self, parent, algo_key, is_rr=False):
        G = self.GH
        wrapper = tk.Frame(parent, bg=G["card"], padx=8, pady=6)
        wrapper.pack(fill=tk.BOTH, expand=True)

        header_var = tk.StringVar(value=f"{algo_key} Simulation Results")
        tk.Label(
            wrapper, textvariable=header_var, font=("Arial", 10, "bold"),
            bg=G["card"], fg=G["text"]
        ).pack(anchor="w", pady=(0, 4))

        gantt_box = tk.Frame(
            wrapper, bg=G["canvas"],
            highlightbackground=G["border"], highlightthickness=1, padx=6, pady=4
        )
        gantt_box.pack(fill=tk.X, pady=(0, 6))

        cv = tk.Canvas(gantt_box, height=58, bg=G["canvas"], highlightthickness=0)
        cv.pack(fill=tk.X, expand=True)
        cv.bind("<Configure>", lambda e, k=algo_key: self._redraw_single_gantt(k))

        cols = ("Process ID", "Arrival Time", "Burst Time", "Completion (CT)", "Turnaround (TAT)", "Waiting (WT)", "Response (RT)")
        tree = ttk.Treeview(wrapper, columns=cols, show="headings", height=5 if is_rr else 7)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=105, anchor="center")
        tree.pack(fill=tk.X, pady=(0, 5))

        avg_var = tk.StringVar(value="Averages -> CT: 0.00 | TAT: 0.00 | WT: 0.00 | RT: 0.00")
        tk.Label(
            wrapper, textvariable=avg_var, font=("Arial", 9, "bold"),
            bg=G["subtle"], fg=G["blue_link"], padx=8, pady=4
        ).pack(fill=tk.X, pady=(0, 5))

        trace_tree = None
        if is_rr:
            tk.Label(
                wrapper, text="Round Robin Quantum Execution Trace:",
                font=("Arial", 9, "bold"), bg=G["card"], fg=G["text"]
            ).pack(anchor="w", pady=(2, 2))

            trace_frame = tk.Frame(wrapper, bg=G["card"])
            trace_frame.pack(fill=tk.BOTH, expand=True)

            trace_scroll = ttk.Scrollbar(trace_frame, orient="vertical")
            tcols = ("Step", "Time Interval", "Process", "Prev BT", "Quantum Used", "Remaining BT", "Status")
            trace_tree = ttk.Treeview(
                trace_frame,
                columns=tcols,
                show="headings",
                height=5,
                yscrollcommand=trace_scroll.set,
            )
            trace_scroll.configure(command=trace_tree.yview)

            for c in tcols:
                trace_tree.heading(c, text=c)
                trace_tree.column(c, width=125 if c == "Status" else 96, anchor="center")

            trace_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            trace_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        return {
            "header_var": header_var,
            "canvas": cv,
            "tree": tree,
            "avg_var": avg_var,
            "trace_tree": trace_tree,
        }

        return {
            "header_var": header_var,
            "canvas": cv,
            "tree": tree,
            "avg_var": avg_var,
            "trace_tree": trace_tree,
        }

    # --------------------------------------------------------------------------
    # PROCESS INPUT MANAGEMENT
    # --------------------------------------------------------------------------

    def _bind_proc_wheel(self, event=None):
        self.proc_canvas.bind_all("<MouseWheel>", self._on_proc_scroll)
        self.proc_canvas.bind_all("<Button-4>", self._on_proc_scroll)
        self.proc_canvas.bind_all("<Button-5>", self._on_proc_scroll)

    def _unbind_proc_wheel(self, event=None):
        self.proc_canvas.unbind_all("<MouseWheel>")
        self.proc_canvas.unbind_all("<Button-4>")
        self.proc_canvas.unbind_all("<Button-5>")

    def _on_proc_scroll(self, event):
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.proc_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self.proc_canvas.yview_scroll(1, "units")

    def clear_process_rows(self):
        for r in self.process_rows:
            r["frame"].destroy()
        self.process_rows.clear()

    def add_process_row(self, pid=None, at="0", bt="1"):
        G = self.GH
        idx = len(self.process_rows) + 1
        if pid is None:
            pid = f"P{idx}"

        row_frame = tk.Frame(self.proc_list_frame, bg=G["card"], pady=2)
        row_frame.pack(fill=tk.X)

        pid_var = tk.StringVar(value=str(pid))
        at_var = tk.StringVar(value=str(at))
        bt_var = tk.StringVar(value=str(bt))

        for var, width in [(pid_var, 11), (at_var, 13), (bt_var, 13)]:
            tk.Entry(
                row_frame, textvariable=var, width=width,
                font=("Arial", 9), justify="center", relief="flat",
                bg=G["canvas"], fg=G["text"], insertbackground=G["text"],
                highlightbackground=G["border"], highlightthickness=1
            ).pack(side=tk.LEFT, padx=4)

        self.process_rows.append({
            "frame": row_frame,
            "pid_var": pid_var,
            "at_var": at_var,
            "bt_var": bt_var,
        })
        self.num_proc_var.set(str(len(self.process_rows)))

        # Auto-scroll down so newly added rows (P5, P6, ...) are immediately visible
        self.proc_canvas.update_idletasks()
        self.proc_canvas.configure(scrollregion=self.proc_canvas.bbox("all"))
        self.proc_canvas.yview_moveto(1.0)

    def remove_process_row(self):
        if len(self.process_rows) <= 1:
            messagebox.showwarning("Minimum Process", "At least 1 process is required.")
            return
        last = self.process_rows.pop()
        last["frame"].destroy()
        self.num_proc_var.set(str(len(self.process_rows)))

    def apply_process_count(self):
        try:
            target = int(self.num_proc_var.get().strip())
            if target < 1 or target > 20:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Count", "Enter an integer between 1 and 20.")
            return

        while len(self.process_rows) < target:
            self.add_process_row(at=str(len(self.process_rows)), bt="4")
        while len(self.process_rows) > target:
            last = self.process_rows.pop()
            last["frame"].destroy()

    def load_rr_sample(self):
        self.clear_process_rows()
        self.tq_var.set("3")
        samples = [("P1", "0", "8"), ("P2", "1", "4"), ("P3", "2", "9"), ("P4", "3", "5")]
        for pid, at, bt in samples:
            self.add_process_row(pid, at, bt)
        self.run_all_simulations()

    def load_fcfs_sample(self):
        self.clear_process_rows()
        self.tq_var.set("2")
        samples = [("P1", "0", "5"), ("P2", "1", "3"), ("P3", "2", "8"), ("P4", "3", "6")]
        for pid, at, bt in samples:
            self.add_process_row(pid, at, bt)
        self.run_all_simulations()

    # --------------------------------------------------------------------------
    # TAB & DROPDOWN SYNC
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
        reverse_map = {
            0: "All Algorithms (Compare)",
            1: "FCFS",
            2: "SJF (Non-Preemptive)",
            3: "SRTF (Preemptive)",
            4: "Round Robin (RR)",
        }
        idx = self.notebook.index(self.notebook.select())
        if idx in reverse_map:
            self.view_var.set(reverse_map[idx])

    # --------------------------------------------------------------------------
    # SIMULATION & RENDERING
    # --------------------------------------------------------------------------

    def run_all_simulations(self):
        try:
            quantum = int(self.tq_var.get().strip())
            if quantum <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantum", "Time Quantum (Q) must be a positive integer.")
            return

        processes = []
        seen_pids = set()
        for idx, row in enumerate(self.process_rows):
            pid = row["pid_var"].get().strip()
            if not pid or pid in seen_pids:
                messagebox.showerror("Invalid Process ID", f"Duplicate or empty Process ID at row {idx + 1}.")
                return
            seen_pids.add(pid)
            try:
                at = int(row["at_var"].get().strip())
                bt = int(row["bt_var"].get().strip())
                if at < 0 or bt <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", f"Check Arrival Time (>=0) and Burst Time (>0) for {pid}.")
                return
            processes.append({"index": idx, "pid": pid, "at": at, "bt": bt})

        self.pid_color_map = {
            p["pid"]: self.PALETTE[i % len(self.PALETTE)]
            for i, p in enumerate(processes)
        }

        self.results_cache = {
            "FCFS": schedule_fcfs(processes),
            "SJF": schedule_sjf(processes),
            "SRTF": schedule_srtf(processes),
            "RR": schedule_round_robin(processes, quantum),
        }

        self._populate_comparison_tab(len(processes), quantum)
        for key in ["FCFS", "SJF", "SRTF", "RR"]:
            self._populate_single_algo_tab(key)

        self.status_var.set(
            f"Simulation Completed! (All 4 Algorithms Simulated with RR Q={quantum} for {len(processes)} Processes)"
        )

    def _populate_comparison_tab(self, count, quantum):
        self.comp_header_var.set(f"Algorithm Comparison (Processes = {count}, RR Quantum = {quantum}):")
        self.overview_gantts["RR"]["label_var"].set(f"4. Round Robin (Q={quantum})")

        for item in self.comp_tree.get_children():
            self.comp_tree.delete(item)

        for key in ["FCFS", "SJF", "SRTF", "RR"]:
            res = self.results_cache[key]
            avgs = res["avgs"]
            self.comp_tree.insert(
                "", "end",
                values=(
                    res["name"],
                    f"{avgs['ct']:.2f}",
                    f"{avgs['tat']:.2f}",
                    f"{avgs['wt']:.2f}",
                    f"{avgs['rt']:.2f}",
                )
            )
            self._redraw_overview_gantt(key)

        summary = generate_short_comparison(self.results_cache, quantum)
        self.comp_text.configure(state="normal")
        self.comp_text.delete("1.0", tk.END)
        self.comp_text.insert("1.0", summary)
        self.comp_text.configure(state="disabled")

    def _populate_single_algo_tab(self, key):
        w = self.algo_widgets[key]
        res = self.results_cache[key]
        w["header_var"].set(f"{res['name']} — Detailed Gantt Chart & Process Metrics")

        for item in w["tree"].get_children():
            w["tree"].delete(item)

        for r in res["rows"]:
            w["tree"].insert(
                "", "end",
                values=(r["pid"], r["at"], r["bt"], r["ct"], r["tat"], r["wt"], r["rt"])
            )

        avgs = res["avgs"]
        w["avg_var"].set(
            f"Averages  ->  CT: {avgs['ct']:.2f}   |   TAT: {avgs['tat']:.2f}   |   WT: {avgs['wt']:.2f}   |   RT: {avgs['rt']:.2f}"
        )

        if key == "RR" and w["trace_tree"] is not None:
            for item in w["trace_tree"].get_children():
                w["trace_tree"].delete(item)
            for step in res["trace"]:
                w["trace_tree"].insert(
                    "", "end",
                    values=(
                        step["step"], step["interval"], step["pid"],
                        step["prev_bt"], step["used"], step["rem_bt"], step["status"]
                    )
                )

        self._redraw_single_gantt(key)

    def _redraw_overview_gantt(self, key):
        if key not in self.results_cache:
            return
        cv = self.overview_gantts[key]["canvas"]
        self._draw_gantt_blocks(cv, self.results_cache[key]["gantt"], compact=True)

    def _redraw_single_gantt(self, key):
        if key not in self.results_cache:
            return
        cv = self.algo_widgets[key]["canvas"]
        self._draw_gantt_blocks(cv, self.results_cache[key]["gantt"], compact=False)

    def _draw_gantt_blocks(self, canvas, gantt, compact=True):
        G = self.GH
        canvas.delete("all")
        if not gantt:
            return

        w = max(canvas.winfo_width(), 320)
        h = max(canvas.winfo_height(), 38 if compact else 56)
        pad_x = 10
        top_y = 4 if compact else 8
        bot_y = h - (14 if compact else 18)

        start_t = gantt[0][1]
        end_t = gantt[-1][2]
        total = max(end_t - start_t, 1)
        usable_w = w - 2 * pad_x

        for pid, s, e in gantt:
            x1 = pad_x + ((s - start_t) / total) * usable_w
            x2 = pad_x + ((e - start_t) / total) * usable_w
            fill = G["subtle"] if pid == "IDLE" else self.pid_color_map.get(pid, G["blue_link"])
            txt_fg = G["muted"] if pid == "IDLE" else "#0D1117"

            canvas.create_rectangle(x1, top_y, x2, bot_y, fill=fill, outline=G["canvas"], width=1)
            if (x2 - x1) >= 18:
                canvas.create_text(
                    (x1 + x2) / 2, (top_y + bot_y) / 2,
                    text=pid, fill=txt_fg, font=("Arial", 8 if compact else 9, "bold")
                )
            canvas.create_text(
                x1, bot_y + 7, text=str(s), fill=G["muted"], font=("Arial", 7 if compact else 8)
            )

        canvas.create_text(
            pad_x + usable_w, bot_y + 7, text=str(end_t),
            fill=G["muted"], font=("Arial", 7 if compact else 8)
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSchedulerApp(root)
    root.mainloop()