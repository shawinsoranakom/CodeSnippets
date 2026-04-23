def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        ptr = kwargs["ptr"] if "ptr" in kwargs else args[0]

        if not isinstance(ptr, variables.DataPtrVariable):
            unimplemented(
                gb_type="invalid ptr argument for create_tma_descriptor",
                context=f"args = {args}, kwargs = {kwargs}",
                explanation=f"Expected `ptr` argument of `create_{self.rank}d_tma_descriptor`"
                "to be from a `.data_ptr()` call, represented internally by `DataPtrVariable`",
                hints=[
                    "`torch.compile` may fail to internally represent result of `.data_ptr()` "
                    "with `DataPtrVariable` due to a graph break between the `.data_ptr()` call and "
                    f"`create_{self.rank}d_tma_descriptor`. Please ensure there were no graph breaks "
                    "between these two calls.",
                ],
            )

        if self.rank == 1:
            if len(args) + len(kwargs) != 4:
                raise_type_error(
                    tx,
                    f"TMA metadata rank=1 requires exactly 4 arguments, got {len(args) + len(kwargs)}",
                )
            dims = [
                kwargs["dim"] if "dim" in kwargs else args[1],
            ]
            block_dims = [
                kwargs["block_dim"] if "block_dim" in kwargs else args[2],
            ]
        else:
            if len(args) + len(kwargs) != 6:
                raise_type_error(
                    tx,
                    f"TMA metadata rank=2 requires exactly 6 arguments, got {len(args) + len(kwargs)}",
                )
            dims = [
                kwargs["dim1"] if "dim1" in kwargs else args[1],
                kwargs["dim0"] if "dim0" in kwargs else args[2],
            ]
            block_dims = [
                kwargs["block_dim1"] if "block_dim1" in kwargs else args[3],
                kwargs["block_dim0"] if "block_dim0" in kwargs else args[4],
            ]
        element_size = kwargs["element_size"] if "element_size" in kwargs else args[-1]

        # to make pyrefy happy
        assert isinstance(ptr, variables.DataPtrVariable)

        return TMADescriptorExperimentalVariable(
            data_ptr=ptr,
            dims=dims,
            block_dims=block_dims,
            element_size=element_size,
        )