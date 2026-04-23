def _match(self, node: torch.fx.Node, ctx: MatchContext):
        m = super()._match(node, ctx)
        if not m:
            return m
        split_sections = node.args[1]
        if not isinstance(split_sections, (list, tuple)):
            return FailedMatch("split not normalized")
        # check users are all unique getitems
        seen_idxs = OrderedSet[int]()
        for user in node.users:
            if not CallFunction(operator.getitem, Arg(), Arg()).match(user):
                # This should ideally never happen. Split user should always be a getitem
                return FailedMatch(f"user of split not a getitem: {user}")
            if not isinstance(user.args[1], int):
                return FailedMatch("only integer getitems are handled")
            if user.args[1] in seen_idxs:
                return FailedMatch(f"duplicate getitem {user.args[1]}")
            if user.args[-1] < 0:  # type: ignore[operator]
                # This shouldn't ideally happen as dynamo normalizes indexes to positive
                return FailedMatch("negative index")
            seen_idxs.add(user.args[1])
        return m