from tkinter import ttk

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


def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=GH["card"],
        fieldbackground=GH["card"],
        foreground=GH["text_body"],
        bordercolor=GH["border"],
        lightcolor=GH["border"],
        darkcolor=GH["border"],
        rowheight=24,
        font=("Arial", 9),
    )
    style.map(
        "Treeview",
        background=[("selected", GH["blue"])],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure(
        "Treeview.Heading",
        font=("Arial", 9, "bold"),
        background=GH["subtle"],
        foreground=GH["text"],
        bordercolor=GH["border"],
        relief="flat",
    )
    style.map("Treeview.Heading", background=[("active", GH["hover"])])

    style.configure("TNotebook", background=GH["card"], borderwidth=0)
    style.configure("TNotebook.Tab", font=("Arial", 9, "bold"), padding=[10, 5])
    style.map(
        "TNotebook.Tab",
        background=[("selected", GH["blue"]), ("!selected", GH["subtle"])],
        foreground=[("selected", "#FFFFFF"), ("!selected", GH["muted"])],
    )

    style.configure(
        "TCombobox",
        fieldbackground=GH["canvas"],
        background=GH["subtle"],
        foreground=GH["text"],
        arrowcolor=GH["muted"],
        bordercolor=GH["border"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", GH["canvas"])],
        foreground=[("readonly", GH["text"])],
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