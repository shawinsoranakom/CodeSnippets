def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Use the tool."""
        args_names = get_arg_names(self.inputs)
        if len(args_names) == len(args):
            kwargs = {arg["arg_name"]: arg_value for arg, arg_value in zip(args_names, args, strict=True)}
        elif len(args_names) != len(args) and len(args) != 0:
            msg = "Number of arguments does not match the number of inputs. Pass keyword arguments instead."
            raise ToolException(msg)
        tweaks = {arg["component_name"]: kwargs[arg["arg_name"]] for arg in args_names}

        run_outputs = run_until_complete(
            run_flow(
                graph=self.graph,
                tweaks={key: {"input_value": value} for key, value in tweaks.items()},
                flow_id=self.flow_id,
                user_id=self.user_id,
                session_id=self.session_id,
            )
        )
        if not run_outputs:
            return "No output"
        run_output = run_outputs[0]

        data = []
        if run_output is not None:
            for output in run_output.outputs:
                if output:
                    data.extend(build_data_from_result_data(output))
        return format_flow_output_data(data)