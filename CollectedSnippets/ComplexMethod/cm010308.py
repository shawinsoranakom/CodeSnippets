def _graph_module_flat_inputs(self, args: Any, kwargs: Any) -> Any:
        """Transform args, kwargs of __call__ to args for graph_module.

        self.graph_module takes stuff from state dict as inputs.
        The invariant is for ep: ExportedProgram is
        ep(args, kwargs) ==
          ep.postprocess(ep.graph_module(ep.graph_module_flat_inputs(args, kwargs)))
        """

        in_spec = self.call_spec.in_spec
        flat_args, received_spec = self._get_flat_args_with_check(args, kwargs)
        if in_spec is not None and not is_equivalent(
            received_spec, in_spec, _fx_collection_equivalence_fn
        ):
            raise ValueError(
                "Trying to flatten user inputs with exported input tree spec: \n"
                f"{in_spec}\n"
                "but actually got inputs with tree spec of: \n"
                f"{received_spec}"
            )

        additional_inputs = []
        for input_ in self.graph_signature.input_specs:
            if input_.kind == InputKind.USER_INPUT:
                continue
            elif input_.kind in (
                InputKind.PARAMETER,
                InputKind.BUFFER,
            ):
                if input_.persistent is False:
                    # This is a non-persistent buffer, grab it from our
                    # constants instead of the state dict.
                    additional_inputs.append(self.constants[input_.target])
                else:
                    additional_inputs.append(self.state_dict[input_.target])
            elif input_.kind in (
                InputKind.CONSTANT_TENSOR,
                InputKind.CUSTOM_OBJ,
            ):
                additional_inputs.append(self.constants[input_.target])
        additional_inputs = tuple(additional_inputs)

        # NOTE: calling convention is first params, then buffers, then args as user supplied them.
        # See: torch/_functorch/aot_autograd.py#L1034
        return additional_inputs + flat_args