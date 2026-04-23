def __init__(
        self,
        m: torch.fx.GraphModule,
        flat_args: list[Any],
        matched_input_elements_positions: list[int],
        flat_results: Sequence[Any],
        matched_output_elements_positions: list[int],
        example_fake_inputs: list[torch.Tensor],
        flat_args_dynamic_dims: list[set[int]],
        fake_mode: fake_tensor.FakeTensorMode | None = None,
    ) -> None:
        super().__init__(m)

        assert len(flat_args_dynamic_dims) == len(flat_args)
        matched_input_elements_to_fake = {
            val: example_fake_inputs[ix]
            for ix, val in enumerate(matched_input_elements_positions)
        }

        self.new_args = []
        for i in range(len(flat_args)):
            arg = super().placeholder(f"arg{i}", (), {})
            if i in matched_input_elements_to_fake:
                arg.node.meta["val"] = matched_input_elements_to_fake[i]
            else:
                # Fill node.meta["val"] with faketensor from the input,
                # if it's not found in matched_input_elements_positions
                if fake_mode is not None and isinstance(flat_args[i], torch.Tensor):
                    # TODO(zhxchen17) Also preserve all the user constraints here.
                    arg.node.meta["val"] = fake_mode.from_tensor(
                        flat_args[i],
                        symbolic_context=StatelessSymbolicContext(
                            dynamic_sizes=[
                                (
                                    DimDynamic.DYNAMIC
                                    if d in flat_args_dynamic_dims[i]
                                    else DimDynamic.STATIC
                                )
                                for d in range(len(flat_args[i].shape))
                            ],
                            constraint_sizes=[None] * len(flat_args[i].shape),
                        ),
                    )
                elif isinstance(flat_args[i], _IntWrapper):
                    arg.node.meta["val"] = flat_args[i].val
                else:
                    arg.node.meta["val"] = flat_args[i]

            self.new_args.append(arg)
        self.old_args_gen = (self.new_args[i] for i in matched_input_elements_positions)
        self.matched_output_elements_positions = matched_output_elements_positions
        self.flat_results = flat_results