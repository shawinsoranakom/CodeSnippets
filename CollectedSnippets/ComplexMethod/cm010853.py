def __post_init__(self) -> None:
        epilogue_args_idx = list(self.runtime_metadata.mutated_inp_runtime_indices)
        for info in self.runtime_metadata.output_info:
            if (
                info.output_type == OutputType.alias_of_input
                or info.output_type == OutputType.is_input
            ):
                if not isinstance(info.base_idx, int):
                    raise AssertionError(
                        f"expected info.base_idx to be int, got {type(info.base_idx)}"
                    )
                epilogue_args_idx.append(info.base_idx)
        self.epilogue_args_idx = tuple(epilogue_args_idx)

        if config.unlift_effect_tokens:
            if len(self.runtime_metadata.tokens) != 0:
                raise AssertionError(
                    "expected no tokens when unlift_effect_tokens is True, "
                    f"got {len(self.runtime_metadata.tokens)}"
                )

        if self.runtime_metadata.num_outputs_aliased > 0:
            self.output_handlers = tuple(
                make_output_handler(info, self.runtime_metadata, self.trace_joint)
                for info in self.runtime_metadata.output_info
            )
        else:
            self.output_handlers = ()