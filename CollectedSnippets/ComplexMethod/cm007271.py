def get_field_value(self) -> Data:
        flow = _ensure_working_flow()
        node = _find_node(flow, self.component_id)
        if node is None:
            available = [n.get("data", {}).get("id", "") for n in flow.get("data", {}).get("nodes", [])]
            return Data(data={"error": f"Component '{self.component_id}' not found. Available: {available}"})

        template = node.get("data", {}).get("node", {}).get("template", {})

        if not self.field_name:
            # List all fields with their values
            fields = {}
            for fname, fdata in template.items():
                if not isinstance(fdata, dict) or fname in ("code", "_type"):
                    continue
                value = fdata.get("value")
                if is_sensitive_field(fname) and value:
                    fields[fname] = "***REDACTED***"
                else:
                    fields[fname] = value
            return Data(data={"component_id": self.component_id, "fields": fields})

        # Get specific field
        if self.field_name not in template:
            available = [k for k, v in template.items() if isinstance(v, dict) and k not in ("code", "_type")]
            return Data(data={"error": f"Field '{self.field_name}' not found. Available: {available}"})

        fdata = template[self.field_name]
        value = fdata.get("value") if isinstance(fdata, dict) else fdata
        if is_sensitive_field(self.field_name) and value:
            value = "***REDACTED***"
        return Data(data={"component_id": self.component_id, "field": self.field_name, "value": value})