async def generate_results(self) -> list[Data]:
        tweaks: dict = {}
        for field in self._attributes:
            if field != "flow_name" and "|" in field:
                [node, name] = field.split("|")
                if node not in tweaks:
                    tweaks[node] = {}
                tweaks[node][name] = self._attributes[field]
        flow_name = self._attributes.get("flow_name")
        run_outputs = await self.run_flow(
            tweaks=tweaks,
            flow_name=flow_name,
            output_type="all",
        )
        data: list[Data] = []
        if not run_outputs:
            return data
        run_output = run_outputs[0]

        if run_output is not None:
            for output in run_output.outputs:
                if output:
                    data.extend(build_data_from_result_data(output))
        return data