def _extract_chart_legend(table) -> str | None:
    """Detect a chart-legend table and return an inline legend string.

    SEC filings embed bar/pie charts as ``<img>`` tags followed by
    small HTML tables that use tiny coloured ``<td>`` cells as colour
    swatches paired with label text (typically font-family 'Gotham
    Narrow Book', font-size ~5 pt, rows of height ~3 pt).

    The standard table converter turns these into single-column
    markdown tables like::

        | Affiliates |
        |---|
        | Europe |

    This helper detects the pattern and emits a more useful format
    that preserves the colour-to-label mapping so the chart can be
    interpreted::

        **Legend:** ■ (#009dd9) United States · ■ (#0b2d71) Other Americas · …

    Returns ``None`` if the table is *not* a chart legend.
    """
    rows = table.find_all("tr")
    if not rows or len(rows) > 30:
        return None

    # Quick pre-check: reject tables that look like financial data.
    # Real chart legends never contain numeric data, dollar signs,
    # parenthesised negatives, or percentage values in their cells.
    _data_cell_re = re.compile(
        r"(?:^\s*[-—]?\s*\$|\d[\d,]+\.\d|^\s*\(\s*\d|\d\s*%\s*$" + r"|^\s*\d{4}\s*$)"
    )
    data_cell_count = 0
    for row in rows:
        for td in row.find_all("td"):
            cell_text = td.get_text(strip=True)
            if cell_text and _data_cell_re.search(cell_text):
                data_cell_count += 1
    if data_cell_count >= 2:
        return None

    # Chart-legend tables use tiny coloured cells as colour swatches.
    # A "swatch cell" MUST be a cell whose ONLY purpose is to show
    # a background colour — it must have NO text content (or at most
    # a single non-breaking space).  Cells that combine colour with
    # text are header/data cells, NOT swatches.
    #
    # Additionally, swatch cells should be physically small (height
    # ≤ 8px or width ≤ 30px via inline style).
    _height_re = re.compile(r"height:\s*(\d+(?:\.\d+)?)\s*(?:px|pt)", re.I)
    _width_re = re.compile(r"width:\s*(\d+(?:\.\d+)?)\s*(?:px|pt)", re.I)
    swatch_count = 0
    all_labels: list[str] = []
    all_colors: list[str] = []
    # Track how many rows have non-empty text in > 2 columns — a sign
    # this is a real data table, not a legend.
    multi_col_text_rows = 0

    for row in rows:
        tds = row.find_all("td")
        row_color: str | None = None
        row_label: str | None = None
        text_cell_count = 0
        for td in tds:
            style = td.get("style", "") or ""
            bg = _LEGEND_BG_RE.search(style)
            cell_text = td.get_text(strip=True)

            # A swatch cell: has background-color, is NOT white,
            # and has NO meaningful text content.
            if bg and bg.group(1).lower() not in ("#ffffff", "#fff") and not cell_text:
                # Check for small dimensions (strong swatch signal)
                h_m = _height_re.search(style)
                w_m = _width_re.search(style)
                is_tiny = (h_m and float(h_m.group(1)) <= 8) or (
                    w_m and float(w_m.group(1)) <= 30
                )
                if is_tiny:
                    row_color = bg.group(1)
                    swatch_count += 1
                else:
                    # Empty cell with colour but not tiny — could
                    # still be a swatch if no dimension is specified
                    # (some legends omit explicit sizes).  Count it
                    # but don't bump swatch_count (only truly tiny
                    # cells are confident swatch detections).
                    row_color = bg.group(1)
                # Cell has BOTH colour and text → NOT a swatch.
                # This is typically a header or data cell with shading.

            if cell_text and len(cell_text) < 80:
                row_label = cell_text
                text_cell_count += 1

        if text_cell_count > 2:
            multi_col_text_rows += 1
        if row_color and not row_label:
            all_colors.append(row_color)
        elif row_label and not row_color:
            all_labels.append(row_label)
        elif row_color and row_label:
            # Both in one row — paired directly
            all_colors.append(row_color)
            all_labels.append(row_label)

    # If many rows have text in 3+ columns, this is a data table.
    if multi_col_text_rows >= 2:
        return None

    # Require enough CONFIDENT swatch detections (tiny empty colour
    # cells) and at least two labels.
    if swatch_count < 2 or len(all_labels) < 2:
        return None

    # Labels should be category names, NOT numbers/years/percentages.
    _numeric_label_re = re.compile(r"^\s*[\d,.%$€£()\-—]+\s*$")
    non_numeric_labels = [lab for lab in all_labels if not _numeric_label_re.match(lab)]
    if len(non_numeric_labels) < 2:
        return None

    # Final sanity: the raw text of the whole table should be short
    # (legends are just a handful of category names).
    full_text = table.get_text(strip=True)
    if len(full_text) > 500:
        return None

    # Pair colours and labels.  The HTML structure typically puts the
    # label row immediately before its colour swatch row, so
    # all_labels[i] corresponds to all_colors[i].
    # Only include labels that have a paired colour swatch.
    # Unpaired labels (more labels than colours) are typically chart
    # titles/descriptions embedded in the legend table — omit them.
    n_pairs = min(len(non_numeric_labels), len(all_colors))
    if n_pairs < 2:
        return None

    # Build an HTML legend with actual CSS-styled colour swatches.
    # Using background-color on inline-block spans is the most reliable
    # way to render coloured boxes across markdown renderers.
    swatch = (
        '<span style="display:inline-block;width:12px;height:12px;'
        "background:{color};vertical-align:middle;border-radius:2px"
        '"></span>'
    )
    items: list[str] = []
    for idx in range(n_pairs):
        box = swatch.format(color=all_colors[idx])
        items.append(f"{box} {non_numeric_labels[idx]}")

    legend_body = " &nbsp;&middot;&nbsp; ".join(items)
    return (
        f'<div style="margin:4px 0;font-size:0.9em"><b>Legend:</b> {legend_body}</div>'
    )