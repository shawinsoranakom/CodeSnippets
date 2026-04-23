def serialize_metadata(self, node: torch.fx.Node) -> dict[str, str]:
        ret = {}

        if stack_trace := node.meta.get("stack_trace"):
            ret["stack_trace"] = stack_trace

        if nn_module_stack := node.meta.get("nn_module_stack"):

            def export_nn_module_stack(val):
                if not isinstance(val, tuple) or len(val) != 2:
                    val_len = len(val) if isinstance(val, tuple) else "N/A"
                    raise AssertionError(
                        f"expected tuple of length 2, got {type(val).__name__} of length {val_len}"
                    )
                path, ty = val

                if not isinstance(path, str):
                    raise AssertionError(
                        f"expected path to be str, got {type(path).__name__}"
                    )
                if not isinstance(ty, str):
                    raise AssertionError(
                        f"expected ty to be str, got {type(ty).__name__}"
                    )

                return path + "," + ty

            # Serialize to "key,orig_path,type_str"
            nn_module_list = [
                f"{k},{export_nn_module_stack(v)}" for k, v in nn_module_stack.items()
            ]
            ret["nn_module_stack"] = ST_DELIMITER.join(nn_module_list)

        if source_fn_st := node.meta.get("source_fn_stack"):
            source_fn_list = [
                f"{source_fn[0]},{self.serialize_operator(source_fn[1])}"
                for source_fn in source_fn_st
            ]
            ret["source_fn_stack"] = ST_DELIMITER.join(source_fn_list)

        if torch_fn := node.meta.get("torch_fn"):
            ret["torch_fn"] = ST_DELIMITER.join(list(torch_fn))

        if custom := node.meta.get("custom"):
            try:
                ret["custom"] = json.dumps(custom)
            except Exception as e:
                raise SerializeError(
                    f"Failed to serialize custom metadata for node {node.name} with error {e}"
                ) from e

        if "from_node" in node.meta:
            from_node = node.meta["from_node"]
            # Serialize from_node as JSON since it's a complex nested structure
            ret["from_node"] = json.dumps(self._serialize_from_node(from_node))

        return ret