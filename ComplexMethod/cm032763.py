def select_level_group(lines, raw_levels):
        if not raw_levels:
            return []

        # Select one regex family before assigning numeric levels. Mixing
        # patterns across families would make the level numbers ambiguous and
        # break downstream comparisons.
        hits = [0] * len(raw_levels)
        for i, group in enumerate(raw_levels):
            for sec in lines:
                sec = sec.strip()
                if not sec:
                    continue
                for pattern in group:
                    if re.match(pattern, sec) and not not_bullet(sec):
                        hits[i] += 1
                        break

        maximum = 0
        selected = -1
        for i, hit in enumerate(hits):
            if hit <= maximum:
                continue
            selected = i
            maximum = hit

        if selected < 0:
            return []
        return [pattern for pattern in raw_levels[selected] if pattern]