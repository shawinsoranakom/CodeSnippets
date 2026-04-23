def benchmark_compiled_module(self, output):
        """Write out codegen for benchmarking the output code"""

        def add_fake_input(name, shape, stride, device, dtype):
            output.writeline(
                f"{name} = rand_strided("
                f"{self.codegen_python_shape_tuple(shape)}, "
                f"{self.codegen_python_shape_tuple(stride)}, "
                f"device='{device}', dtype={dtype})"
            )

        def add_expr_input(name, val):
            output.writeline(f"{name} = {val}")

        def add_torchbind_input(name, value):
            if value is None:
                output.writeline(f"{name} = None")
                return

            import pickle

            try:
                output.writeline(f"{name} = pickle.loads({pickle.dumps(value)!r})")
            except (TypeError, AttributeError, pickle.PicklingError) as e:
                output.writeline(
                    f'raise TypeError("Failed to pickle opaque type {type(value)} for variable {name}: {str(e)}")'
                )

        # Generate get_args() to create input tensors separately from benchmarking
        output.writelines(["", "", "def get_args():"])
        with output.indent():
            output.splice(
                """
                from torch._dynamo.testing import rand_strided
                """,
                strip=True,
            )

            for name, value in V.graph.constants.items():
                # all the constants are global variables, that's why we need
                # these 'global var_name' lines
                output.writeline(f"global {name}")
                add_fake_input(
                    name, value.size(), value.stride(), value.device, value.dtype
                )

            if len(V.graph.torchbind_constants) > 0:
                output.writeline("import pickle")
                for name, torchbind_obj in V.graph.torchbind_constants.items():
                    # all the constants are global variables, that's why we need
                    # these 'global var_name' lines
                    output.writeline(f"global {name}")
                    add_torchbind_input(name, torchbind_obj)

            for name, value in V.graph.graph_inputs.items():
                if isinstance(value, sympy.Symbol) and isinstance(
                    V.graph.sizevars.backed_var_to_val.get(value, None), SingletonInt
                ):
                    # Inductor should only work with dense -> dense graph, and
                    # SingletonInts belong to metadata that should only live on
                    # the subclass.
                    continue
                if isinstance(value, ir.TorchBindObject):
                    output.writeline(f"{name} = None")
                elif isinstance(value, sympy.Expr):  # Don't need to add symbolic
                    # TODO: this fallback and those below actually will generate possibly
                    # invalid benchmark code, because it's not guaranteed 42
                    # is actually a valid value for the kernel in question.
                    # See https://github.com/pytorch/pytorch/issues/124686
                    add_expr_input(
                        name, V.graph.sizevars.optimization_hint(value, fallback=42)
                    )
                elif isinstance(value, sympy.Basic):
                    # sympy.Boolean (e.g. StrictLessThan from torch.cond predicates)
                    # is not a sympy.Expr so optimization_hint cannot handle it.
                    # Use False as a fallback for benchmark harness purposes.
                    add_expr_input(name, False)
                elif isinstance(value, ir.GeneratorState):
                    add_expr_input(
                        name,
                        f"torch.cuda.default_generators[{value.device.index}].graphsafe_get_state()",
                    )
                elif isinstance(value, ir.OpaqueObjectState):
                    output.writeline(f"{name} = None")
                else:
                    shape = V.graph.sizevars.optimization_hints(
                        value.get_size(), fallback=42
                    )
                    stride = V.graph.sizevars.optimization_hints(
                        value.get_stride(), fallback=42
                    )

                    add_fake_input(
                        name,
                        shape,
                        stride,
                        value.get_device(),
                        value.get_dtype(),
                    )

            output.writeline(f"return [{', '.join(V.graph.graph_inputs.keys())}]")

        # Generate benchmark_compiled_module() that takes args as parameter
        output.writelines(
            ["", "", "def benchmark_compiled_module(args, times=10, repeat=10):"]
        )
        with output.indent():
            output.splice(
                """
                from torch._inductor.utils import print_performance
                fn = lambda: call(list(args))
                return print_performance(fn, times=times, repeat=repeat)
                """,
                strip=True,
            )