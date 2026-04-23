async def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        await logger.adebug(f"Updating build config with field value {field_value} and field name {field_name}")
        if field_name == "flow_name":
            build_config["flow_name"]["options"] = await self.get_flow_names()
        # Clean up the build config
        for key in list(build_config.keys()):
            if key not in {*self.field_order, "code", "_type", "get_final_results_only"}:
                del build_config[key]
        if field_value is not None and field_name == "flow_name":
            try:
                flow_data = await self.get_flow(field_value)
            except Exception:  # noqa: BLE001
                await logger.aexception(f"Error getting flow {field_value}")
            else:
                if not flow_data:
                    msg = f"Flow {field_value} not found."
                    await logger.aerror(msg)
                else:
                    try:
                        graph = Graph.from_payload(flow_data.data["data"])
                        # Get all inputs from the graph
                        inputs = get_flow_inputs(graph)
                        # Add inputs to the build config
                        build_config = self.add_inputs_to_build_config(inputs, build_config)
                    except Exception:  # noqa: BLE001
                        await logger.aexception(f"Error building graph for flow {field_value}")

        return build_config