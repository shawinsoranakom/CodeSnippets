def get_group_part_items(self) -> list[tuple[str, list[int]]]:
        if not self.labels:
            return []

        def get_neighbouring_pairs(vals):
            return list(zip(vals[:-1], vals[1:]))

        range_lens, group_labels = zip(*(
            (len(list(grouper)), val)
            for val, grouper in it.groupby(self.labels)
        ))
        submob_indices_lists = [
            list(range(*submob_range))
            for submob_range in get_neighbouring_pairs(
                [0, *it.accumulate(range_lens)]
            )
        ]
        labelled_spans = self.labelled_spans
        start_items = [
            (group_labels[0], 1),
            *(
                (curr_label, 1)
                if self.span_contains(
                    labelled_spans[prev_label], labelled_spans[curr_label]
                )
                else (prev_label, -1)
                for prev_label, curr_label in get_neighbouring_pairs(
                    group_labels
                )
            )
        ]
        end_items = [
            *(
                (curr_label, -1)
                if self.span_contains(
                    labelled_spans[next_label], labelled_spans[curr_label]
                )
                else (next_label, 1)
                for curr_label, next_label in get_neighbouring_pairs(
                    group_labels
                )
            ),
            (group_labels[-1], -1)
        ]
        group_substrs = [
            re.sub(r"\s+", "", self.reconstruct_string(
                start_item, end_item,
                self.replace_for_matching,
                lambda label, flag, attr_dict: ""
            ))
            for start_item, end_item in zip(start_items, end_items)
        ]
        return list(zip(group_substrs, submob_indices_lists))