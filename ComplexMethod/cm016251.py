def guard_for(arg: SavedAttribute) -> str | None:
            if info is None:
                raise AssertionError("info is None in guard_for")

            # It's hard to determine the edge offset if we have TensorLists
            # NOTE(crcrpar): in-place foreach functions' arguments include tensorlist
            # but their derivatives don't use it, so let them bypass this check.
            if has_tensorlist_arg and (not is_inplace_foreach):
                return None

            # Empirical evaluation of the cases where we insert those guards in
            # backward show that they are somewhat useless. E.g. there's no need
            # to guard on some values captured from forward, because they had to
            # require_grad if the backward function even gets executed. I don't
            # have any good ideas for detecting those cases, so I simply disabled the
            # checks.
            if "backward" in info.name:
                return None

            # If there's a single derivative we could compute, we already have
            # a requires_grad check that is sufficient
            if len(args_with_derivatives) <= 1:
                return None

            # We really only care about trimming down the amount of tensors we save
            if arg.nctype.type != BaseCType(tensorT):
                return None

            # We want to emit simple guards, so we only allow that if checking one
            # input is enough to determine whether we need that value
            used_in = [d for d in info.derivatives if arg in d.saved_inputs]
            if len(used_in) == 0:
                raise AssertionError(f"used_in is empty for arg {arg.nctype.name}")
            if len(used_in) != 1:
                return None
            derivative = used_in[0]

            # Case with multioutput formulas
            # TODO: process all derivative formulas!!!
            if len(derivative.var_names) != 1:
                wrap_opt_if_start = derivative.formula.find(
                    f"wrap_opt_if({arg.nctype.name}"
                )
                if wrap_opt_if_start == -1:
                    return None

                wrap_opt_if_match = re.match(
                    rf"wrap_opt_if\({arg.nctype.name},(.*?)\)",
                    derivative.formula[wrap_opt_if_start:],
                )
                if wrap_opt_if_match is None:
                    raise AssertionError(
                        f"wrap_opt_if_match is None for {arg.nctype.name} in {derivative.formula}"
                    )

                # Condition is between 'wrap_opt_if(var_name,' and ')'.
                condition_slice = slice(len(rf"wrap_opt_if\({arg.nctype.name},"), -1)
                wrap_opt_if_condition = wrap_opt_if_match.group(0)[
                    condition_slice
                ].strip()
                # replace 'grad_input_mask[num]' with 'grad_fn->should_compute_output(num)'
                wrap_opt_if_condition = re.sub(
                    r"grad_input_mask\[(\d+)\]",
                    r"grad_fn->should_compute_output(\1)",
                    wrap_opt_if_condition,
                )
                return f"{wrap_opt_if_condition}"

            # Figure out the offset of the edge that uses this variable
            derivative_var_name = derivative.var_names[0]
            for edge_off, a in enumerate(args_with_derivatives):
                if a.name == derivative_var_name:
                    break
            else:
                raise AssertionError
            return f"grad_fn->should_compute_output({edge_off})"