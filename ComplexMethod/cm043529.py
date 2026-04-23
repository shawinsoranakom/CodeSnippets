def validate_and_correct(self, lines_dict: dict) -> List[str]:
        """Validates and corrects each hunk in the diff."""
        problems = []
        past_hunk = None
        cut_lines_dict = lines_dict.copy()
        for hunk in self.hunks:
            if past_hunk is not None:
                # make sure to not cut so much that the start_line gets out of range
                cut_ind = min(
                    past_hunk.start_line_pre_edit + past_hunk.hunk_len_pre_edit,
                    hunk.start_line_pre_edit,
                )
                cut_lines_dict = {
                    key: val for key, val in cut_lines_dict.items() if key >= (cut_ind)
                }
            is_valid = hunk.validate_and_correct(cut_lines_dict, problems)
            if not is_valid and len(problems) > 0:
                for idx, val in enumerate(problems):
                    print(f"\nInvalid Hunk NO.{idx}---\n{val}\n---")
                self.hunks.remove(hunk)
            # now correct the numbers, assuming the start line pre-edit has been fixed
            hunk.hunk_len_pre_edit = (
                hunk.category_counts[RETAIN] + hunk.category_counts[REMOVE]
            )
            hunk.hunk_len_post_edit = (
                hunk.category_counts[RETAIN] + hunk.category_counts[ADD]
            )
            if past_hunk is not None:
                hunk.start_line_post_edit = (
                    hunk.start_line_pre_edit
                    + past_hunk.hunk_len_post_edit
                    - past_hunk.hunk_len_pre_edit
                    + past_hunk.start_line_post_edit
                    - past_hunk.start_line_pre_edit
                )
            else:
                hunk.start_line_post_edit = hunk.start_line_pre_edit
            past_hunk = hunk
        return problems