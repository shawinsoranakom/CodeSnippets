def _try_position_merge(hdrs_a, hdrs_b):
            """Try to merge two header rows by matching positions.
            Returns (merged_texts, merged_positions) sorted by position,
            or (None, None) if no month+year merges found.
            """
            # Build position maps
            pos_a = {s: t for t, s in hdrs_a}
            pos_b = {s: t for t, s in hdrs_b}
            all_positions = sorted(set(pos_a.keys()) | set(pos_b.keys()))

            merged = []
            merged_pos = []
            month_year_merges = 0
            for pos in all_positions:
                text_a = pos_a.get(pos)
                text_b = pos_b.get(pos)
                if text_a and text_b:
                    a_is_month = bool(re.search(MONTHS_PATTERN, text_a, re.I))
                    b_is_year = is_year(text_b)
                    a_is_year = is_year(text_a)
                    b_is_month = bool(re.search(MONTHS_PATTERN, text_b, re.I))
                    if a_is_month and b_is_year:
                        merged.append(f"{text_a.rstrip(',').strip()}, {text_b}")
                        month_year_merges += 1
                    elif a_is_year and b_is_month:
                        merged.append(f"{text_b.rstrip(',').strip()}, {text_a}")
                        month_year_merges += 1
                    else:
                        # Generic vertical merge (e.g., "%" + "Change" -> "% Change")
                        merged.append(f"{text_a} {text_b}".strip())
                elif text_a:
                    merged.append(text_a)
                elif text_b:
                    merged.append(text_b)
                merged_pos.append(pos)

            if month_year_merges > 0:
                return merged, merged_pos
            return None, None