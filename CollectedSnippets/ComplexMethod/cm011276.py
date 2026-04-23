def forward(self, *args, **kwargs):
        executor_args = args
        if len(kwargs) > 0:
            parameters = []
            for node in self.split_gm.graph.nodes:
                if node.op == "placeholder":
                    if node.args and len(node.args) > 0:
                        parameters.append(
                            Parameter(
                                node.target,
                                Parameter.POSITIONAL_OR_KEYWORD,
                                default=node.args[0],
                            )
                        )
                    else:
                        parameter_kind = Parameter.POSITIONAL_OR_KEYWORD
                        param_name = node.target
                        if node.target.startswith("**"):
                            parameter_kind = Parameter.VAR_KEYWORD  # type: ignore[assignment]
                            param_name = param_name[2:]
                        elif node.target.startswith("*"):
                            parameter_kind = Parameter.VAR_POSITIONAL  # type: ignore[assignment]
                            param_name = param_name[1:]
                        parameters.append(Parameter(param_name, parameter_kind))
            signature = Signature(parameters)
            ba = signature.bind(*args, **kwargs)
            ba.apply_defaults()
            executor_args = ba.arguments.values()  # type: ignore[assignment]

        res = self.executor.run(*executor_args)

        return res