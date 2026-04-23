def _choose_from_candidates(
                    candidates: list[dict], entry_code: str
                ) -> dict | None:
                    if not candidates:
                        return None
                    if len(candidates) == 1:
                        return candidates[0]

                    entry_code_upper = entry_code.upper()
                    markers: set[str] = {entry_code_upper}
                    if entry_code_upper in {"CD_T", "NEGCD_T"}:
                        markers |= {"CD", "CREDIT"}
                    elif entry_code_upper == "DB_T":
                        markers |= {"DB", "DEBIT"}
                    elif entry_code_upper == "A_P":
                        markers |= {"ASSET", "ASSETS"}
                    elif entry_code_upper == "L_P":
                        markers |= {"LIAB", "LIABILITIES", "LIABILITY"}

                    for cand in candidates:
                        haystack = f"{cand.get('hierarchy_node_id','')} {cand.get('hierarchy_series_id','')}".upper()
                        if any(m in haystack for m in markers):
                            return cand

                    return candidates[0]