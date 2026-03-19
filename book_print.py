"""
book_print.py  —  A4 booklet export for BookWriter
----------------------------------------------------
Prints two A5 pages side by side on a single A4 landscape sheet.
Left page = odd book pages, Right page = even book pages.

Requires:  pip install reportlab
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk

from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, FrameBreak
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas as rl_canvas

FONT_MAP = {
    "Georgia":         "Times-Roman",
    "Times New Roman": "Times-Roman",
    "Courier New":     "Courier",
    "Arial":           "Helvetica",
    "Helvetica":       "Helvetica",
    "Verdana":         "Helvetica",
    "Palatino":        "Times-Roman",
    "Garamond":        "Times-Roman",
}

BOLD_MAP = {
    "Times-Roman": "Times-Bold",
    "Helvetica":   "Helvetica-Bold",
    "Courier":     "Courier-Bold",
}

# A4 landscape dimensions
A4L = landscape(A4)
PAGE_W, PAGE_H = A4L  # ~841 x 595 pts

# Each A5 panel is half the A4 width
PANEL_W = PAGE_W / 2
PANEL_H = PAGE_H

MARGIN = 14 * mm
DIVIDER_X = PAGE_W / 2  # centre divider


def _rl_font(name):
    return FONT_MAP.get(name, "Times-Roman")


# ── Draw the centre divider line on every sheet ────────────────────────────────
def _draw_divider(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas.setLineWidth(0.5)
    canvas.line(DIVIDER_X, 10 * mm, DIVIDER_X, PAGE_H - 10 * mm)
    canvas.restoreState()


def export_to_pdf(book, out_path, font_family="Georgia", font_size=12):
    rl_font = _rl_font(font_family)
    rl_bold = BOLD_MAP.get(rl_font, rl_font)

    # ── Two frames per A4 sheet: left panel and right panel ───────────────────
    left_frame = Frame(
        x1=MARGIN,
        y1=MARGIN,
        width=PANEL_W - 2 * MARGIN,
        height=PANEL_H - 2 * MARGIN,
        id="left",
        showBoundary=0,
    )
    right_frame = Frame(
        x1=PANEL_W + MARGIN,
        y1=MARGIN,
        width=PANEL_W - 2 * MARGIN,
        height=PANEL_H - 2 * MARGIN,
        id="right",
        showBoundary=0,
    )

    doc = BaseDocTemplate(
        out_path,
        pagesize=A4L,
        title=book.get("title", "Book"),
        author="BookWriter",
    )

    template = PageTemplate(
        id="booklet",
        frames=[left_frame, right_frame],
        onPage=_draw_divider,
    )
    doc.addPageTemplates([template])

    # ── Styles ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "BookTitle",
        fontName=rl_bold,
        fontSize=font_size + 6,
        leading=(font_size + 6) * 1.4,
        spaceAfter=6 * mm,
        alignment=TA_LEFT,
    )

    body_style = ParagraphStyle(
        "BookBody",
        fontName=rl_font,
        fontSize=font_size,
        leading=font_size * 1.5,
        spaceAfter=3,
        alignment=TA_LEFT,
    )

    page_num_style = ParagraphStyle(
        "PageNum",
        fontName=rl_font,
        fontSize=font_size - 2,
        textColor=(0.5, 0.5, 0.5),
        spaceAfter=2 * mm,
        alignment=TA_LEFT,
    )

    # ── Build story ───────────────────────────────────────────────────────────
    story = []

    # Title panel (takes the left slot of the first sheet)
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph(book.get("title", "Untitled Book"), title_style))
    # Jump to right panel (blank title verso)
    story.append(FrameBreak())

    pages = book.get("pages", [""])
    for i, page_text in enumerate(pages, start=1):
        story.append(Paragraph(f"— {i} —", page_num_style))

        for line in page_text.splitlines():
            if line.strip():
                safe = (line.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))
                story.append(Paragraph(safe, body_style))
            else:
                story.append(Spacer(1, body_style.leading))

        # Move to next panel (either right side of same sheet or left of next)
        story.append(FrameBreak())

    doc.build(story)


def print_book_dialog(parent=None):
    src = filedialog.askopenfilename(
        title="Choose a book file",
        filetypes=[("Book files", "*.book"), ("JSON", "*.json"), ("All", "*.*")],
        parent=parent,
    )
    if not src:
        return

    try:
        with open(src, "r", encoding="utf-8") as f:
            book = json.load(f)
        if "pages" not in book:
            raise ValueError("Missing 'pages' key — not a valid book file.")
    except Exception as e:
        messagebox.showerror("Load error", f"Could not read book:\n{e}", parent=parent)
        return

    dlg = tk.Toplevel(parent)
    dlg.title("Print settings")
    dlg.geometry("300x180")
    dlg.resizable(False, False)
    dlg.grab_set()

    tk.Label(dlg, text="Font family:").grid(row=0, column=0, padx=12, pady=10, sticky="w")
    font_var = tk.StringVar(value="Georgia")
    ttk.Combobox(dlg, textvariable=font_var, values=list(FONT_MAP.keys()),
                 state="readonly", width=16).grid(row=0, column=1, pady=10)

    tk.Label(dlg, text="Font size:").grid(row=1, column=0, padx=12, sticky="w")
    size_var = tk.IntVar(value=12)
    ttk.Combobox(dlg, textvariable=size_var,
                 values=[9, 10, 11, 12, 13, 14, 16, 18],
                 state="readonly", width=5).grid(row=1, column=1, sticky="w")

    confirmed = [False]

    def confirm():
        confirmed[0] = True
        dlg.destroy()

    tk.Button(dlg, text="Choose save location →", command=confirm,
              padx=10, pady=6).grid(row=3, column=0, columnspan=2, pady=20)

    if parent:
        parent.wait_window(dlg)
    else:
        dlg.mainloop()

    if not confirmed[0]:
        return

    default_name = os.path.splitext(os.path.basename(src))[0] + ".pdf"
    out = filedialog.asksaveasfilename(
        title="Save PDF as",
        initialfile=default_name,
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        parent=parent,
    )
    if not out:
        return

    try:
        export_to_pdf(book, out,
                      font_family=font_var.get(),
                      font_size=int(size_var.get()))
        messagebox.showinfo("Done", f"PDF saved to:\n{out}", parent=parent)
    except Exception as e:
        messagebox.showerror("Export error", f"PDF export failed:\n{e}", parent=parent)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    print_book_dialog(parent=root)
    root.destroy()
