def matching_blocks(
        self,
        source: StringMobject,
        target: StringMobject,
        matched_keys: Iterable[str],
        key_map: dict[str, str]
    ) -> list[tuple[VMobject, VMobject]]:
        syms1 = source.get_symbol_substrings()
        syms2 = target.get_symbol_substrings()
        counts1 = list(map(source.substr_to_path_count, syms1))
        counts2 = list(map(target.substr_to_path_count, syms2))

        # Start with user specified matches
        blocks = [(source[key1], target[key2]) for key1, key2 in key_map.items()]
        blocks += [(source[key], target[key]) for key in matched_keys]

        # Nullify any intersections with those matches in the two symbol lists
        for sub_source, sub_target in blocks:
            for i in range(len(syms1)):
                if i < len(source) and source[i] in sub_source.family_members_with_points():
                    syms1[i] = "Null1"
            for j in range(len(syms2)):
                if j < len(target) and target[j] in sub_target.family_members_with_points():
                    syms2[j] = "Null2"

        # Group together longest matching substrings
        while True:
            matcher = SequenceMatcher(None, syms1, syms2)
            match = matcher.find_longest_match(0, len(syms1), 0, len(syms2))
            if match.size == 0:
                break

            i1 = sum(counts1[:match.a])
            i2 = sum(counts2[:match.b])
            size = sum(counts1[match.a:match.a + match.size])

            blocks.append((source[i1:i1 + size], target[i2:i2 + size]))

            for i in range(match.size):
                syms1[match.a + i] = "Null1"
                syms2[match.b + i] = "Null2"

        return blocks