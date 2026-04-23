async def update_build_config(
        self,
        build_config: dotdict,
        field_value: Any,
        field_name: str | None = None,
    ):
        missing_keys = [key for key in self.default_keys if key not in build_config]
        for key in missing_keys:  # TODO: create a defaults dict to avoid hardcoding the defaults here
            if key == "flow_name_selected":
                build_config[key] = {"options": [], "options_metadata": [], "value": None}
            elif key == "flow_id_selected":
                build_config[key] = {"value": None}
            elif key == "cache_flow":
                build_config[key] = {"value": False}
            else:
                build_config[key] = {}
        if field_name == "flow_name_selected" and (build_config.get("is_refresh", False) or field_value is None):
            # refresh button was clicked or componented was initialized, so list the flows
            options: list[str] = await self.alist_flows_by_flow_folder()
            build_config["flow_name_selected"]["options"] = [flow.data["name"] for flow in options]
            build_config["flow_name_selected"]["options_metadata"] = []
            for flow in options:
                # populate options_metadata
                build_config["flow_name_selected"]["options_metadata"].append(
                    {"id": flow.data["id"], "updated_at": flow.data["updated_at"]}
                )
                # update selected flow if it is stale
                if str(flow.data["id"]) == self.flow_id_selected:
                    await self.check_and_update_stale_flow(flow, build_config)
        elif field_name in {"flow_name_selected", "flow_id_selected"} and field_value is not None:
            # flow was selected by name or id, so get the flow and update the bcfg
            try:
                # derive flow id if the field_name is flow_name_selected
                build_config["flow_id_selected"]["value"] = (
                    self.get_selected_flow_meta(build_config, "id") or build_config["flow_id_selected"]["value"]
                )
                updated_at = self.get_selected_flow_meta(build_config, "updated_at")
                await self.load_graph_and_update_cfg(
                    build_config, build_config["flow_id_selected"]["value"], updated_at
                )
            except Exception as e:
                msg = f"Error building graph for flow {field_value}"
                await logger.aexception(msg)
                raise RuntimeError(msg) from e

        return build_config