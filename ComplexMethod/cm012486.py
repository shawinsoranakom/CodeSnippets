def codegen_while_loop(self, while_loop, stack_output):
        """while_loop is codegened as a host side while_loop"""

        def codegen_subgraph(subgraph, outer_inputs, outer_outputs):
            """Helper method to deduplicate subgraph codegen logic"""
            if V.graph.aot_mode:
                self.codegen_subgraph_by_inlining(subgraph, outer_inputs, outer_outputs)
            else:
                self.codegen_subgraph_with_flattened_outputs(
                    subgraph, outer_inputs, outer_outputs
                )

        name = while_loop.get_name()
        outer_carried_inputs = [
            buf.codegen_reference() for buf in while_loop.carried_inputs
        ]
        outer_additional_inputs = [
            buf.codegen_reference() for buf in while_loop.additional_inputs
        ]

        ckp_offset = len(outer_carried_inputs)
        self.writeline(f"{name} = [None] * {len(outer_carried_inputs)}")
        if stack_output:
            self.writeline(
                f"{name}.extend([[] for _ in range({len(outer_carried_inputs)})])"
            )

        for i, inp in enumerate(outer_carried_inputs):
            # set the initial state before the loop
            self.writeline(f"{name}[{i}] = {inp}")

        cond_outer_inputs = [
            *[f"{name}[{i}]" for i in range(len(outer_carried_inputs))],
            *outer_additional_inputs,
        ]
        cond_outer_outputs = [f"{name}_cond_result"]
        body_outer_inputs = list(
            cond_outer_inputs
        )  # same inputs for cond_fn and body_fn
        # Carry over the state from body_fn. Note: We only carry over
        # the carried_inputs part of the inputs, the additional ones
        # are passed in as they're before.
        body_outer_outputs = body_outer_inputs[: len(outer_carried_inputs)]
        # Check condition at the beginning and set up flag
        codegen_subgraph(
            while_loop.cond_subgraph, cond_outer_inputs, cond_outer_outputs
        )
        self.writeline(f"should_loop = {cond_outer_outputs[0]}")
        self.writeline("if not should_loop:")
        if stack_output:
            # Handle the case when loop never executes
            for i, carried_input in enumerate(outer_carried_inputs):
                self.writeline(EnterSubgraphLine(self, while_loop.body_subgraph.graph))
                self.writeline(f"{name}[{i}] = {carried_input}.unsqueeze(0).clone()")
                self.writeline(ExitSubgraphLine(self))
        else:
            for i, carried_input in enumerate(outer_carried_inputs):
                self.writeline(EnterSubgraphLine(self, while_loop.body_subgraph.graph))
                self.writeline(f"{name}[{i}] = {carried_input}.clone()")
                self.writeline(ExitSubgraphLine(self))

        self.writeline("while should_loop:")
        # Body execution
        self.writeline(EnterSubgraphLine(self, while_loop.body_subgraph.graph))
        codegen_subgraph(
            while_loop.body_subgraph, body_outer_inputs, body_outer_outputs
        )
        self.writeline(ExitSubgraphLine(self))

        # Collect outputs if enabled
        if stack_output:
            self.writeline(EnterSubgraphLine(self, while_loop.body_subgraph.graph))
            for i in range(len(outer_carried_inputs)):
                self.writeline(f"{name}[{i + ckp_offset}].append({name}[{i}])")
            self.writeline(ExitSubgraphLine(self))

        # Condition check at end of loop
        self.writeline(EnterSubgraphLine(self, while_loop.cond_subgraph.graph))
        codegen_subgraph(
            while_loop.cond_subgraph, cond_outer_inputs, cond_outer_outputs
        )
        self.writeline(ExitSubgraphLine(self))
        self.writeline(f"    should_loop = {cond_outer_outputs[0]}")

        # Stack outputs after loop completion
        if stack_output:
            self.writeline("# Stack outputs after loop completion")
            for i in range(len(outer_carried_inputs)):
                self.writeline(f"if len({name}[{i + ckp_offset}]) > 0:")
                self.writeline(EnterSubgraphLine(self, while_loop.body_subgraph.graph))
                self.writeline(
                    f"{name}[{i}] = torch.stack({name}[{i + ckp_offset}], dim=0)"
                )
                self.writeline(ExitSubgraphLine(self))