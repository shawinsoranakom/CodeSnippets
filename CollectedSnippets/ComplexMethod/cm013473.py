def run(self, shape_env: ShapeEnv | None = None) -> Any:
        from torch.fx.experimental.symbolic_shapes import (
            is_symbolic,
            ShapeEnv,
            SymTypes,
        )

        # Special handling for the constructor event.
        if self.f is ShapeEnv:
            if not (
                shape_env is None and self.args is None and self.kwargs is not None
            ):
                raise AssertionError(
                    "ShapeEnv constructor requires shape_env=None, args=None, kwargs set"
                )
            return ShapeEnv(**self.kwargs)

        if shape_env is None:
            raise AssertionError("shape_env is required for non-constructor events")
        args = list(self.args or [])
        kwargs = dict(self.kwargs or {})

        # Replace any argument of type ShapeEnv by the given one.
        args, kwargs = pytree.tree_map_only(
            ShapeEnv, lambda _: shape_env, (args, kwargs)
        )

        # Replace any argument of type SymTypes by a new instance,
        # replacing its ShapeEnv reference.
        args, kwargs = pytree.tree_map_only(
            lambda x: isinstance(x, SymTypes) and is_symbolic(x),
            lambda a: type(a)(a.node.with_shape_env(shape_env)),
            (args, kwargs),
        )

        # Converts FX nodes using the mapping argument.
        def maybe_convert_node(x: Any) -> Any:
            if not isinstance(x, torch.fx.Node):
                # Don't do anything to x if it's not an FX node.
                return x

            # If, at some point, we created an FX node, it means that translation validation is on.
            # It also means we are building an FX graph for symbolic shapes at shape_env.graph, and
            # we are tracking node names at shape_env.name_to_node.
            if not hasattr(shape_env, "name_to_node"):
                raise AssertionError("shape_env missing name_to_node attribute")
            name_to_node = shape_env.name_to_node  # type: ignore[attr-defined]
            if x.name not in name_to_node:
                raise AssertionError(f"Node {x.name} not found in name_to_node")
            return name_to_node[x.name]

        # Replaces the value of an specific argument by the result of fn.
        def replacearg(index: int, key: str, fn: Callable[..., Any]) -> None:
            if index < len(args):
                args[index] = fn(args[index])
            if key in kwargs:
                kwargs[key] = fn(kwargs[key])

        if self.is_create_fx_call_function():
            # ShapeEnv.create_fx_call_function:
            # "args" parameter is a tuple of FX nodes from the FX graph of the old ShapeEnv.
            # They must be replaced, since a "call_function" FX node with this tuple as argument
            # will be added to the FX graph of the new shape_env.
            replacearg(
                index=2,
                key="args",
                fn=lambda args: tuple(maybe_convert_node(a) for a in args),
            )
        if self.is_evaluate_expr() or self.is_defer_runtime_assert():
            # ShapeEnv.evaluate_expr and ShapeEnv.guard_or_defer_runtime_assert:
            # "fx_node" parameter is an (optional) FX node that represents the evaluate expression.
            # They must be replaced, since it will be part of a "call_function" FX node for
            # torch._assert, which will be added to the FX graph of the new shape_env.
            replacearg(index=3, key="fx_node", fn=maybe_convert_node)

        # Actually call the method with the converted arguments.
        return self.f(*args, **kwargs)