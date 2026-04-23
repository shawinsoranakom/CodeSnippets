def add_arg(idx, arg, is_constexpr=False, equals_1=False, equals_none=False):
            if is_constexpr:
                if triton_version_uses_attrs_dict():
                    # tl.constexpr args appear in the signature in new versions of triton,
                    # but not in old versions of triton.
                    add_to_signature(idx, arg)

                if arg.name in kwargs:
                    # the arg may not appear in kwargs if it is an autotuned arg.
                    # in this case, it will be added in triton_heuristics after autotuning.
                    constants[arg.name] = kwargs[arg.name]

            else:
                # the only case where arg name isn't in kwargs, should be
                # when the arg is a constexpr.
                assert arg.name in kwargs

                if equals_1:
                    if triton_version_uses_attrs_dict():
                        # new versions of triton: add the equal-to-1 arg in the signature (labeled as "constexpr"),
                        #                         and add the arg as a constant.
                        # new versions of triton: add the equal-to-1 arg in the signature (labeled as, e.g., "i32"),
                        #                         and add the arg as a constant.
                        add_to_signature(idx, ConstexprArg(name=arg.name))
                    else:
                        add_to_signature(idx, arg)
                    constants[arg.name] = 1
                elif equals_none:
                    if triton_version_uses_attrs_dict():
                        # new versions of triton: add the none arg in the signature (as a constexpr arg) and as a constant
                        # old versions of triton: include the none arg as a constant (but not in the signature)
                        add_to_signature(idx, ConstexprArg(name=arg.name))
                    constants[arg.name] = None
                else:
                    add_to_signature(idx, arg)