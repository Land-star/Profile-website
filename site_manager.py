#!/usr/bin/env python3
"""
KIERAN Site Manager v2
- Create / Edit / Delete projects (auto-manages templates + cards + prev/next links)
- Edit all profile links (LinkedIn, GitHub, TryHackMe, HTB, Email)
- Edit hero, about, certs, nav, footer
- Surgical string.replace() — never rewrites files from scratch

Put this in your website folder and run:  python site_manager.py
Requires: Python 3 with tkinter (built-in, no pip installs needed)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os, re, shutil, glob
from datetime import datetime

TYPE_MAP = {
    "Home Lab": "lab",
    "CTF / Challenge": "ctf",
    "Article / Thought Piece": "article",
    "Research": "research",
}
TYPE_OPTIONS = list(TYPE_MAP.keys())
CLASS_TO_TYPE = {v: k for k, v in TYPE_MAP.items()}


class SiteManager:
    def __init__(self, root):
        self.root = root
        self.root.title("KIERAN // Site Manager v2")
        self.root.geometry("1020x760")
        self.root.configure(bg="#0a0e17")
        self.site_dir = None
        self.files = {}
        self._styles()
        self._build_header()
        self._build_picker()

    # ────────────────────── SETUP ──────────────────────

    def _styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook", background="#0a0e17", borderwidth=0)
        s.configure("TNotebook.Tab", background="#111927", foreground="#00f5ff",
                     padding=[14, 6], font=("Consolas", 9, "bold"))
        s.map("TNotebook.Tab", background=[("selected", "#1a2740")],
              foreground=[("selected", "#00f5ff")])

    def _build_header(self):
        h = tk.Frame(self.root, bg="#070d18", height=48)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="KIERAN // SITE MANAGER", bg="#070d18", fg="#00f5ff",
                 font=("Consolas", 14, "bold")).pack(side="left", padx=16)
        tk.Label(h, text="v2 — Projects + Links + Content", bg="#070d18",
                 fg="#334455", font=("Consolas", 9)).pack(side="left", padx=8)

    def _build_picker(self):
        self.picker = tk.Frame(self.root, bg="#0a0e17")
        self.picker.pack(expand=True, fill="both")
        tk.Label(self.picker, text="SELECT YOUR WEBSITE FOLDER", bg="#0a0e17",
                 fg="#00f5ff", font=("Consolas", 16, "bold")).pack(pady=(80, 10))
        tk.Button(self.picker, text="Choose Folder", bg="#00f5ff", fg="#020409",
                  font=("Consolas", 12, "bold"), relief="flat", padx=20, pady=10,
                  command=self._pick_folder, cursor="hand2").pack(pady=10)
        cwd = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(cwd, "index.html")):
            tk.Button(self.picker, text=f"Use current folder: {os.path.basename(cwd)}",
                      bg="#1a2740", fg="#00f5ff", font=("Consolas", 9), relief="flat",
                      padx=12, pady=6, command=lambda: self._load(cwd),
                      cursor="hand2").pack(pady=8)

    def _pick_folder(self):
        f = filedialog.askdirectory(title="Select website folder")
        if f: self._load(f)

    def _load(self, folder):
        self.site_dir = folder
        self.files = {}
        for fp in glob.glob(os.path.join(folder, "*.html")):
            with open(fp, "r", encoding="utf-8") as fh:
                self.files[os.path.basename(fp)] = fh.read()
        if "index.html" not in self.files:
            messagebox.showerror("Error", "index.html not found!"); return
        self.picker.destroy()
        self._build_editor()

    # ────────────────────── WIDGETS ──────────────────────

    def _scroll(self, parent):
        c = tk.Canvas(parent, bg="#0a0e17", highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=c.yview)
        f = tk.Frame(c, bg="#0a0e17")
        f.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        cw = c.create_window((0, 0), window=f, anchor="nw")
        c.configure(yscrollcommand=sb.set)
        c.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        # Make frame fill canvas width
        def _resize(e): c.itemconfig(cw, width=e.width)
        c.bind("<Configure>", _resize)
        # Mousewheel
        def _wheel(e): c.yview_scroll(int(-1*(e.delta/120)), "units")
        f.bind("<Enter>", lambda e: c.bind_all("<MouseWheel>", _wheel))
        f.bind("<Leave>", lambda e: c.unbind_all("<MouseWheel>"))
        return f

    def _field(self, parent, label, default="", multi=False):
        fr = tk.Frame(parent, bg="#0a0e17")
        fr.pack(fill="x", padx=12, pady=4)
        tk.Label(fr, text=label.upper(), bg="#0a0e17", fg="#00f5ff",
                 font=("Consolas", 8, "bold")).pack(anchor="w")
        if multi:
            w = scrolledtext.ScrolledText(fr, width=70, height=4, bg="#111927",
                fg="#c8e0f0", insertbackground="#00f5ff", font=("Consolas", 10),
                relief="flat", borderwidth=2, wrap="word")
            w.insert("1.0", default)
        else:
            w = tk.Entry(fr, width=70, bg="#111927", fg="#c8e0f0",
                insertbackground="#00f5ff", font=("Consolas", 10), relief="flat", borderwidth=2)
            w.insert(0, default)
        w.pack(fill="x", pady=(2, 0))
        return w

    def _dropdown(self, parent, label, options, default=""):
        fr = tk.Frame(parent, bg="#0a0e17")
        fr.pack(fill="x", padx=12, pady=4)
        tk.Label(fr, text=label.upper(), bg="#0a0e17", fg="#00f5ff",
                 font=("Consolas", 8, "bold")).pack(anchor="w")
        var = tk.StringVar(value=default)
        ttk.Combobox(fr, textvariable=var, values=options, state="readonly",
                      font=("Consolas", 10)).pack(fill="x", pady=(2, 0))
        return var

    def _hdr(self, parent, text):
        tk.Label(parent, text=f"── {text} ──", bg="#0a0e17", fg="#00f5ff",
                 font=("Consolas", 11, "bold")).pack(anchor="w", padx=12, pady=(16, 4))

    def _hint(self, parent, text):
        tk.Label(parent, text=text, bg="#0a0e17", fg="#556677",
                 font=("Consolas", 9)).pack(anchor="w", padx=12)

    def _ex(self, html, pat, grp=1, default=""):
        m = re.search(pat, html, re.DOTALL)
        return m.group(grp).strip() if m else default

    def _v(self, w):
        if isinstance(w, scrolledtext.ScrolledText): return w.get("1.0", "end-1c").strip()
        if isinstance(w, tk.StringVar): return w.get().strip()
        return w.get().strip()

    # ────────────────────── MAIN EDITOR ──────────────────────

    def _build_editor(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(expand=True, fill="both", padx=8, pady=(4, 4))
        self._tab_projects()
        self._tab_links()
        self._tab_hero()
        self._tab_about()
        self._tab_certs()
        self._tab_nav()
        self._tab_footer()
        # Bottom bar
        bar = tk.Frame(self.root, bg="#070d18", height=48)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        tk.Label(bar, text=f"  {self.site_dir}", bg="#070d18", fg="#334455",
                 font=("Consolas", 8)).pack(side="left", padx=12)
        tk.Button(bar, text="  SAVE ALL", bg="#00f5ff", fg="#020409",
                  font=("Consolas", 11, "bold"), relief="flat", padx=16, pady=5,
                  command=self._save_all, cursor="hand2").pack(side="right", padx=12, pady=7)
        tk.Button(bar, text="Backup", bg="#1a2740", fg="#00f5ff",
                  font=("Consolas", 9), relief="flat", padx=10, pady=3,
                  command=self._backup, cursor="hand2").pack(side="right", padx=4, pady=7)

    # ═══════════════════════════════════════════════════════
    #  PROJECTS TAB
    # ═══════════════════════════════════════════════════════

    def _tab_projects(self):
        self.proj_tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(self.proj_tab, text=" PROJECTS ")
        self._refresh_projects()

    def _refresh_projects(self):
        for w in self.proj_tab.winfo_children(): w.destroy()
        # Top bar
        top = tk.Frame(self.proj_tab, bg="#070d18")
        top.pack(fill="x")
        tk.Label(top, text="  YOUR PROJECTS", bg="#070d18", fg="#00f5ff",
                 font=("Consolas", 11, "bold")).pack(side="left", padx=12, pady=8)
        tk.Button(top, text="+ NEW PROJECT", bg="#00ff88", fg="#020409",
                  font=("Consolas", 10, "bold"), relief="flat", padx=12, pady=4,
                  command=self._new_project, cursor="hand2").pack(side="right", padx=12, pady=8)
        frame = self._scroll(self.proj_tab)
        # Find project files
        pfiles = sorted(
            [f for f in self.files if re.match(r'^project-\d+\.html$', f)],
            key=lambda x: int(re.search(r'(\d+)', x).group(1)), reverse=True)
        if not pfiles:
            tk.Label(frame, text="No projects yet. Click '+ NEW PROJECT' to create one.",
                     bg="#0a0e17", fg="#556677", font=("Consolas", 11)).pack(pady=60)
            return
        for pf in pfiles:
            html = self.files[pf]
            title = self._ex(html, r'class="project-title">([^<]+)<', default=pf)
            ptype = self._ex(html, r'class="project-type\s+\w+">([^<]+)<', default="?")
            date = self._ex(html, r'class="project-date">([^<]+)<', default="")
            row = tk.Frame(frame, bg="#111927", highlightbackground="#1a2740", highlightthickness=1)
            row.pack(fill="x", padx=12, pady=3)
            info = tk.Frame(row, bg="#111927")
            info.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            tk.Label(info, text=title, bg="#111927", fg="#ffffff",
                     font=("Consolas", 11, "bold")).pack(anchor="w")
            tk.Label(info, text=f"{ptype}  |  {date}  |  {pf}", bg="#111927",
                     fg="#556677", font=("Consolas", 8)).pack(anchor="w")
            btns = tk.Frame(row, bg="#111927")
            btns.pack(side="right", padx=12, pady=8)
            tk.Button(btns, text="Edit", bg="#1a2740", fg="#00f5ff",
                      font=("Consolas", 9, "bold"), relief="flat", padx=10, pady=2,
                      command=lambda f=pf: self._edit_project(f), cursor="hand2").pack(side="left", padx=3)
            tk.Button(btns, text="Delete", bg="#1a2740", fg="#ff2244",
                      font=("Consolas", 9, "bold"), relief="flat", padx=10, pady=2,
                      command=lambda f=pf: self._delete_project(f), cursor="hand2").pack(side="left", padx=3)

    def _next_num(self):
        nums = [int(re.search(r'(\d+)', f).group(1))
                for f in self.files if re.match(r'^project-\d+\.html$', f)]
        return max(nums, default=0) + 1

    # ── CREATE PROJECT ──────────────────────────────────

    def _new_project(self):
        win = tk.Toplevel(self.root)
        win.title("New Project"); win.geometry("720x720"); win.configure(bg="#0a0e17")
        frame = self._scroll(win)
        self._hdr(frame, "NEW PROJECT")
        e_title = self._field(frame, "Project Title")
        e_type = self._dropdown(frame, "Type", TYPE_OPTIONS, TYPE_OPTIONS[0])
        e_month = self._field(frame, "Month (e.g. JAN)")
        e_year = self._field(frame, "Year", str(datetime.now().year))
        e_summary = self._field(frame, "Summary (1-2 sentences)", multi=True)
        e_tags = self._field(frame, "Tags (comma separated)")
        self._hdr(frame, "WRITEUP SECTIONS")
        self._hint(frame, "Fill in what you have now — you can always edit later")
        e_overview = self._field(frame, "Overview", multi=True)
        e_built = self._field(frame, "What I Built / Did", multi=True)
        e_challenges = self._field(frame, "Challenges & Solutions", multi=True)
        e_takeaways = self._field(frame, "Key Takeaways", multi=True)
        e_tools = self._field(frame, "Tools & Resources (one per line)", multi=True)

        def do_create():
            title = self._v(e_title)
            if not title: messagebox.showwarning("!", "Enter a title"); return
            num = self._next_num()
            fn = f"project-{num}.html"
            ptype = self._v(e_type)
            month = self._v(e_month).upper() or "MMM"
            year = self._v(e_year) or str(datetime.now().year)
            summary = self._v(e_summary) or "Project summary."
            tags = [t.strip() for t in self._v(e_tags).split(",") if t.strip()]
            # Build project file from template
            self._create_project_file(fn, title, ptype, month, year, summary, tags,
                self._v(e_overview), self._v(e_built), self._v(e_challenges),
                self._v(e_takeaways), self._v(e_tools))
            # Add card to projects.html
            self._add_card(fn, title, ptype, month, year, summary, tags)
            self._update_count()
            self._update_prevnext()
            win.destroy()
            self._refresh_projects()
            messagebox.showinfo("Done", f"Created {fn}: '{title}'")

        tk.Button(frame, text="CREATE PROJECT", bg="#00ff88", fg="#020409",
                  font=("Consolas", 11, "bold"), relief="flat", padx=20, pady=8,
                  command=do_create, cursor="hand2").pack(pady=20)

    def _create_project_file(self, fn, title, ptype, month, year, summary, tags,
                              overview, built, challenges, takeaways, tools_text):
        tmpl = self.files.get("project-template.html", "")
        if not tmpl:
            messagebox.showerror("Error", "project-template.html not found!"); return
        h = tmpl
        tc = TYPE_MAP.get(ptype, "lab")
        # Page title
        h = h.replace("<title>KIERAN — Project Title Here</title>",
                       f"<title>KIERAN — {title}</title>")
        # Breadcrumb
        h = h.replace('<span class="current">Project Title</span>',
                       f'<span class="current">{title}</span>')
        # Type badge
        old_type = re.search(r'<span class="project-type \w+">([^<]+)</span>', h)
        if old_type:
            h = h.replace(old_type.group(0), f'<span class="project-type {tc}">{ptype}</span>')
        # Date
        h = h.replace('<span class="project-date">MMM YYYY</span>',
                       f'<span class="project-date">{month} {year}</span>')
        # Title
        h = h.replace("YOUR PROJECT TITLE HERE", title)
        # Summary
        old_sum = self._ex(h, r'class="project-summary">\s*(.+?)\s*</p>')
        if old_sum: h = h.replace(old_sum, summary, 1)
        # Tags
        old_tb = re.search(r'(<div class="project-tags">)(.*?)(</div>)', h, re.DOTALL)
        if old_tb and tags:
            nt = old_tb.group(1) + "\n"
            for t in tags: nt += f'      <span class="project-tag">{t}</span>\n'
            nt += "    " + old_tb.group(3)
            h = h.replace(old_tb.group(0), nt, 1)
        # Content
        placeholders = {
            "overview": "Start with the big picture. What was the goal of this project? What problem were you trying to solve, or what were you trying to learn? Give readers context before diving into the details.",
            "built": "Describe the setup in detail. Walk through the architecture, the tools you used, the configuration steps. Be specific — this is where you show technical depth.",
            "challenges": "What went wrong? What took longer than expected? How did you troubleshoot? This section is where problem-solving skills shine — employers love seeing how you think through issues.",
            "takeaways": "What did you learn? How does this project connect to real-world security work? Tie it back to the skills and concepts that matter in the industry.",
        }
        vals = {"overview": overview, "built": built, "challenges": challenges, "takeaways": takeaways}
        for key, placeholder in placeholders.items():
            if vals[key]: h = h.replace(placeholder, vals[key])
        # Tools list
        if tools_text:
            tools = [t.strip() for t in tools_text.split("\n") if t.strip()]
            old_ul = re.search(r'(<h2>Tools &amp; Resources</h2>\s*<ul>)(.*?)(</ul>)', h, re.DOTALL)
            if old_ul and tools:
                nl = old_ul.group(1) + "\n"
                for t in tools: nl += f"    <li>{t}</li>\n"
                nl += "  " + old_ul.group(3)
                h = h.replace(old_ul.group(0), nl)
        self.files[fn] = h

    def _add_card(self, fn, title, ptype, month, year, desc, tags):
        if "projects.html" not in self.files: return
        tc = TYPE_MAP.get(ptype, "lab")
        num = re.search(r'(\d+)', fn).group(1)
        tags_html = "\n".join(f'          <span class="project-tag">{t}</span>' for t in tags) \
                    if tags else '          <span class="project-tag">Tag</span>'
        card = f"""
    <!-- PROJECT {num} -->
    <a href="{fn}" class="project-card">
      <div class="project-date-col">
        <span class="project-month">{month}</span>
        <span class="project-year">{year}</span>
      </div>
      <div class="project-info">
        <div class="project-type-row">
          <span class="project-type {tc}">{ptype}</span>
          <span class="project-num">{num.zfill(2)}</span>
        </div>
        <div class="project-name">{title}</div>
        <p class="project-desc">{desc}</p>
        <div class="project-tags">
{tags_html}
        </div>
      </div>
      <div class="project-arrow">&rarr;</div>
    </a>
"""
        marker = '<div class="projects-list">'
        self.files["projects.html"] = self.files["projects.html"].replace(marker, marker + card, 1)

    # ── EDIT PROJECT ────────────────────────────────────

    def _edit_project(self, fn):
        html = self.files.get(fn, "")
        if not html: return
        win = tk.Toplevel(self.root)
        win.title(f"Edit — {fn}"); win.geometry("720x720"); win.configure(bg="#0a0e17")
        frame = self._scroll(win)
        self._hdr(frame, f"EDITING: {fn}")

        title = self._ex(html, r'class="project-title">([^<]+)<')
        e_title = self._field(frame, "Title", title)

        tc = self._ex(html, r'class="project-type (\w+)"')
        cur_type = CLASS_TO_TYPE.get(tc, TYPE_OPTIONS[0])
        e_type = self._dropdown(frame, "Type", TYPE_OPTIONS, cur_type)

        date_str = self._ex(html, r'class="project-date">([^<]+)<')
        parts = date_str.split()
        e_month = self._field(frame, "Month", parts[0] if parts else "")
        e_year = self._field(frame, "Year", parts[1] if len(parts) > 1 else "")

        summary = re.sub(r'\s+', ' ', self._ex(html, r'class="project-summary">\s*(.+?)\s*</p>'))
        e_summary = self._field(frame, "Summary", summary, multi=True)

        tags = re.findall(r'class="project-tag">([^<]+)<', html)
        e_tags = self._field(frame, "Tags (comma separated)", ", ".join(tags))

        self._hdr(frame, "WRITEUP SECTIONS")
        # Parse all h2 > p sections
        sections = re.findall(r'<h2>([^<]+)</h2>\s*<p>\s*(.*?)\s*</p>', html, re.DOTALL)
        sec_widgets = {}
        for stitle, scontent in sections:
            sec_widgets[stitle] = self._field(frame, stitle,
                re.sub(r'\s+', ' ', scontent).strip(), multi=True)

        # Tools list
        tools_items = re.findall(r'<li>(.+?)</li>', html)
        e_tools = self._field(frame, "Tools & Resources (one per line)",
                              "\n".join(tools_items), multi=True)

        def do_save():
            h = self.files[fn]
            nt = self._v(e_title)
            # Title
            old_t = self._ex(h, r'class="project-title">([^<]+)<')
            if old_t and old_t != nt:
                h = h.replace(f'class="project-title">{old_t}<', f'class="project-title">{nt}<')
                h = h.replace(f'<span class="current">{old_t}</span>',
                              f'<span class="current">{nt}</span>')
                old_pt = self._ex(h, r'<title>([^<]+)</title>')
                if old_pt: h = h.replace(f'<title>{old_pt}</title>', f'<title>KIERAN — {nt}</title>')
            # Type
            new_type = self._v(e_type)
            old_type_m = re.search(r'<span class="project-type \w+">([^<]+)</span>', h)
            if old_type_m:
                h = h.replace(old_type_m.group(0),
                    f'<span class="project-type {TYPE_MAP.get(new_type,"lab")}">{new_type}</span>')
            # Date
            old_d = self._ex(h, r'class="project-date">([^<]+)<')
            new_d = f"{self._v(e_month).upper()} {self._v(e_year)}"
            if old_d != new_d:
                h = h.replace(f'class="project-date">{old_d}<', f'class="project-date">{new_d}<')
            # Summary
            old_s = self._ex(h, r'class="project-summary">\s*(.+?)\s*</p>')
            new_s = self._v(e_summary)
            if old_s and new_s and old_s != new_s: h = h.replace(old_s, new_s, 1)
            # Tags
            new_tags = [t.strip() for t in self._v(e_tags).split(",") if t.strip()]
            otb = re.search(r'(<div class="project-tags">)(.*?)(</div>)', h, re.DOTALL)
            if otb and new_tags:
                nblock = otb.group(1) + "\n"
                for t in new_tags: nblock += f'      <span class="project-tag">{t}</span>\n'
                nblock += "    " + otb.group(3)
                h = h.replace(otb.group(0), nblock, 1)
            # Sections
            for stitle, widget in sec_widgets.items():
                nv = self._v(widget)
                m = re.search(rf'(<h2>{re.escape(stitle)}</h2>\s*<p>\s*)(.*?)(\s*</p>)', h, re.DOTALL)
                if m and nv: h = h.replace(m.group(0), f'{m.group(1)}{nv}{m.group(3)}', 1)
            # Tools
            tools_text = self._v(e_tools)
            if tools_text:
                tools = [t.strip() for t in tools_text.split("\n") if t.strip()]
                old_ul = re.search(r'(<h2>Tools &amp; Resources</h2>\s*<ul>)(.*?)(</ul>)', h, re.DOTALL)
                if old_ul:
                    nl = old_ul.group(1) + "\n"
                    for t in tools: nl += f"    <li>{t}</li>\n"
                    nl += "  " + old_ul.group(3)
                    h = h.replace(old_ul.group(0), nl)
            self.files[fn] = h
            # Update card on projects page
            self._update_card(fn, nt, self._v(e_type), self._v(e_month).upper(),
                              self._v(e_year), self._v(e_summary),
                              [t.strip() for t in self._v(e_tags).split(",") if t.strip()])
            self._update_prevnext()
            win.destroy()
            self._refresh_projects()
            messagebox.showinfo("Saved", f"'{nt}' updated.")

        tk.Button(frame, text="SAVE CHANGES", bg="#00f5ff", fg="#020409",
                  font=("Consolas", 11, "bold"), relief="flat", padx=20, pady=8,
                  command=do_save, cursor="hand2").pack(pady=20)

    def _update_card(self, fn, title, ptype, month, year, desc, tags):
        if "projects.html" not in self.files: return
        html = self.files["projects.html"]
        cm = re.search(rf'(<a href="{re.escape(fn)}" class="project-card">)(.*?)(</a>)',
                        html, re.DOTALL)
        if not cm: return
        card = cm.group(2)
        tc = TYPE_MAP.get(ptype, "lab")
        num = re.search(r'(\d+)', fn).group(1).zfill(2)
        card = re.sub(r'(class="project-month">)[^<]+(<)', rf'\g<1>{month}\2', card)
        card = re.sub(r'(class="project-year">)[^<]+(<)', rf'\g<1>{year}\2', card)
        card = re.sub(r'<span class="project-type \w+">([^<]+)</span>',
                       f'<span class="project-type {tc}">{ptype}</span>', card)
        card = re.sub(r'(class="project-num">)[^<]+(<)', rf'\g<1>{num}\2', card)
        card = re.sub(r'(class="project-name">)[^<]+(<)', rf'\g<1>{title}\2', card)
        card = re.sub(r'(class="project-desc">)[^<]+(<)', rf'\g<1>{desc}\2', card)
        otb = re.search(r'(<div class="project-tags">)(.*?)(</div>)', card, re.DOTALL)
        if otb and tags:
            nt = otb.group(1) + "\n"
            for t in tags: nt += f'          <span class="project-tag">{t}</span>\n'
            nt += "        " + otb.group(3)
            card = card.replace(otb.group(0), nt)
        self.files["projects.html"] = html.replace(cm.group(0),
            f'{cm.group(1)}{card}{cm.group(3)}')

    # ── DELETE PROJECT ──────────────────────────────────

    def _delete_project(self, fn):
        title = self._ex(self.files.get(fn, ""), r'class="project-title">([^<]+)<', default=fn)
        if not messagebox.askyesno("Delete?",
            f"Delete '{title}'?\n\nThis removes {fn} and its card from projects.html."):
            return
        # Remove file from dict and disk
        self.files.pop(fn, None)
        path = os.path.join(self.site_dir, fn)
        if os.path.exists(path): os.remove(path)
        # Remove card from projects.html
        if "projects.html" in self.files:
            html = self.files["projects.html"]
            num = re.search(r'(\d+)', fn).group(1)
            # Try with comment
            pat = rf'\s*<!-- PROJECT {num}\b[^>]*-->\s*<a href="{re.escape(fn)}" class="project-card">.*?</a>'
            new_html = re.sub(pat, '', html, flags=re.DOTALL)
            if new_html == html:
                # Try without comment
                pat2 = rf'\s*<a href="{re.escape(fn)}" class="project-card">.*?</a>'
                new_html = re.sub(pat2, '', html, flags=re.DOTALL)
            self.files["projects.html"] = new_html
        self._update_count()
        self._update_prevnext()
        self._refresh_projects()

    # ── PROJECT HELPERS ─────────────────────────────────

    def _update_count(self):
        if "projects.html" not in self.files: return
        n = len([f for f in self.files if re.match(r'^project-\d+\.html$', f)])
        self.files["projects.html"] = re.sub(
            r'(class="num">)\d+(</span>)', rf'\g<1>{n:02d}\2',
            self.files["projects.html"])

    def _update_prevnext(self):
        pfs = sorted(
            [f for f in self.files if re.match(r'^project-\d+\.html$', f)],
            key=lambda x: int(re.search(r'(\d+)', x).group(1)))
        for i, pf in enumerate(pfs):
            h = self.files[pf]
            # Prev
            if i > 0:
                pfile = pfs[i - 1]
                ptitle = self._ex(self.files[pfile], r'class="project-title">([^<]+)<', default="Previous")
                prev_href = pfile
                prev_cls = "prev"
                prev_title = ptitle
            else:
                prev_href = "#"
                prev_cls = "prev disabled"
                prev_title = "\u2014"
            # Next
            if i < len(pfs) - 1:
                nfile = pfs[i + 1]
                ntitle = self._ex(self.files[nfile], r'class="project-title">([^<]+)<', default="Next")
                next_href = nfile
                next_cls = "next"
                next_title = ntitle
            else:
                next_href = "#"
                next_cls = "next disabled"
                next_title = "\u2014"
            # Replace prev link
            h = re.sub(
                r'<a href="[^"]*" class="project-nav-link prev[^"]*">\s*<span class="project-nav-label">[^<]*</span>\s*<span class="project-nav-title">[^<]*</span>\s*</a>',
                f'<a href="{prev_href}" class="project-nav-link {prev_cls}">\n'
                f'    <span class="project-nav-label">\u2190 Previous Project</span>\n'
                f'    <span class="project-nav-title">{prev_title}</span>\n'
                f'  </a>', h)
            # Replace next link
            h = re.sub(
                r'<a href="[^"]*" class="project-nav-link next[^"]*">\s*<span class="project-nav-label">[^<]*</span>\s*<span class="project-nav-title">[^<]*</span>\s*</a>',
                f'<a href="{next_href}" class="project-nav-link {next_cls}">\n'
                f'    <span class="project-nav-label">Next Project \u2192</span>\n'
                f'    <span class="project-nav-title">{next_title}</span>\n'
                f'  </a>', h)
            self.files[pf] = h

    # ═══════════════════════════════════════════════════════
    #  LINKS TAB
    # ═══════════════════════════════════════════════════════

    def _tab_links(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" LINKS ")
        frame = self._scroll(tab)
        idx = self.files.get("index.html", "")
        chtml = self.files.get("contact.html", "")

        self._hdr(frame, "PROFILE LINKS")
        self._hint(frame, "Changes apply everywhere these appear across all pages")

        li = self._ex(idx, r'linkedin\.com/in/([^"<\s]+)', default="yourprofile")
        self.lnk_linkedin = self._field(frame, "LinkedIn Username", li)

        gh = self._ex(idx, r'github\.com/([^"<\s]+)', default="yourusername")
        self.lnk_github = self._field(frame, "GitHub Username", gh)

        self._hdr(frame, "CONTACT PAGE PROFILES")
        self._hint(frame, "These update links and display text on your contact page")

        thm = self._ex(chtml, r'tryhackme\.com/p/([^"<\s]+)', default="yourusername")
        self.lnk_thm = self._field(frame, "TryHackMe Username", thm)

        htb = self._ex(chtml, r'hackthebox\.com/users/([^"<\s]+)', default="yourid")
        self.lnk_htb = self._field(frame, "HackTheBox User ID", htb)

        self._hdr(frame, "PLATFORM CARD DESCRIPTIONS (Contact Page)")
        self._hint(frame, "Edit the label, description, and URL text for each platform card")

        # Parse each platform card: label, desc, stat
        self.plat_widgets = {}
        for plat, plat_name in [("thm", "TryHackMe"), ("github", "GitHub"),
                                 ("linkedin", "LinkedIn"), ("htb", "Hack The Box")]:
            self._hdr(frame, plat_name)
            # Find the card block
            card_match = re.search(
                rf'class="platform-card {plat}"[^>]*>(.*?)</a>',
                chtml, re.DOTALL)
            card = card_match.group(1) if card_match else ""
            plabel = self._ex(card, r'class="plat-label">([^<]+)<', default="")
            pdesc = self._ex(card, r'class="plat-desc">([^<]+)<', default="")
            pstat = self._ex(card, r'class="plat-stat">([^<]+)<', default="")
            self.plat_widgets[plat] = {
                "label": self._field(frame, f"Category Label", plabel),
                "desc": self._field(frame, f"Description", pdesc),
                "stat": self._field(frame, f"URL Display Text", pstat),
            }

    # ═══════════════════════════════════════════════════════
    #  HERO TAB
    # ═══════════════════════════════════════════════════════

    def _tab_hero(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" HERO ")
        frame = self._scroll(tab)
        html = self.files.get("index.html", "")
        self._hdr(frame, "HERO SECTION")
        tag = self._ex(html, r'class="hero-tag"[^>]*>([^<]+)<')
        self.hero_tag = self._field(frame, "Tagline (green text)", tag)
        titles = re.findall(r'<span class="block[^"]*">([^<]*)</span>', html)
        sub = self._ex(html, r'class="sub">([^<]+)<')
        self.hero_t1 = self._field(frame, "Title Line 1", titles[0] if titles else "")
        self.hero_t2 = self._field(frame, "Title Line 2 (cyan name)", titles[1] if len(titles) > 1 else "")
        self.hero_t3 = self._field(frame, "Title Line 3", titles[2] if len(titles) > 2 else "")
        self.hero_sub = self._field(frame, "Subtitle", sub)
        desc = self._ex(html, r'class="hero-desc">\s*(.+?)\s*</p>')
        self.hero_desc = self._field(frame, "Description", re.sub(r'\s+', ' ', desc), multi=True)
        self._hdr(frame, "STATS")
        sn = re.findall(r'class="stat-num">([^<]+)<', html)
        sl = re.findall(r'class="stat-label">([^<]+)<', html)
        self.hero_sn1 = self._field(frame, "Stat 1 Number", sn[0] if sn else "")
        self.hero_sl1 = self._field(frame, "Stat 1 Label", sl[0] if sl else "")
        self.hero_sn2 = self._field(frame, "Stat 2 Number", sn[1] if len(sn) > 1 else "")
        self.hero_sl2 = self._field(frame, "Stat 2 Label", sl[1] if len(sl) > 1 else "")
        self._hdr(frame, "STATUS BAR")
        status = self._ex(html, r'class="status-dot"></div>\s*\n?\s*(.+?)\s*</div>\s*\n?\s*</section')
        self.hero_status = self._field(frame, "Status text", re.sub(r'\s+', ' ', status))

    # ═══════════════════════════════════════════════════════
    #  ABOUT TAB
    # ═══════════════════════════════════════════════════════

    def _tab_about(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" ABOUT ")
        frame = self._scroll(tab)
        html = self.files.get("index.html", "")
        self._hdr(frame, "ABOUT (Home Page)")
        texts = re.findall(r'class="about-text">(.+?)</p>', html, re.DOTALL)
        self.about_p1 = self._field(frame, "Paragraph 1", texts[0].strip() if texts else "", multi=True)
        self.about_p2 = self._field(frame, "Paragraph 2", texts[1].strip() if len(texts) > 1 else "", multi=True)
        self.about_p3 = self._field(frame, "Paragraph 3", texts[2].strip() if len(texts) > 2 else "", multi=True)
        self._hdr(frame, "SKILL TAGS")
        tags = re.findall(r'class="skill-tag">([^<]+)<', html)
        self.about_tags = self._field(frame, "Tags (comma separated)", ", ".join(tags), multi=True)

    # ═══════════════════════════════════════════════════════
    #  CERTS TAB
    # ═══════════════════════════════════════════════════════

    def _tab_certs(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" CERTS ")
        frame = self._scroll(tab)
        html = self.files.get("index.html", "")
        self._hdr(frame, "CERTIFICATION DATES")
        statuses = re.findall(r'class="cert-status"[^>]*>([^<]+)<', html)
        self.cert_dates = []
        for i, label in enumerate(["A+ Status", "Network+ Status", "Security+ Status"]):
            val = statuses[i].replace("&nbsp;", " ").strip() if i < len(statuses) else ""
            self.cert_dates.append(self._field(frame, label, val))

    # ═══════════════════════════════════════════════════════
    #  NAV TAB
    # ═══════════════════════════════════════════════════════

    def _tab_nav(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" NAV ")
        frame = self._scroll(tab)
        self._hdr(frame, "SITE BRANDING")
        self._hint(frame, "Changes apply across ALL pages")
        self.nav_name = self._field(frame, "Name (logo)", "KIERAN")
        self.nav_tagline = self._field(frame, "Tagline (after //)", "SECURITY")

    # ═══════════════════════════════════════════════════════
    #  FOOTER TAB
    # ═══════════════════════════════════════════════════════

    def _tab_footer(self):
        tab = tk.Frame(self.nb, bg="#0a0e17")
        self.nb.add(tab, text=" FOOTER ")
        frame = self._scroll(tab)
        html = self.files.get("index.html", "")
        self._hdr(frame, "FOOTER (All Pages)")
        ft = re.findall(r'class="footer-text">\s*([^<]+?)\s*<', html)
        self.ft1 = self._field(frame, "Line 1 (credentials)", ft[0].replace("&nbsp;", " ") if ft else "")
        self.ft2 = self._field(frame, "Line 2 (built with)", ft[1].replace("&nbsp;", " ") if len(ft) > 1 else "")

    # ═══════════════════════════════════════════════════════
    #  SAVE ALL
    # ═══════════════════════════════════════════════════════

    def _backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        d = os.path.join(self.site_dir, f"backup_{ts}")
        os.makedirs(d, exist_ok=True)
        for fp in glob.glob(os.path.join(self.site_dir, "*.html")):
            shutil.copy2(fp, os.path.join(d, os.path.basename(fp)))
        messagebox.showinfo("Backup", f"Saved to:\n{d}")

    def _sr(self, fn, old, new):
        if fn in self.files and old and old != new:
            self.files[fn] = self.files[fn].replace(old, new)

    def _sr_all(self, old, new):
        if old and old != new:
            for fn in self.files:
                self.files[fn] = self.files[fn].replace(old, new)

    def _save_all(self):
        try:
            self._apply_links()
            self._apply_hero()
            self._apply_about()
            self._apply_certs()
            self._apply_nav()
            self._apply_footer()
            for name, content in self.files.items():
                with open(os.path.join(self.site_dir, name), "w", encoding="utf-8") as f:
                    f.write(content)
            messagebox.showinfo("Saved", f"All changes saved to:\n{self.site_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Apply functions ─────────────────────────────────

    def _apply_links(self):
        idx = self.files.get("index.html", "")
        chtml = self.files.get("contact.html", "")
        # LinkedIn URL — update everywhere
        old_li = self._ex(idx, r'linkedin\.com/in/([^"<\s]+)', default="yourprofile")
        new_li = self._v(self.lnk_linkedin)
        if old_li != new_li:
            self._sr_all(f"linkedin.com/in/{old_li}", f"linkedin.com/in/{new_li}")
        # GitHub URL — update everywhere
        old_gh = self._ex(idx, r'github\.com/([^"<\s]+)', default="yourusername")
        new_gh = self._v(self.lnk_github)
        if old_gh != new_gh:
            self._sr_all(f"github.com/{old_gh}", f"github.com/{new_gh}")
        # Contact page specific
        if chtml:
            old_thm = self._ex(chtml, r'tryhackme\.com/p/([^"<\s]+)', default="yourusername")
            new_thm = self._v(self.lnk_thm)
            if old_thm != new_thm:
                self._sr("contact.html", f"tryhackme.com/p/{old_thm}", f"tryhackme.com/p/{new_thm}")
            old_htb = self._ex(chtml, r'hackthebox\.com/users/([^"<\s]+)', default="yourid")
            new_htb = self._v(self.lnk_htb)
            if old_htb != new_htb:
                self._sr("contact.html", f"hackthebox.com/users/{old_htb}", f"hackthebox.com/users/{new_htb}")
            # Platform card content
            for plat in ["thm", "github", "linkedin", "htb"]:
                if plat not in self.plat_widgets: continue
                card_match = re.search(
                    rf'class="platform-card {plat}"[^>]*>(.*?)</a>',
                    self.files.get("contact.html", ""), re.DOTALL)
                if not card_match: continue
                card = card_match.group(1)
                for cls, key in [("plat-label", "label"), ("plat-desc", "desc"), ("plat-stat", "stat")]:
                    old_val = self._ex(card, rf'class="{cls}">([^<]+)<', default="")
                    new_val = self._v(self.plat_widgets[plat][key])
                    if old_val and new_val and old_val != new_val:
                        self._sr("contact.html", f'class="{cls}">{old_val}<',
                                 f'class="{cls}">{new_val}<')

    def _apply_hero(self):
        h = self.files.get("index.html", "")
        if not h: return
        # Tag
        old = self._ex(h, r'class="hero-tag"[^>]*>([^<]+)<')
        nv = self._v(self.hero_tag)
        if old and old != nv:
            self.files["index.html"] = self.files["index.html"].replace(
                f">{old}</", f">{nv}</", 1)
        # Title spans
        spans = re.findall(r'(<span class="block[^"]*">)([^<]*)(</span>)', self.files["index.html"])
        for i, (o, txt, c) in enumerate(spans):
            w = [self.hero_t1, self.hero_t2, self.hero_t3]
            if i < len(w):
                nv = self._v(w[i])
                if txt != nv:
                    self.files["index.html"] = self.files["index.html"].replace(
                        f"{o}{txt}{c}", f"{o}{nv}{c}", 1)
        # Sub
        old = self._ex(self.files["index.html"], r'class="sub">([^<]+)<')
        nv = self._v(self.hero_sub)
        if old and old != nv:
            self._sr("index.html", f'class="sub">{old}<', f'class="sub">{nv}<')
        # Desc
        old = self._ex(self.files["index.html"], r'class="hero-desc">\s*(.+?)\s*</p>')
        nv = self._v(self.hero_desc)
        if old and nv and old != nv:
            self.files["index.html"] = self.files["index.html"].replace(old, nv, 1)
        # Stats
        h = self.files["index.html"]
        for cls, widgets in [("stat-num", [self.hero_sn1, self.hero_sn2]),
                              ("stat-label", [self.hero_sl1, self.hero_sl2])]:
            matches = re.findall(rf'(class="{cls}">)([^<]+)(<)', h)
            for i, (p, old, c) in enumerate(matches):
                if i < len(widgets):
                    nv = self._v(widgets[i])
                    if old != nv:
                        self.files["index.html"] = self.files["index.html"].replace(
                            f"{p}{old}{c}", f"{p}{nv}{c}", 1)

    def _apply_about(self):
        h = self.files.get("index.html", "")
        if not h: return
        texts = re.findall(r'class="about-text">(.+?)</p>', h, re.DOTALL)
        for i, old in enumerate(texts):
            w = [self.about_p1, self.about_p2, self.about_p3]
            if i < len(w):
                nv = self._v(w[i])
                if old.strip() != nv:
                    self.files["index.html"] = self.files["index.html"].replace(old, nv, 1)
        new_tags = [t.strip() for t in self._v(self.about_tags).split(",") if t.strip()]
        otb = re.search(r'(<div class="skill-tags">)(.*?)(</div>)', self.files["index.html"], re.DOTALL)
        if otb and new_tags:
            nt = otb.group(1) + "\n"
            for t in new_tags: nt += f'      <div class="skill-tag">{t}</div>\n'
            nt += "    " + otb.group(3)
            self.files["index.html"] = self.files["index.html"].replace(otb.group(0), nt, 1)

    def _apply_certs(self):
        h = self.files.get("index.html", "")
        if not h: return
        statuses = re.findall(r'(class="cert-status"[^>]*>)([^<]+)(<)', h)
        for i, (p, old, c) in enumerate(statuses):
            if i < len(self.cert_dates):
                nv = self._v(self.cert_dates[i])
                if old.strip().replace("&nbsp;", " ") != nv:
                    self.files["index.html"] = self.files["index.html"].replace(
                        f"{p}{old}{c}", f"{p}{nv}{c}", 1)

    def _apply_nav(self):
        nn = self._v(self.nav_name)
        nt = self._v(self.nav_tagline)
        self._sr_all('KIERAN <span>// SECURITY</span>', f'{nn} <span>// {nt}</span>')
        self._sr_all('<div class="footer-logo">KIERAN</div>',
                     f'<div class="footer-logo">{nn}</div>')

    def _apply_footer(self):
        h = self.files.get("index.html", "")
        ft = re.findall(r'class="footer-text">\s*([^<]+?)\s*<', h)
        if ft: self._sr_all(ft[0], self._v(self.ft1))
        if len(ft) > 1: self._sr_all(ft[1], self._v(self.ft2))


if __name__ == "__main__":
    root = tk.Tk()
    SiteManager(root)
    root.mainloop()
