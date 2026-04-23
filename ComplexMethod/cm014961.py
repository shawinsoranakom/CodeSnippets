def try_resolve_aten_out_overload(ol, args, kwargs, num_outputs):

        ol_args = ol._schema.arguments
        olp: OpOverloadPacket = ol._overloadpacket

        if olp in MetaCrossRefDispatchMode.aten_olp_no_out_overload:
            return (None, None, None)

        candidate_ols = []
        for candidate_ol_name in olp.overloads():
            candidate_ol = getattr(olp, candidate_ol_name)
            if any(arg.is_out for arg in candidate_ol._schema.arguments):
                candidate_ols.append(candidate_ol)

        if not candidate_ols:
            MetaCrossRefDispatchMode.aten_olp_no_out_overload.add(olp)
            return (None, None, None)

        # Now match based on args, kwargs and number of required outputs
        candidate_ol: OpOverload = None
        for candidate_ol in candidate_ols:
            candidate_ol_args = candidate_ol._schema.arguments

            if (len(args) >= len(candidate_ol_args)):
                continue

            # Positional arguments must have the same type
            if not all(
                ol_args[pos_arg_ind].type == candidate_ol_args[pos_arg_ind].type
                for pos_arg_ind in range(len(args))
            ):
                continue

            # Number of outputs must match
            candidate_out_names = [out_arg.name for out_arg in candidate_ol_args[-num_outputs:] if out_arg.is_out]
            if len(candidate_out_names) != num_outputs:
                continue

            # Now try and match kwargs. Just need to ensure that the
            # remaining kwargs allow an out overload to be called. For example
            # we can throw away parameters like `dtype` that may be passed to the
            # functional version of the op since the `dtype` will already be present
            # in the `out` argument
            new_kwargs = {}
            kwargs_match = True
            for arg in candidate_ol_args[len(args):-num_outputs]:
                if arg.name not in kwargs:
                    if arg.has_default_value():
                        new_kwargs[arg.name] = arg.default_value
                    elif isinstance(arg.type, torch.OptionalType):
                        if isinstance(arg.type.getElementType(), torch.BoolType):
                            new_kwargs[arg.name] = False
                        else:
                            new_kwargs[arg.name] = None
                    else:
                        kwargs_match = False
                        break
                else:
                    new_kwargs[arg.name] = kwargs[arg.name]

            if kwargs_match:
                return candidate_ol, candidate_out_names, new_kwargs

        return None, None, None