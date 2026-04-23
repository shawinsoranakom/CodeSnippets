def test_template_field_order_matches_component(self, template_file):
        """Test that field_order in starter project JSON matches the actual component's input order."""
        with template_file.open(encoding="utf-8") as f:
            template_data = json.load(f)

        errors = []
        for node in template_data.get("data", {}).get("nodes", []):
            node_data = node.get("data", {})
            node_info = node_data.get("node", {})
            metadata = node_info.get("metadata", {})
            module_path = metadata.get("module", "")
            json_field_order = node_info.get("field_order")

            if not module_path or json_field_order is None:
                continue

            # Parse module path: "lfx.components.foo.bar.ClassName"
            parts = module_path.rsplit(".", 1)
            if len(parts) != 2:
                continue

            module_name, class_name = parts

            try:
                mod = import_module(module_name)
                cls = getattr(mod, class_name)
                instance = cls()
                component_field_order = instance._get_field_order()
            except Exception as e:
                errors.append(
                    f"  Node '{node_data.get('display_name', node_data.get('type', '?'))}' "
                    f"({class_name}): Could not instantiate component: {e}"
                )
                continue

            # Verify that the JSON field_order exactly matches the component's full field order.
            # A subset would cause layout inconsistency between template and sidebar components.
            if json_field_order != component_field_order:
                display = node_data.get("display_name") or node_data.get("type", "?")
                missing = [f for f in component_field_order if f not in json_field_order]
                extra = [f for f in json_field_order if f not in component_field_order]
                detail_lines = [
                    f"    JSON field_order:     {json_field_order}",
                    f"    Expected (component): {component_field_order}",
                ]
                if missing:
                    detail_lines.append(f"    Missing fields:       {missing}")
                if extra:
                    detail_lines.append(f"    Extra fields:         {extra}")
                errors.append(f"  Node '{display}' ({class_name}):\n" + "\n".join(detail_lines))

        if errors:
            error_msg = "\n".join(errors)
            pytest.fail(f"field_order mismatches in {template_file.name}:\n{error_msg}")