def parse(self) -> None:
        def get_substr(span: Span) -> str:
            return self.string[slice(*span)]

        configured_items = self.get_configured_items()
        isolated_spans = self.find_spans_by_selector(self.isolate)
        protected_spans = self.find_spans_by_selector(self.protect)
        command_matches = self.get_command_matches(self.string)

        def get_key(category, i, flag):
            def get_span_by_category(category, i):
                if category == 0:
                    return configured_items[i][0]
                if category == 1:
                    return isolated_spans[i]
                if category == 2:
                    return protected_spans[i]
                return command_matches[i].span()

            index, paired_index = get_span_by_category(category, i)[::flag]
            return (
                index,
                flag * (2 if index != paired_index else -1),
                -paired_index,
                flag * category,
                flag * i
            )

        index_items = sorted([
            (category, i, flag)
            for category, item_length in enumerate((
                len(configured_items),
                len(isolated_spans),
                len(protected_spans),
                len(command_matches)
            ))
            for i in range(item_length)
            for flag in (1, -1)
        ], key=lambda t: get_key(*t))

        inserted_items = []
        labelled_items = []
        overlapping_spans = []
        level_mismatched_spans = []

        label = 1
        protect_level = 0
        bracket_stack = [0]
        bracket_count = 0
        open_command_stack = []
        open_stack = []
        for category, i, flag in index_items:
            if category >= 2:
                protect_level += flag
                if flag == 1 or category == 2:
                    continue
                inserted_items.append((i, 0))
                command_match = command_matches[i]
                command_flag = self.get_command_flag(command_match)
                if command_flag == 1:
                    bracket_count += 1
                    bracket_stack.append(bracket_count)
                    open_command_stack.append((len(inserted_items), i))
                    continue
                if command_flag == 0:
                    continue
                pos, i_ = open_command_stack.pop()
                bracket_stack.pop()
                open_command_match = command_matches[i_]
                attr_dict = self.get_attr_dict_from_command_pair(
                    open_command_match, command_match
                )
                if attr_dict is None:
                    continue
                span = (open_command_match.end(), command_match.start())
                labelled_items.append((span, attr_dict))
                inserted_items.insert(pos, (label, 1))
                inserted_items.insert(-1, (label, -1))
                label += 1
                continue
            if flag == 1:
                open_stack.append((
                    len(inserted_items), category, i,
                    protect_level, bracket_stack.copy()
                ))
                continue
            span, attr_dict = configured_items[i] \
                if category == 0 else (isolated_spans[i], {})
            pos, category_, i_, protect_level_, bracket_stack_ \
                = open_stack.pop()
            if category_ != category or i_ != i:
                overlapping_spans.append(span)
                continue
            if protect_level_ or protect_level:
                continue
            if bracket_stack_ != bracket_stack:
                level_mismatched_spans.append(span)
                continue
            labelled_items.append((span, attr_dict))
            inserted_items.insert(pos, (label, 1))
            inserted_items.append((label, -1))
            label += 1
        labelled_items.insert(0, ((0, len(self.string)), {}))
        inserted_items.insert(0, (0, 1))
        inserted_items.append((0, -1))

        if overlapping_spans:
            log.warning(
                "Partly overlapping substrings detected: %s",
                ", ".join(
                    f"'{get_substr(span)}'"
                    for span in overlapping_spans
                )
            )
        if level_mismatched_spans:
            log.warning(
                "Cannot handle substrings: %s",
                ", ".join(
                    f"'{get_substr(span)}'"
                    for span in level_mismatched_spans
                )
            )

        def reconstruct_string(
            start_item: tuple[int, int],
            end_item: tuple[int, int],
            command_replace_func: Callable[[re.Match], str],
            command_insert_func: Callable[[int, int, dict[str, str]], str]
        ) -> str:
            def get_edge_item(i: int, flag: int) -> tuple[Span, str]:
                if flag == 0:
                    match_obj = command_matches[i]
                    return (
                        match_obj.span(),
                        command_replace_func(match_obj)
                    )
                span, attr_dict = labelled_items[i]
                index = span[flag < 0]
                return (
                    (index, index),
                    command_insert_func(i, flag, attr_dict)
                )

            items = [
                get_edge_item(i, flag)
                for i, flag in inserted_items[slice(
                    inserted_items.index(start_item),
                    inserted_items.index(end_item) + 1
                )]
            ]
            pieces = [
                get_substr((start, end))
                for start, end in zip(
                    [interval_end for (_, interval_end), _ in items[:-1]],
                    [interval_start for (interval_start, _), _ in items[1:]]
                )
            ]
            interval_pieces = [piece for _, piece in items[1:-1]]
            return "".join(it.chain(*zip(pieces, (*interval_pieces, ""))))

        self.labelled_spans = [span for span, _ in labelled_items]
        self.reconstruct_string = reconstruct_string