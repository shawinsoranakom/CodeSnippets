def deserialize_metadata(self, metadata: dict[str, str]) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if stack_trace := metadata.get("stack_trace"):
            ret["stack_trace"] = stack_trace

        def deserialize_meta_func(serialized_target: str):
            module = None
            if serialized_target.startswith("torch.nn"):
                module = torch.nn
                serialized_target_names = serialized_target.split(".")[2:]
            elif serialized_target.startswith("torch"):
                module = torch
                serialized_target_names = serialized_target.split(".")[1:]
            else:
                return self.deserialize_operator(serialized_target)

            target = module
            for name in serialized_target_names:
                if not hasattr(target, name):
                    return serialized_target
                else:
                    target = getattr(target, name)
            return target

        if nn_module_stack_str := metadata.get("nn_module_stack"):
            # Originally serialized to "key,orig_path,type_str"
            def import_nn_module_stack(key, path, ty):
                return key, (path, ty)

            # Helper function to split string by commas, accounting for nested parentheses/brackets
            def metadata_split(metadata):
                out = []
                start, n = 0, 0
                a, b = "[(", ")]"
                for end, c in enumerate(metadata):
                    if c in a:
                        n += 1
                    elif c in b:
                        n -= 1
                    elif c == "," and n == 0:
                        out.append(metadata[start:end])
                        start = end + 1
                out.append(metadata[start:])
                if len(out) != 3:
                    raise AssertionError(
                        f"expected metadata_split to return 3 parts, got {len(out)}"
                    )
                return out

            nn_module_stack = dict(
                import_nn_module_stack(*metadata_split(item))
                for item in nn_module_stack_str.split(ST_DELIMITER)
            )
            ret["nn_module_stack"] = nn_module_stack

        if source_fn_st_str := metadata.get("source_fn_stack"):
            # Originally serializes to "fx_node_name,op_str"
            source_fn_st = []
            for source_fn_str in source_fn_st_str.split(ST_DELIMITER):
                name, target_str = source_fn_str.split(",")
                source_fn_st.append((name, deserialize_meta_func(target_str)))
            ret["source_fn_stack"] = source_fn_st

        if torch_fn_str := metadata.get("torch_fn"):
            ret["torch_fn"] = tuple(torch_fn_str.split(ST_DELIMITER))

        if custom_str := metadata.get("custom"):
            ret["custom"] = json.loads(custom_str)

        if from_node_str := metadata.get("from_node"):
            ret["from_node"] = self._deserialize_from_node(json.loads(from_node_str))

        return ret