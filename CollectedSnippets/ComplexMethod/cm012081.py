def decide_loop_order_to_match(self, other: "MemoryDep") -> list[int] | None:
        """
        Can return None if not able to decide loop orders.
        """
        assert self.num_vars == other.num_vars

        # ignore broadcast for now since broadcast causes extra 0 strides
        # which makes it hard to decide the correct loop orders.
        if self.num_vars != len(self.index.free_symbols):
            return None
        if other.num_vars != len(other.index.free_symbols):
            return None

        # bail out if any size is 0 or 1
        # For size == 0, it's an empty tensor, any strides for that dimension
        # are equivalent. Skip for simplicity and it may not matter that much.
        #
        # For size == 1, it cause cause tie for strides of different dimensions.
        # Also when we first time create LoopBody in ComputedBuffer.simplify_and_reorder
        # we can dependencies.index_vars_squeeze which should already sqeeuze
        # the size == 1 dimensions.
        if any(s == 0 or s == 1 for s in itertools.chain(self.size, other.size)):
            return None

        # Extract strides for both expression
        self_strides = V.graph.sizevars.stride_hints(self.index, self.var_names)
        other_strides = V.graph.sizevars.stride_hints(other.index, other.var_names)

        # Even if the shape contains no 0/1, some complex index expression may
        # still have duplicate stride values. Here is an example:
        # https://gist.github.com/shunting314/511a7e1ec88aa2e1a8ec85d8445ab129
        # We don't reorder the loop for these cases for now, but in theory
        # we could improve the algorithm to detect the correct loop orders.
        if len(OrderedSet(self_strides)) != len(self_strides) or len(
            OrderedSet(other_strides)
        ) != len(other_strides):
            log.debug(
                "unable to decide loop order. self_dep=%s v.s. other_dep=%s, self_strides=%s v.s. other_strides=%s",
                self,
                other,
                self_strides,
                other_strides,
            )
            return None

        # May happen if self and other are as follows
        # MemoryDep('addmm_6', 393216*d0 + 768*d1 + d2, {d0: 16, d1: 512, d2: 768}, None)
        # MemoryDep('addmm_6', 98304*d0 + d1 + 768*d2, {d0: 64, d1: 768, d2: 128}, None)
        if OrderedSet(self_strides) != OrderedSet(other_strides):
            return None

        stride_to_index = {s: i for i, s in enumerate(self_strides)}
        order = [stride_to_index[s] for s in other_strides]

        assert OrderedSet(order) == OrderedSet(range(self.num_vars))
        return order