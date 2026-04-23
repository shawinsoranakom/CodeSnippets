async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Use the tool asynchronously."""
        tweaks = self.build_tweaks_dict(args, kwargs)
        try:
            run_id = self.graph.run_id if hasattr(self, "graph") and self.graph else None
        except Exception:  # noqa: BLE001
            logger.warning("Failed to set run_id", exc_info=True)
            run_id = None
        run_outputs = await run_flow(
            tweaks={key: {"input_value": value} for key, value in tweaks.items()},
            flow_id=self.flow_id,
            user_id=self.user_id,
            run_id=run_id,
            session_id=self.session_id,
            graph=self.graph,
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