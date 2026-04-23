def _normalize_section(section):
            # pad section to length 3: (txt, sec_id, poss)
            if len(section) == 1:
                section = (section[0], "", [])
            elif len(section) == 2:
                section = (section[0], "", section[1])
            elif len(section) != 3:
                raise ValueError(f"Unexpected section length: {len(section)} (value={section!r})")

            txt, layoutno, poss = section
            if isinstance(poss, str):
                poss = pdf_parser.extract_positions(poss)
                if poss:
                    first = poss[0]  # tuple: ([pn], x1, x2, y1, y2)
                    pn = first[0]
                    if isinstance(pn, list) and pn:
                        pn = pn[0]  # [pn] -> pn
                        poss[0] = (pn, *first[1:])

            return (txt, layoutno, poss)