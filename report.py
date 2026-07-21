import copy
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from models import MatchResult, InterviewQuestions

# ── Color palette ─────────────────────────────────────────────────────────────
DARK       = colors.HexColor("#000000")
ACCENT     = colors.HexColor("#8D8FF2")   # indigo
SUCCESS    = colors.HexColor("#10B981")   # emerald
WARNING    = colors.HexColor("#F59E0B")   # amber
DANGER     = colors.HexColor("#F17070")   # red
LIGHT_BG   = colors.HexColor("#F8FAFC")
MUTED      = colors.HexColor("#64748B")
WHITE      = colors.white


def _score_color(score: int):
    if score >= 75:
        return SUCCESS
    elif score >= 50:
        return WARNING
    return DANGER


def _flag_color(flag: str):
    return {
        "good": SUCCESS,
        "vague": WARNING,
        "weak": WARNING,
        "hallucinated": DANGER,
    }.get(flag, MUTED)


def _hex(c) -> str:
    """Reliable '#rrggbb' string for a reportlab Color, for use inside <font color='...'> tags."""
    return "#%02x%02x%02x" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))

# ── Fixed suggestion section order ───────────────────────────────────────────
# Leadership & Community → Certifications & Achievements → Projects
# These three are forced to the end of suggestions in this order.
_TAIL_SECTION_ORDER = ["leadership", "certifications", "projects"]


def _section_sort_key(s) -> tuple:
    """Return (group, original_index) so tail sections sort to the end in order."""
    name = s.section.lower()
    for rank, keyword in enumerate(_TAIL_SECTION_ORDER):
        if keyword in name:
            return (1, rank)
    return (0, 0)  # all other sections keep their natural order


def generate_pdf_report(result: MatchResult) -> bytes:
    buffer = BytesIO()

    # ── Metadata collected once for use in header/footer ─────────────────────
    candidate_name = ""
    target_job = ""
    # Try to extract candidate name from the first suggestion's context or leave blank.
    # Job title: peek at gap_analysis or suggestions for a label (best-effort).
    # These are populated via closure into the canvas callback below.
    report_date = date.today().strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=1.10 * inch,   # extra room for header
        bottomMargin=0.65 * inch, # extra room for footer
    )

    base = getSampleStyleSheet()
    story = []

    # Custom styles 
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=base["Normal"],
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=DARK,
        spaceAfter=20,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=base["Normal"],
        fontSize=19,
        fontName="Helvetica",
        textColor=MUTED,
        spaceAfter=16,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=base["Normal"],
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=DARK,
        spaceBefore=18,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=DARK,
        spaceAfter=4,
        leading=15,
    )
    muted_style = ParagraphStyle(
        "Muted",
        parent=body_style,
        textColor=MUTED,
        fontSize=9,
    )
    tag_style = ParagraphStyle(
        "Tag",
        parent=base["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=DARK,
    )

    # ── Per-page header / footer callback ────────────────────────────────────
    GRAY      = colors.HexColor("#9CA3AF")   # light gray for header/footer text
    RULE_GRAY = colors.HexColor("#D1D5DB")   # slightly lighter rule line
    PAGE_W, PAGE_H = letter
    H_MARGIN  = 0.45 * inch

    def _draw_header_footer(canvas, doc):
        canvas.saveState()
        page_num   = canvas.getPageNumber()
        total_pages = getattr(doc, "_total_pages", "?")

        # ── Header ────────────────────────────────────────────────────────────
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(GRAY)
        # Left: candidate name (if available)
        canvas.drawString(H_MARGIN, PAGE_H - 0.50 * inch, candidate_name)
        # Center: report title
        canvas.setFont("Helvetica", 9)
        title_text = "AI Resume and Job Match Report"
        canvas.drawCentredString(PAGE_W / 2, PAGE_H - 0.50 * inch, title_text)
        # Right: target job title (if available)
        canvas.drawRightString(PAGE_W - H_MARGIN, PAGE_H - 0.50 * inch,
                               target_job if target_job else "")
        # Thin rule below header
        canvas.setStrokeColor(RULE_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(H_MARGIN, PAGE_H - 0.60 * inch,
                    PAGE_W - H_MARGIN, PAGE_H - 0.60 * inch)

        # ── Footer ────────────────────────────────────────────────────────────
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(GRAY)
        # Left: date
        canvas.drawString(H_MARGIN, 0.38 * inch, f"Generated: {report_date}")
        # Right: page number
        canvas.drawRightString(PAGE_W - H_MARGIN, 0.38 * inch,
                               f"Page {page_num} of {total_pages}")

        canvas.restoreState()

    def divider():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=10, spaceBefore=7)

    def pill_table(items, bg_color):
        """Render a list of items as colored pills, wrapping into rows of max 5."""
        if not items:
            return Paragraph("None identified.", muted_style)

        # Split items into rows of up to 5 to avoid overly wide tables
        COLS = 5
        rows = [items[i:i + COLS] for i in range(0, len(items), COLS)]
        # Pad last row so the table has uniform column count
        for row in rows:
            while len(row) < COLS:
                row.append("")

        cell_width = 1.3 * inch
        table_data = [
            [Paragraph(cell, tag_style) if cell else Paragraph("", tag_style) for cell in row]
            for row in rows
        ]

        t = Table(table_data, colWidths=[cell_width] * COLS, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    # ── Resolve header metadata values ───────────────────────────────────────
    # candidate_name: MatchResult has no dedicated name field, so we leave it
    # blank. If a name field is added to the model in future, assign it here.
    # target_job: attempt to extract from the first strong-match skill label;
    # this is a best-effort heuristic — leave blank if nothing useful found.
    if result.match_score.strong_matches:
        # Use the first two strong-match items as a compact job-context hint,
        # but only if they look like short labels (≤ 30 chars each).
        hints = [m for m in result.match_score.strong_matches[:2] if len(m) <= 30]
        target_job = ", ".join(hints) if hints else ""

    # ── Page body header (first page title) ──────────────────────────────────
    story.append(Paragraph("AI Resume and Job Match Report", title_style))

    # Score summary row 
    llm_score = result.match_score.score
    sem_pct = result.semantic_similarity.percentage if result.semantic_similarity else "N/A"

    score_data = [
        [
            Paragraph("LLM Match Score", muted_style),
            Paragraph("Semantic Similarity", muted_style),
            Paragraph("Eval Quality", muted_style),
        ],
        [
            Paragraph(f"<font size=15><b>{llm_score}</b></font><font size=11> / 100</font>", ParagraphStyle("sc", parent=base["Normal"], textColor=_score_color(llm_score))),
            Paragraph(f"<font size=15><b>{sem_pct}</b></font><font size=11> / 100</font>", ParagraphStyle("sc2", parent=base["Normal"], textColor=_score_color(sem_pct if isinstance(sem_pct, int) else 50))),
            Paragraph(f"<font size=15><b>{result.eval_report.overall_quality if result.eval_report else 'N/A'}</b></font><font size=11> / 10</font>", ParagraphStyle("sc3", parent=base["Normal"], textColor=ACCENT)),
        ],
    ]

    score_table = Table(score_data, colWidths=[2.2 * inch, 2.2 * inch, 2.2 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (3, 3), (-1, -1), 12),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(score_table)
    story.append(Spacer(4, 12))

    # LLM Match Score 
    story.append(Paragraph("Match Analysis", h2_style))
    story.append(Paragraph(result.match_score.reasoning, body_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Strong matches</b>", body_style))
    story.append(pill_table(result.match_score.strong_matches, SUCCESS))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Partial matches</b>", body_style))
    story.append(pill_table(result.match_score.weak_matches, WARNING))

    # Semantic Similarity 
    if result.semantic_similarity:
        story.append(Paragraph("Semantic Similarity", h2_style))
        story.append(divider())
        story.append(Paragraph(result.semantic_similarity.interpretation, body_style))
        story.append(Paragraph(
            f"Cosine similarity score: <b>{result.semantic_similarity.score}</b> — "
            "this is a mathematical embedding comparison, independent of the LLM's analysis.",
            muted_style,
        ))

    # Gap Analysis 
    story.append(Paragraph("Gap Analysis", h2_style))
    story.append(divider())

    sections = [
        ("Missing Skills", result.gap_analysis.missing_skills, DANGER),
        ("Missing Experience", result.gap_analysis.missing_experience, WARNING),
        ("Missing ATS Keywords", result.gap_analysis.missing_keywords, colors.HexColor("#8B5CF6")),
        ("Priority Gaps (fix these first)", result.gap_analysis.priority_gaps, WARNING),
    ]
    for label, items, color in sections:
        story.append(Paragraph(f"<b>{label}</b>", body_style))
        story.append(pill_table(items, color))
        story.append(Spacer(1, 8))

    # Resume Suggestions
    story.append(Paragraph("Resume Improvement Suggestions", h2_style))
    story.append(divider())
    story.append(Paragraph(result.resume_suggestions.summary_advice, body_style))
    story.append(Spacer(4, 8))

    eval_map = {}
    if result.eval_report:
        eval_map = {e.suggestion_index: e for e in result.eval_report.evaluations}

    # Sort: all other sections first (natural order), then Leadership →
    # Certifications → Projects in that fixed order.
    original_suggestions = list(result.resume_suggestions.suggestions)
    sorted_suggestions = sorted(
        enumerate(original_suggestions),
        key=lambda pair: _section_sort_key(pair[1]),
    )

    for orig_i, s in sorted_suggestions:
        ev = eval_map.get(orig_i)
        flag = ev.flag if ev else "—"
        flag_color = _flag_color(flag) if ev else MUTED
        quality = f"  Quality: {ev.quality_score}/10" if ev else ""

        header = [
            Paragraph(f"<b>{s.section}</b>", body_style),
            Paragraph(f"<font color='{_hex(flag_color)}'>● {flag.upper()}</font>{quality}", muted_style),
        ]
        header_table = Table([header], colWidths=[3.5 * inch, 3 * inch])
        header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

        rows = [
            [header_table],
            [Paragraph(f"<i>Before:</i> {s.original}", muted_style)] if s.original else [],
            [Paragraph(f"<b>Suggestion:</b> {s.suggestion}", body_style)],
            [Paragraph(f"<i>Why:</i> {s.reason}", muted_style)],
        ]
        rows = [r for r in rows if r]

        card = Table(rows, colWidths=[6.5 * inch])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEAFTER", (0, 0), (0, -1), 3, flag_color),
        ]))
        story.append(KeepTogether([card, Spacer(1, 8)]))

    # Interview Questions (before Self-Eval Summary)
    if result.interview_questions:
        iq = result.interview_questions

        q_style = ParagraphStyle(
            "QStyle",
            parent=body_style,
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=ACCENT,
            spaceBefore=6,
            spaceAfter=2,
        )
        a_style = ParagraphStyle(
            "AStyle",
            parent=body_style,
            fontSize=9.5,
            fontName="Helvetica",
            textColor=DARK,
            leading=14,
            spaceAfter=6,
            leftIndent=12,
        )

        def _render_qa_block(heading: str, qa_list):
            story.append(Paragraph(heading, h2_style))
            story.append(divider())
            for idx, qa in enumerate(qa_list, 1):
                q_para = Paragraph(f"Q{idx}. {qa.question}", q_style)
                a_para = Paragraph(f"A: {qa.answer}", a_style)
                card = Table(
                    [[q_para], [a_para]],
                    colWidths=[6.5 * inch],
                )
                card.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEAFTER", (0, 0), (0, -1), 3, ACCENT),
                ]))
                story.append(KeepTogether([card, Spacer(1, 8)]))

        _render_qa_block("Interview Questions — Skills & Keywords", iq.skill_questions)
        _render_qa_block("Interview Questions — Projects", iq.project_questions)

    # Self-Eval Summary — always last section in the document
    if result.eval_report:
        story.append(Paragraph("Self-Eval Summary", h2_style))
        story.append(divider())
        story.append(Paragraph(result.eval_report.eval_summary, body_style))

    # ── Two-pass build: first pass counts pages, second pass renders ──────────
    # ReportLab's SimpleDocTemplate doesn't expose total page count during build,
    # so we build to a throwaway buffer first to get the count, then build for real.
    _dummy = BytesIO()
    _dummy_doc = SimpleDocTemplate(
        _dummy,
        pagesize=letter,
        leftMargin=doc.leftMargin,
        rightMargin=doc.rightMargin,
        topMargin=doc.topMargin,
        bottomMargin=doc.bottomMargin,
    )
    _dummy_doc.build(copy.deepcopy(story))
    doc._total_pages = _dummy_doc.page

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)
    return buffer.getvalue()
Pressing key...Clicking...Stopping...

Stop Agent
