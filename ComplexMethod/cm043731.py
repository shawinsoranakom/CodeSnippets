def _normalize_toc_table(md: str) -> str:
            """Normalize a mangled Table of Contents markdown table.

            Foreign-filer exhibits (and some domestic filings) include a
            TOC rendered as an HTML table with colspan-driven multi-
            column layouts.  The converter produces markdown rows with
            varying column counts (4–7 cells per row).  This helper
            detects the TOC table and re-builds it as a clean 4-column
            table:  Page | Section | Page | Section.
            """
            _toc_hdr = re.compile(
                r"^\|[^\n]*Table\s+of\s+Contents[^\n]*\|",
                re.MULTILINE,
            )
            m = _toc_hdr.search(md)
            if not m:
                return md

            # Locate the full table block.
            toc_start = md.rfind("\n", 0, m.start())
            toc_start = toc_start + 1 if toc_start >= 0 else m.start()
            # Advance past the header line's trailing newline.
            toc_end = m.end()
            first_nl = md.find("\n", toc_end)
            if first_nl >= 0:
                toc_end = first_nl + 1
            while toc_end < len(md):
                nl = md.find("\n", toc_end)
                if nl < 0:
                    toc_end = len(md)
                    break
                next_line = md[toc_end:nl].strip()
                if next_line.startswith("|"):
                    toc_end = nl + 1
                else:
                    toc_end = nl
                    break

            toc_block = md[toc_start:toc_end]
            _link_re = re.compile(r"\[([^\]]*)\]\((#[^)]*)\)")

            new_rows: list[tuple[str, str, str, str]] = []
            for _toc_row in toc_block.splitlines():
                _toc_row = _toc_row.strip()
                if not _toc_row.startswith("|") or _toc_row.startswith("|---"):
                    continue
                cells = [c.strip() for c in _toc_row.strip("|").split("|")]
                if any("Table of Contents" in c for c in cells):
                    continue

                # Pair up (page_link, section_name) from non-empty cells.
                non_empty = [(i, c) for i, c in enumerate(cells) if c]
                pairs: list[tuple[str, str]] = []
                j = 0
                while j < len(non_empty):
                    _, val = non_empty[j]
                    if _link_re.match(val) or val.isdigit():
                        sect = non_empty[j + 1][1] if j + 1 < len(non_empty) else ""
                        pairs.append((val, sect))
                        j += 2
                    else:
                        pairs.append(("", val))
                        j += 1

                if len(pairs) == 1:
                    new_rows.append((pairs[0][0], pairs[0][1], "", ""))
                elif len(pairs) >= 2:
                    new_rows.append(
                        (pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1])
                    )

            if not new_rows:
                return md

            toc_lines = ["| Table of Contents | | | |", "|---|---|---|---|"]
            for p1, s1, p2, s2 in new_rows:
                toc_lines.append(f"| {p1} | {s1} | {p2} | {s2} |")
            toc_lines.append("")
            return md[:toc_start] + "\n".join(toc_lines) + md[toc_end:]