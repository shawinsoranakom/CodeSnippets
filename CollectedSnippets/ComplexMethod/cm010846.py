def inner_fn(*args: Any) -> Any:
        # See Note [Disabling Functionalize TLS Above Python Functionalization]
        disable_above = torch._C._ExcludeDispatchKeyGuard(
            torch._C.DispatchKeySet(torch._C.DispatchKey.Functionalize)
        )

        with disable_above:
            # See Note [Side-Effectful Tokens in AOTAutograd]
            if trace_joint:
                if not (isinstance(args, tuple) and isinstance(args[0], (list, tuple))):
                    raise AssertionError(
                        f"expected args to be tuple with first element as list/tuple, got {type(args)}"
                    )
                tokens = args[0][:num_tokens]
                if not all(token.numel() == 0 for token in tokens):
                    raise AssertionError("all tokens must have numel() == 0")
                args = (args[0][num_tokens:], *args[1:])
            else:
                tokens = args[:num_tokens]
                if not all(token.numel() == 0 for token in tokens):
                    raise AssertionError("all tokens must have numel() == 0")
                args = args[num_tokens:]

            # Populate the current FunctionalTensorMode with the tokens per
            # operator. See Note [FunctionalTensorMode is Stateful]
            functional_tensor_mode = torch.utils._python_dispatch._detect_infra_mode(
                torch._C._TorchDispatchModeKey.FUNCTIONAL
            )
            if functional_tensor_mode is None:
                raise AssertionError("functional_tensor_mode must not be None")
            f_tokens = pytree.tree_map(to_fun, tokens)
            for i, k in enumerate(meta.tokens.keys()):
                functional_tensor_mode._tokens[k] = f_tokens[i]

            # Run the joint
            outs, outs_descs = call_and_expect_output_descs(fn, args)

        # Return both the tokens and the outputs
        # See Note [Side-Effectful Tokens in AOTAutograd]
        if trace_joint:
            if len(outs) != 2:
                raise AssertionError(
                    f"expected len(outs) == 2 for joint trace, got {len(outs)}"
                )
            if len(functional_tensor_mode._tokens_forward_output) != num_tokens:
                raise AssertionError(
                    f"expected {num_tokens} forward output tokens, got {len(functional_tensor_mode._tokens_forward_output)}"
                )
            fwd_out_tokens = functional_tensor_mode._tokens_forward_output.values()

            bwd_out_tokens = functional_tensor_mode._tokens.values()

            f_fwd_out_tokens = [from_fun(t) for t in fwd_out_tokens]
            f_bwd_out_tokens = [from_fun(t) for t in bwd_out_tokens]
            f_fwd_out_tokens_descs = [
                ForwardTokenAOTOutput(i) for i in range(len(fwd_out_tokens))
            ]
            f_bwd_out_tokens_descs = [
                BackwardTokenAOTOutput(i) for i in range(len(bwd_out_tokens))
            ]

            meta.num_backward_tokens = len(bwd_out_tokens)
            return (
                ((*f_fwd_out_tokens, *outs[0]), (*outs[1], *f_bwd_out_tokens)),
                (
                    (*f_fwd_out_tokens_descs, *outs_descs[0]),
                    (*outs_descs[1], *f_bwd_out_tokens_descs),
                ),
            )

        out_tokens = [from_fun(t) for t in functional_tensor_mode._tokens.values()]
        # TODO: can probably do a little more resolution here
        out_tokens_descs = [
            ForwardTokenAOTOutput(i)
            for i in range(len(functional_tensor_mode._tokens.values()))
        ]
        return ((*out_tokens, *outs), (*out_tokens_descs, *outs_descs))