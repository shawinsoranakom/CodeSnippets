def generate_constraints_node(
        self, n: Node, counter: int
    ) -> tuple[list[Constraint], int]:
        """
        Generate constraints the given node:
        Currently supported operations:
        - Reshape
        - Add
        - conv2d
        """

        if n.op == "placeholder":
            x, counter = gen_tvar(counter)
            self.symbol_dict[n] = x

            my_type = n.type

            if n.type != Dyn and (not isinstance(n.type, TensorType)):
                if n.type == torch.nn.parameter.Parameter:
                    # since we have a parameter, the shape must be static
                    if "example_value" not in n.meta:
                        raise AssertionError("example_value not in n.meta")
                    my_type = TensorType(n.meta["example_value"].size())
                else:
                    my_type = Dyn

            c1 = BinConstraintT(my_type, x, op_precision)
            c2 = BinConstraintT(x, MAX_TENSOR_RANK, op_leq)
            return [c1, c2], counter

        elif n.op == "call_function":
            if n.target in _INFERENCE_RULES:
                return _INFERENCE_RULES[n.target](
                    n, self.symbol_dict, self.constraints, counter
                )
            else:
                raise RuntimeError(
                    f"No inference rule registered for target {n.target}!"
                )

        elif n.op == "call_module":
            module_instance = self.traced.get_submodule(
                n.target  # pyrefly: ignore[bad-argument-type]
            )
            if type(module_instance) in _INFERENCE_RULES:
                return _INFERENCE_RULES[type(module_instance)](
                    n, module_instance, self.symbol_dict, self.constraints, counter
                )
            else:
                raise RuntimeError(
                    f"No inference rule registered for class {type(module_instance)}!"
                )

        elif n.op == "call_method":
            if n.target in _INFERENCE_RULES:
                return _INFERENCE_RULES[n.target](
                    n, self.symbol_dict, self.constraints, counter
                )
            else:
                raise RuntimeError(
                    f"No inference rule registered for target {n.target}!"
                )

        elif n.op == "get_attr":
            t = self.traced_params.get(  # pyrefly: ignore[no-matching-overload]
                n.target, None
            )

            if isinstance(t, torch.Tensor):
                if len(t.shape) > 0:
                    res = list(t.shape)
                    attr_type = TensorType(res)
                    output, counter = gen_tvar(counter)
                    self.symbol_dict[n] = output
                    return [BinConstraintT(output, attr_type, op_eq)], counter
                else:
                    # scalar?
                    return [], counter  # pyrefly: ignore[implicit-any]
            else:
                return [], counter  # pyrefly: ignore[implicit-any]

        elif n.op == "output":
            return [], counter  # pyrefly: ignore[implicit-any]

        else:
            raise NotImplementedError(f"Method {n.op} not yet implemented")