async def get(self, node_id):
        if node_id in self.is_changed:
            return self.is_changed[node_id]

        node = self.dynprompt.get_node(node_id)
        class_type = node["class_type"]
        class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
        has_is_changed = False
        is_changed_name = None
        if issubclass(class_def, _ComfyNodeInternal) and first_real_override(class_def, "fingerprint_inputs") is not None:
            has_is_changed = True
            is_changed_name = "fingerprint_inputs"
        elif hasattr(class_def, "IS_CHANGED"):
            has_is_changed = True
            is_changed_name = "IS_CHANGED"
        if not has_is_changed:
            self.is_changed[node_id] = False
            return self.is_changed[node_id]

        if "is_changed" in node:
            self.is_changed[node_id] = node["is_changed"]
            return self.is_changed[node_id]

        # Intentionally do not use cached outputs here. We only want constants in IS_CHANGED
        input_data_all, _, v3_data = get_input_data(node["inputs"], class_def, node_id, None)
        try:
            is_changed = await _async_map_node_over_list(self.prompt_id, node_id, class_def, input_data_all, is_changed_name, v3_data=v3_data)
            is_changed = await resolve_map_node_over_list_results(is_changed)
            node["is_changed"] = [None if isinstance(x, ExecutionBlocker) else x for x in is_changed]
        except Exception as e:
            logging.warning("WARNING: {}".format(e))
            node["is_changed"] = float("NaN")
        finally:
            self.is_changed[node_id] = node["is_changed"]
        return self.is_changed[node_id]