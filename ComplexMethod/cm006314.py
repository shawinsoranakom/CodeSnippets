def validate_operation_references(self) -> WatsonxDeploymentUpdatePayload:
        if self.put_tools is not None:
            return self
        raw_tool_names = {payload.name for payload in (self.tools.raw_payloads or [])}

        raw_app_ids = {payload.app_id for payload in (self.connections.raw_payloads or [])}
        bind_operations = [operation for operation in self.operations if isinstance(operation, WatsonxBindOperation)]
        referenced_app_ids = _validate_bind_operation_references(
            operations=bind_operations,
            raw_tool_names=raw_tool_names,
        )

        for operation in self.operations:
            if not isinstance(operation, WatsonxUnbindOperation):
                continue
            for app_id in operation.app_ids:
                referenced_app_ids.add(app_id)
                if app_id in raw_app_ids:
                    msg = f"unbind.operation app_ids must not reference connections.raw_payloads app_ids: [{app_id!r}]"
                    raise ValueError(msg)

        _validate_all_declared_app_ids_are_referenced(
            raw_app_ids=raw_app_ids,
            referenced_app_ids=referenced_app_ids,
        )
        _validate_tool_ref_consistency(self.operations)
        _validate_overlapping_existing_tool_operations(self.operations)

        return self