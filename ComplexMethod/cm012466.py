def codegen_iteration_ranges_entry(self, entry: IterationRangesEntry) -> None:
        index_expr = self.rename_indexing(entry.expr)
        index_str = self.sexpr(index_expr)  # type: ignore[misc]

        if not entry.is_reduction or (
            isinstance(entry.root.numel, sympy.Integer)
            and entry.root.numel <= self.max_threadgroup_size
        ):
            self.indexing_code.writeline(
                f"{self.index_dtype} {entry.name} = {index_str};"
            )
            return

        acc_size = (
            entry.root.numel
            if isinstance(entry.root.numel, sympy.Integer)
            else sympy.Symbol(f"{entry.root.prefix}numel", integer=True, positive=True)
        )

        # Check if we've already generated a loop for this reduction root
        root_already_processed = any(
            e.root is entry.root for e in self.multistage_reduction_entry
        )

        linear_idx_name = f"{entry.root.prefix}_linear_idx"

        if not root_already_processed:
            self.multistage_reduction_entry.append(entry)
            # When reducing the tensor whose size exceeds max threadgroup size
            # loop over extra indices per reduction thread and perform part of the operation
            # using values in the shared memory

            # Use floats so that it doesn't do integer division
            loop_size = (acc_size + float(self.max_threadgroup_size - 1)) // float(
                self.max_threadgroup_size
            )
            loop_size_str = self.sexpr(loop_size)

            root_name = entry.root.name

            self.body.writeline(
                f"for(auto {entry.root.prefix}_cnt = 0; {entry.root.prefix}_cnt < {loop_size_str}; ++{entry.root.prefix}_cnt) {{"
            )
            with self.body.indent():
                if isinstance(acc_size, sympy.Symbol):
                    self.body.writeline(
                        f"{self.index_dtype} {linear_idx_name} = "
                        f"{self.max_threadgroup_size} * {entry.root.prefix}_cnt + {root_name};"
                    )
                else:
                    self.body.writeline(
                        f"{self.index_dtype} {linear_idx_name} = {loop_size_str} * {root_name} + {entry.root.prefix}_cnt;"
                    )

                # Check that reduction is performed only within tensor boundary
                if (
                    isinstance(acc_size, sympy.Symbol)
                    or loop_size * self.max_threadgroup_size != acc_size
                ):
                    self.body.writeline(f"if ({linear_idx_name} >= {acc_size}) break;")

                # Compute entry value from linear index by substituting root name
                sub_index_str = index_str.replace(entry.root.name, linear_idx_name)
                self.body.writeline(
                    f"{self.index_dtype} {entry.name} = {sub_index_str};"
                )
        else:
            # root is already processed so just need to compute this entry's value inside the existing loop
            with self.body.indent():
                sub_index_str = index_str.replace(entry.root.name, linear_idx_name)
                self.body.writeline(
                    f"{self.index_dtype} {entry.name} = {sub_index_str};"
                )