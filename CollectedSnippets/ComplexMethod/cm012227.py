def replace_split(
        self,
        graph: torch.fx.Graph,
        split_node: torch.fx.Node,
        split_sections: list[int],
        user_inputs_list: list[list[torch.fx.Node | _Range]],
        split_ranges: list[_Range],
    ) -> list[list[torch.fx.Node]]:
        """
        Replace the split node. It can either remove the split node if len(split_ranges) == 1, or simplify it
        into a split with lesser sections if len(split_ranges) > 1.

        Returns the new `user_inputs_list`, with tuples replaced with new getitems from the newer split node.
        """
        split_input = split_node.args[0]
        split_dim = _get_dim(split_node)
        if len(split_ranges) == 1:  # We can completely eliminate the split node
            split_items = [split_input]
        else:
            with graph.inserting_after(split_node):
                new_split = graph.call_function(
                    torch.split,
                    args=(
                        split_input,
                        [r[1] - r[0] for r in split_ranges],
                    ),
                    kwargs={"dim": split_dim},
                )
                if is_node_meta_valid(split_input):  # type: ignore[arg-type, union-attr]
                    new_split.meta["example_value"] = torch.split(
                        split_input.meta["example_value"],  # type: ignore[union-attr]
                        [r[1] - r[0] for r in split_ranges],
                        dim=split_dim,
                    )
                counters[backend]["scmerge_split_added"] += 1
            split_items = []
            with graph.inserting_after(new_split):
                for i in range(len(split_ranges)):
                    getitem = graph.call_function(operator.getitem, args=(new_split, i))
                    if is_node_meta_valid(new_split):
                        getitem.meta["example_value"] = new_split.meta["example_value"][
                            i
                        ]
                        split_items.append(getitem)
        # Now assign the right getitem to the right input
        cumulative_sizes = [0] + torch.cumsum(torch.tensor(split_sections), 0).tolist()
        new_user_inputs_list = []
        for user_inputs in user_inputs_list:
            new_user_inputs = []
            for user_input in user_inputs:
                if isinstance(user_input, tuple):
                    # Find the correct new getitem (present in split_items)
                    new_user_inputs.append(
                        # pyrefly: ignore [bad-argument-type]
                        split_items[
                            split_ranges.index(
                                (
                                    cumulative_sizes[user_input[0]],
                                    cumulative_sizes[user_input[1] + 1],
                                )
                            )
                        ]
                    )
                else:
                    new_user_inputs.append(user_input)
            new_user_inputs_list.append(new_user_inputs)
        return new_user_inputs_list