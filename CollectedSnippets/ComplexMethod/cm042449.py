def tabulate(tabular_data, headers=(), tablefmt="simple", floatfmt="g", stralign="left", numalign=None):
  rows = [list(row) for row in tabular_data]

  def fmt(val):
    if isinstance(val, str):
      return val
    if isinstance(val, (bool, int)):
      return str(val)
    try:
      return format(val, floatfmt)
    except (TypeError, ValueError):
      return str(val)

  formatted = [[fmt(c) for c in row] for row in rows]
  hdrs = [str(h) for h in headers] if headers else None

  ncols = max((len(r) for r in formatted), default=0)
  if hdrs:
    ncols = max(ncols, len(hdrs))
  if ncols == 0:
    return ""

  for r in formatted:
    r.extend([""] * (ncols - len(r)))
  if hdrs:
    hdrs.extend([""] * (ncols - len(hdrs)))

  widths = [0] * ncols
  if hdrs:
    for i in range(ncols):
      widths[i] = len(hdrs[i])
  for row in formatted:
    for i in range(ncols):
      widths[i] = max(widths[i], max(len(ln) for ln in row[i].split('\n')))

  def _align(s, w):
    if stralign == "center":
      return s.center(w)
    return s.ljust(w)

  if tablefmt == "html":
    parts = ["<table>"]
    if hdrs:
      parts.append("<thead>")
      parts.append("<tr>" + "".join(f"<th>{h}</th>" for h in hdrs) + "</tr>")
      parts.append("</thead>")
    parts.append("<tbody>")
    for row in formatted:
      parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    parts.append("</tbody>")
    parts.append("</table>")
    return "\n".join(parts)

  if tablefmt == "simple_grid":
    def _sep(left, mid, right):
      return left + mid.join("\u2500" * (w + 2) for w in widths) + right

    top, mid_sep, bot = _sep("\u250c", "\u252c", "\u2510"), _sep("\u251c", "\u253c", "\u2524"), _sep("\u2514", "\u2534", "\u2518")

    def _fmt_row(cells):
      split = [c.split('\n') for c in cells]
      nlines = max(len(s) for s in split)
      for s in split:
        s.extend([""] * (nlines - len(s)))
      return ["\u2502" + "\u2502".join(f" {_align(split[i][li], widths[i])} " for i in range(ncols)) + "\u2502" for li in range(nlines)]

    lines = [top]
    if hdrs:
      lines.extend(_fmt_row(hdrs))
      lines.append(mid_sep)
    for ri, row in enumerate(formatted):
      lines.extend(_fmt_row(row))
      lines.append(mid_sep if ri < len(formatted) - 1 else bot)
    return "\n".join(lines)

  # simple
  gap = "  "
  lines = []
  if hdrs:
    lines.append(gap.join(h.ljust(w) for h, w in zip(hdrs, widths, strict=True)))
    lines.append(gap.join("-" * w for w in widths))
  for row in formatted:
    lines.append(gap.join(_align(row[i], widths[i]) for i in range(ncols)))
  return "\n".join(lines)