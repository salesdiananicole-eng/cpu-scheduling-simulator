import tkinter as tk
from tkinter import ttk, messagebox

from theme import GH, PALETTE, configure_styles
from algorithms import (
    schedule_fcfs,
    schedule_sjf,
    schedule_srtf,
    schedule_round_robin,
    generate_short_comparison,
)


class CPUSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Topic 1: CPU Scheduling Simulator (FCFS, SJF, SRTF, Round Robin)")
        self.root.geometry("880x690+25+10")
        self.root.minsize(680, 520)
        self.root.configure(bg=GH["canvas"])

        self.process_rows = []
        self.results_cache = {}
        self.pid_color_map = {}

        configure_styles()
        self._build_layout()
        self.load_rr_sample()

    def _build_layout(self):
        container = tk.Frame(self.root, bg=GH["canvas"], padx=12, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        # ======================================================================
        # TOP INPUT PANEL
        # ======================================================================
        top_frame = tk.Frame(container, bg=GH["canvas"])
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Left Card: Simulation Parameters
        param_card = tk.Frame(
            top_frame, bg=GH["card"], bd=0,
            highlightbackground=GH["border"], highlightthickness=1, padx=12, pady=8
        )
        param_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        tk.Label(
            param_card, text="Simulation Parameters", font=("Arial", 10, "bold"),
            bg=GH["card"], fg=GH["text"]
        ).pack(anchor="w", pady=(0, 6))

        num_row = tk.Frame(param_card, bg=GH["card"])
        num_row.pack(fill=tk.X, pady=2)
        tk.Label(
            num_row, text="Number of Processes:", font=("Arial", 9),
            bg=GH["card"], fg=GH["muted"]
        ).pack(side=tk.LEFT)
        self.num_proc_var = tk.StringVar(value="4")
        tk.Entry(
            num_row, textvariable=self.num_proc_var, width=5,
            font=("Arial", 9), justify="center", relief="flat",
            bg=GH["canvas"], fg=GH["text"], insertbackground=GH["text"],
            highlightbackground=GH["border"], highlightthickness=1
        ).pack(side=tk.LEFT, padx=(6, 4))
        tk.Button(
            num_row, text="Apply", font=("Arial", 8, "bold"),
            bg=GH["subtle"], fg=GH["blue_link"], activebackground=GH["hover"],
            activeforeground=GH["text"], relief="flat", padx=7, pady=2,
            highlightbackground=GH["border"], highlightthickness=1,
            cursor="hand2", command=self.apply_process_count
        ).pack(side=tk.LEFT)

        tq_row = tk.Frame(param_card, bg=GH["card"])
        tq_row.pack(fill=tk.X, pady=5)
        tk.Label(
            tq_row, text="RR Time Quantum (Q):", font=("Arial", 9),
            bg=GH["card"], fg=GH["muted"]
        ).pack(side=tk.LEFT)
        self.tq_var = tk.StringVar(value="3")
        tk.Entry(
            tq_row, textvariable=self.tq_var, width=5,
            font=("Arial", 9), justify="center", relief="flat",
            bg=GH["canvas"], fg=GH["text"], insertbackground=GH["text"],
            highlightbackground=GH["border"], highlightthickness=1
        ).pack(side=tk.LEFT, padx=(6, 0))

        view_row = tk.Frame(param_card, bg=GH["card"])
        view_row.pack(fill=tk.X, pady=(3, 5))
        tk.Label(
            view_row, text="Focus View:", font=("Arial", 9),
            bg=GH["card"], fg=GH["muted"]
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
            top_frame, bg=GH["card"], bd=0,
            highlightbackground=GH["border"], highlightthickness=1, padx=12, pady=8
        )
        proc_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        proc_top = tk.Frame(proc_card, bg=GH["card"])
        proc_top.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            proc_top, text="Process Information", font=("Arial", 10, "bold"),
            bg=GH["card"], fg=GH["text"]
        ).pack(side=tk.LEFT)

        row_btns = tk.Frame(proc_top, bg=GH["card"])
        row_btns.pack(side=tk.RIGHT)
        tk.Button(
            row_btns, text="+ Add", font=("Arial", 8, "bold"),
            bg=GH["subtle"], fg=GH["green_fg"], activebackground=GH["hover"],
            activeforeground=GH["green_fg"], relief="flat", padx=7, pady=2,
            highlightbackground=GH["border"], highlightthickness=1,
            cursor="hand2", command=self.add_process_row
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            row_btns, text="- Remove", font=("Arial", 8, "bold"),
            bg=GH["subtle"], fg=GH["red_fg"], activebackground=GH["hover"],
            activeforeground=GH["red_fg"], relief="flat", padx=7, pady=2,
            highlightbackground=GH["border"], highlightthickness=1,
            cursor="hand2", command=self.remove_process_row
        ).pack(side=tk.LEFT)

        hdr = tk.Frame(proc_card, bg=GH["subtle"], pady=3)
        hdr.pack(fill=tk.X)
        for text, width in [("Process ID", 12), ("Arrival Time", 14), ("Burst Time", 14)]:
            tk.Label(
                hdr, text=text, width=width, font=("Arial", 8, "bold"),
                bg=GH["subtle"], fg=GH["muted"]
            ).pack(side=tk.LEFT, padx=4)

        scroll_box = tk.Frame(proc_card, bg=GH["card"], height=105)
        scroll_box.pack(fill=tk.BOTH, expand=True)
        scroll_box.pack_propagate(False)

        proc_sb = ttk.Scrollbar(scroll_box, orient="vertical")
        self.proc_canvas = tk.Canvas(
            scroll_box, bg=GH["card"], highlightthickness=0, yscrollcommand=proc_sb.set
        )
        proc_sb.configure(command=self.proc_canvas.yview)

        proc_sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        self.proc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.proc_list_frame = tk.Frame(self.proc_canvas, bg=GH["card"])
        self.proc_list_frame.bind(
            "<Configure>",
            lambda e: self.proc_canvas.configure(scrollregion=self.proc_canvas.bbox("all"))
        )
        self.proc_canvas.create_window((0, 0), window=self.proc_list_frame, anchor="nw")

        proc_card.bind("<Enter>", self._bind_proc_wheel)
        proc_card.bind("<Leave>", self._unbind_proc_wheel)

        # Right Action Button
        action_col = tk.Frame(top_frame, bg=GH["canvas"])
        action_col.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(
            action_col,
            text="Run Simulation",
            font=("Arial", 10, "bold"),
            bg=GH["green"],
            fg="#FFFFFF",
            activebackground=GH["green_hover"],
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
            container, bg=GH["card"], bd=0,
            highlightbackground=GH["border"], highlightthickness=1
        )
        results_card.pack(fill=tk.BOTH, expand=True)

        title_bar = tk.Frame(results_card, bg=GH["subtle"], padx=12, pady=6)
        title_bar.pack(fill=tk.X)
        tk.Label(
            title_bar,
            text="Results  •  All Algorithms Simulated (FCFS, SJF, SRTF, Round Robin)",
            font=("Arial", 10, "bold"),
            bg=GH["subtle"],
            fg=GH["text"],
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(results_card)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 4))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tab_compare = tk.Frame(self.notebook, bg=GH["card"])
        self.tab_fcfs = tk.Frame(self.notebook, bg=GH["card"])
        self.tab_sjf = tk.Frame(self.notebook, bg=GH["card"])
        self.tab_srtf = tk.Frame(self.notebook, bg=GH["card"])
        self.tab_rr = tk.Frame(self.notebook, bg=GH["card"])

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
            results_card, bg=GH["green_bg"], pady=6, padx=12,
            highlightbackground=GH["green"], highlightthickness=1
        )
        status_banner.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 8))
        self.status_var = tk.StringVar(value="Simulation Completed!")
        tk.Label(
            status_banner,
            textvariable=self.status_var,
            font=("Arial", 9, "bold"),
            bg=GH["green_bg"],
            fg=GH["green_fg"],
        ).pack()

    # --------------------------------------------------------------------------
    # TAB BUILDERS
    # --------------------------------------------------------------------------

    def _build_comparison_tab(self):
        wrapper = tk.Frame(self.tab_compare, bg=GH["card"], padx=8, pady=6)
        wrapper.pack(fill=tk.BOTH, expand=True)

        top_comp = tk.Frame(wrapper, bg=GH["card"])
        top_comp.pack(fill=tk.X, pady=(0, 8))

        self.comp_header_var = tk.StringVar(value="Algorithm Comparison")
        tk.Label(
            top_comp, textvariable=self.comp_header_var,
            font=("Arial", 10, "bold"), bg=GH["card"], fg=GH["text"]
        ).pack(anchor="w", pady=(0, 4))

        cols = ("Algorithm", "Avg CT", "Avg TAT", "Avg WT", "Avg RT")
        self.comp_tree = ttk.Treeview(top_comp, columns=cols, show="headings", height=4)
        for c in cols:
            self.comp_tree.heading(c, text=c)
            self.comp_tree.column(c, width=210 if c == "Algorithm" else 130, anchor="center")
        self.comp_tree.pack(fill=tk.X)

        bottom_split = tk.Frame(wrapper, bg=GH["card"])
        bottom_split.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(bottom_split, bg=GH["card"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            left_col, text="Gantt Charts / Timelines per Algorithm:",
            font=("Arial", 9, "bold"), bg=GH["card"], fg=GH["text"]
        ).pack(anchor="w", pady=(0, 4))

        self.overview_gantts = {}
        for key, label in [
            ("FCFS", "1. FCFS"),
            ("SJF", "2. SJF (Non-Preemptive)"),
            ("SRTF", "3. SRTF (Preemptive)"),
            ("RR", "4. Round Robin"),
        ]:
            row = tk.Frame(
                left_col, bg=GH["canvas"], bd=0,
                highlightbackground=GH["border"], highlightthickness=1, padx=6, pady=2
            )
            row.pack(fill=tk.X, pady=2)

            lbl_var = tk.StringVar(value=label)
            tk.Label(
                row, textvariable=lbl_var, width=20, anchor="w",
                font=("Arial", 8, "bold"), bg=GH["canvas"], fg=GH["text_body"]
            ).pack(side=tk.LEFT)

            cv = tk.Canvas(row, height=38, bg=GH["canvas"], highlightthickness=0)
            cv.pack(side=tk.LEFT, fill=tk.X, expand=True)
            cv.bind("<Configure>", lambda e, k=key: self._redraw_overview_gantt(k))
            self.overview_gantts[key] = {"canvas": cv, "label_var": lbl_var}

        right_col = tk.Frame(bottom_split, bg=GH["card"])
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_col, text="Short Comparison:",
            font=("Arial", 9, "bold"), bg=GH["card"], fg=GH["text"]
        ).pack(anchor="w", pady=(0, 4))

        text_frame = tk.Frame(right_col, bg=GH["card"])
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical")
        self.comp_text = tk.Text(
            text_frame, height=8, wrap="word", font=("Arial", 9),
            bg=GH["canvas"], fg=GH["text_body"], relief="flat", padx=8, pady=6,
            highlightbackground=GH["border"], highlightthickness=1,
            yscrollcommand=text_scroll.set
        )
        text_scroll.configure(command=self.comp_text.yview)

        self.comp_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.comp_text.configure(state="disabled")

    def _build_single_algo_tab(self, parent, algo_key, is_rr=False):
        wrapper = tk.Frame(parent, bg=GH["card"], padx=8, pady=6)
        wrapper.pack(fill=tk.BOTH, expand=True)

        header_var = tk.StringVar(value=f"{algo_key} Simulation Results")
        tk.Label(
            wrapper, textvariable=header_var, font=("Arial", 10, "bold"),
            bg=GH["card"], fg=GH["text"]
        ).pack(anchor="w", pady=(0, 4))

        gantt_box = tk.Frame(
            wrapper, bg=GH["canvas"],
            highlightbackground=GH["border"], highlightthickness=1, padx=6, pady=4
        )
        gantt_box.pack(fill=tk.X, pady=(0, 6))

        cv = tk.Canvas(gantt_box, height=58, bg=GH["canvas"], highlightthickness=0)
        cv.pack(fill=tk.X, expand=True)
        cv.bind("<Configure>", lambda e, k=algo_key: self._redraw_single_gantt(k))

        tree_frame = tk.Frame(wrapper, bg=GH["card"])
        tree_frame.pack(fill=tk.X, pady=(0, 5))

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        cols = ("Process ID", "Arrival Time", "Burst Time", "Completion (CT)", "Turnaround (TAT)", "Waiting (WT)", "Response (RT)")
        tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=5 if is_rr else 7,
            yscrollcommand=tree_scroll.set,
        )
        tree_scroll.configure(command=tree.yview)

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=102, anchor="center")

        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        avg_var = tk.StringVar(value="Averages -> CT: 0.00 | TAT: 0.00 | WT: 0.00 | RT: 0.00")
        tk.Label(
            wrapper, textvariable=avg_var, font=("Arial", 9, "bold"),
            bg=GH["subtle"], fg=GH["blue_link"], padx=8, pady=4
        ).pack(fill=tk.X, pady=(0, 5))

        trace_tree = None
        if is_rr:
            tk.Label(
                wrapper, text="Round Robin Quantum Execution Trace:",
                font=("Arial", 9, "bold"), bg=GH["card"], fg=GH["text"]
            ).pack(anchor="w", pady=(2, 2))

            trace_frame = tk.Frame(wrapper, bg=GH["card"])
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
        idx = len(self.process_rows) + 1
        if pid is None:
            pid = f"P{idx}"

        row_frame = tk.Frame(self.proc_list_frame, bg=GH["card"], pady=2)
        row_frame.pack(fill=tk.X)

        pid_var = tk.StringVar(value=str(pid))
        at_var = tk.StringVar(value=str(at))
        bt_var = tk.StringVar(value=str(bt))

        for var, width in [(pid_var, 11), (at_var, 13), (bt_var, 13)]:
            tk.Entry(
                row_frame, textvariable=var, width=width,
                font=("Arial", 9), justify="center", relief="flat",
                bg=GH["canvas"], fg=GH["text"], insertbackground=GH["text"],
                highlightbackground=GH["border"], highlightthickness=1
            ).pack(side=tk.LEFT, padx=4)

        self.process_rows.append({
            "frame": row_frame,
            "pid_var": pid_var,
            "at_var": at_var,
            "bt_var": bt_var,
        })
        self.num_proc_var.set(str(len(self.process_rows)))

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
            p["pid"]: PALETTE[i % len(PALETTE)]
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
        self.comp_header_var.set(f"Algorithm Comparison")
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
            fill = GH["subtle"] if pid == "IDLE" else self.pid_color_map.get(pid, GH["blue_link"])
            txt_fg = GH["muted"] if pid == "IDLE" else "#0D1117"

            canvas.create_rectangle(x1, top_y, x2, bot_y, fill=fill, outline=GH["canvas"], width=1)
            if (x2 - x1) >= 18:
                canvas.create_text(
                    (x1 + x2) / 2, (top_y + bot_y) / 2,
                    text=pid, fill=txt_fg, font=("Arial", 8 if compact else 9, "bold")
                )
            canvas.create_text(
                x1, bot_y + 7, text=str(s), fill=GH["muted"], font=("Arial", 7 if compact else 8)
            )

        canvas.create_text(
            pad_x + usable_w, bot_y + 7, text=str(end_t),
            fill=GH["muted"], font=("Arial", 7 if compact else 8)
        )