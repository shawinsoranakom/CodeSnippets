def _get_example_val(self, ty: str):
        from torch.fx.experimental.sym_node import SymNode
        from torch.fx.experimental.symbolic_shapes import ShapeEnv

        def create_symtype(cls, pytype, shape_env, val):
            from torch._dynamo.source import ConstantSource

            symbol = shape_env.create_symbol(
                val,
                source=ConstantSource(
                    f"__testing_hop_schema{len(shape_env.backed_var_to_val)}"
                ),
            )
            return cls(SymNode(symbol, shape_env, pytype, hint=val))

        if ty == "bool":
            return True
        elif ty == "int":
            return 1
        elif ty == "float":
            return 1.0
        elif ty == "str":
            return "foo"
        elif ty == "Tensor":
            return torch.tensor(1)
        elif ty == "SymInt":
            shape_env = ShapeEnv()
            return create_symtype(torch.SymInt, int, shape_env, 1)
        elif ty == "SymBool":
            shape_env = ShapeEnv()
            return create_symtype(torch.SymBool, bool, shape_env, True)
        elif ty == "GraphModule":

            def f(x):
                return x.sin()

            return make_fx(f)(torch.ones(1))
        elif ty == "ScriptObj":
            from torch.testing._internal.torchbind_impls import (
                init_torchbind_implementations,
            )

            init_torchbind_implementations()
            foo = torch.classes._TorchScriptTesting._Foo(3, 4)
            return foo
        else:
            raise NotImplementedError(ty)