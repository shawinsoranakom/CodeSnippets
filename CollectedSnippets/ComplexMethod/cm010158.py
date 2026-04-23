def _check_prim_loop_support(self, node):
        inputs = list(node.inputs())

        # TODO: (1/N) stage.
        if inputs[0].debugName() not in self.name_to_constant:
            raise RuntimeError(
                "prim::Loop currently cannot run with dynamic value of number of iterations."
            )

        # Make sure the condition is not updated in the subblock.
        subblock = next(node.blocks())
        condition_output_name = next(subblock.outputs()).debugName()
        for node in subblock.nodes():
            if (
                node.outputsSize() == 1
                and node.output().debugName() == condition_output_name
            ):
                raise RuntimeError(
                    "prim::Loop currently cannot run with dynamic value of condition."
                )
            if node.outputsSize() >= 2:
                for outp in node.outputs():
                    if outp.debugName() == condition_output_name:
                        raise RuntimeError(
                            "prim::Loop currently cannot run with dynamic value of condition."
                        )