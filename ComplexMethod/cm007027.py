async def build_tool(self) -> Tool:
        FlowTool.model_rebuild()
        if "flow_name" not in self._attributes or not self._attributes["flow_name"]:
            msg = "Flow name is required"
            raise ValueError(msg)
        flow_name = self._attributes["flow_name"]
        flow_data = await self.get_flow(flow_name)
        if not flow_data:
            msg = "Flow not found."
            raise ValueError(msg)
        graph = Graph.from_payload(
            flow_data.data["data"],
            user_id=str(self.user_id),
        )
        try:
            graph.set_run_id(self.graph.run_id)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to set run_id", exc_info=True)
        inputs = get_flow_inputs(graph)
        tool_description = self.tool_description.strip() or flow_data.description
        tool = FlowTool(
            name=self.tool_name,
            description=tool_description,
            graph=graph,
            return_direct=self.return_direct,
            inputs=inputs,
            flow_id=str(flow_data.id),
            user_id=str(self.user_id),
            session_id=self.graph.session_id if hasattr(self, "graph") else None,
        )
        description_repr = repr(tool.description).strip("'")
        args_str = "\n".join([f"- {arg_name}: {arg_data['description']}" for arg_name, arg_data in tool.args.items()])
        self.status = f"{description_repr}\nArguments:\n{args_str}"
        return tool