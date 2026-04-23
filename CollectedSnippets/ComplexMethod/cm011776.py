def get_node_splits(self) -> tuple[Split, Split]:
        """
        Get a compatible pointwise, reduction split of the node
        """

        if len(self.all_node_sizes) == 1:
            return next(iter(self.all_node_sizes))

        if len(self.pw_split_options) == 0:
            return ((self.pointwise_numel,), (self.red_numel,))

        max_pw_split = max(self.pw_split_options.keys())
        max_red_split = max(self.red_split_options.keys())

        def add_combined_split_options(
            split_options: dict[int, OrderedSet[Split]], curr_length: int
        ) -> None:
            for split in split_options[curr_length]:
                for i in range(len(split) - 1):
                    new_split = tuple(
                        split[0:i] + (sympy_product(split[i : i + 2]),) + split[i + 2 :]
                    )
                    split_options[len(new_split)].add(new_split)

        max_total_splits = max_pw_split + max_red_split
        for curr_iter, total_splits in enumerate(range(max_total_splits, 0, -1)):
            for pw_split_len in range(total_splits, 0, -1):
                for pw_split in self.pw_split_options[pw_split_len]:
                    for red_split in self.red_split_options[
                        total_splits - pw_split_len
                    ]:
                        if out := self.try_split(pw_split, red_split):
                            return out

            add_combined_split_options(self.pw_split_options, max_pw_split - curr_iter)
            add_combined_split_options(
                self.red_split_options, max_red_split - curr_iter
            )

        # if for whatever reason we couldn't split above, return default split
        return ((self.pointwise_numel,), (self.red_numel,))