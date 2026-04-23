def forward(self, *args, **kwargs):
        if self.graph_module is None:
            raise AssertionError("Didn't finalize this InterpreterModule")
        if not is_fx_symbolic_tracing() and (
            torch.compiler.is_dynamo_compiling() or not self._run_with_interpreter
        ):
            # Dynamo cannot trace through torch.fx.Interpreter, so fall back to
            # GraphModule codegen in this instance.
            # Patch the codegened forward to run with this InterpreterModule,
            # so attribute accesses, etc. are on this module instead.
            return type(self.graph_module).forward(self, *args, **kwargs)
        else:
            if kwargs:
                # Handle **kwargs. FX only natively supports positional
                # arguments (through placeholders). So in order to pass in
                # kwargs, we must correspond the names of the placeholders with
                # the keys in the kwarg dict.
                arg_list = list(args)
                kwarg_names = self.arg_names[len(arg_list) :]
                arg_list.extend(
                    kwargs[kwarg_name]
                    for kwarg_name in kwarg_names
                    if kwarg_name in kwargs
                )

                # Assert that the kwargs passed in exactly match the positional
                # arguments specified by the GraphModule. This should be
                # guaranteed by the unflattening process.
                if len(kwarg_names) != len(kwargs):
                    raise AssertionError(
                        f"kwarg_names length {len(kwarg_names)} does not match kwargs length {len(kwargs)}"
                    )
                if len(arg_list) != len(self.arg_names):
                    raise AssertionError(
                        f"arg_list length {len(arg_list)} does not match arg_names length {len(self.arg_names)}"
                    )
                args = tuple(arg_list)

            return torch.fx.Interpreter(self, graph=self.graph).run(
                *args, enable_io_processing=False
            )