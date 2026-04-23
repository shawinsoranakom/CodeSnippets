def _validate_overlapping_existing_tool_operations(operations: list[Any]) -> None:
    bind_app_ids_by_tool: dict[str, set[str]] = {}
    unbind_app_ids_by_tool: dict[str, set[str]] = {}
    attach_tool_ids: set[str] = set()
    remove_tool_ids: set[str] = set()

    for operation in operations:
        if isinstance(operation, WatsonxBindOperation):
            ref = operation.tool.tool_id_with_ref
            if ref is None:
                continue
            bind_app_ids_by_tool.setdefault(ref.tool_id, set()).update(operation.app_ids)
            continue

        if isinstance(operation, WatsonxAttachToolOperation):
            tool_id = operation.tool.tool_id
            if tool_id in attach_tool_ids:
                msg = f"Duplicate attach_tool operation for tool_id: [{tool_id!r}]"
                raise ValueError(msg)
            attach_tool_ids.add(tool_id)
            continue

        if isinstance(operation, WatsonxUnbindOperation):
            unbind_app_ids_by_tool.setdefault(operation.tool.tool_id, set()).update(operation.app_ids)
            continue

        if isinstance(operation, WatsonxRemoveToolOperation):
            tool_id = operation.tool.tool_id
            if tool_id in remove_tool_ids:
                msg = f"Duplicate remove_tool operation for tool_id: [{tool_id!r}]"
                raise ValueError(msg)
            remove_tool_ids.add(tool_id)
            continue

    bind_tool_ids = set(bind_app_ids_by_tool)
    overlap_attach_bind = sorted(attach_tool_ids.intersection(bind_tool_ids))
    if overlap_attach_bind:
        msg = (
            "attach_tool cannot be combined with bind.tool.tool_id_with_ref for the same tool_id(s): "
            f"{overlap_attach_bind}"
        )
        raise ValueError(msg)

    for tool_id in sorted(remove_tool_ids):
        if tool_id in bind_tool_ids or tool_id in attach_tool_ids or tool_id in unbind_app_ids_by_tool:
            msg = f"remove_tool cannot be combined with bind/attach_tool/unbind for the same tool_id: [{tool_id!r}]"
            raise ValueError(msg)

    for tool_id, bind_app_ids in bind_app_ids_by_tool.items():
        overlap_app_ids = sorted(bind_app_ids.intersection(unbind_app_ids_by_tool.get(tool_id, set())))
        if overlap_app_ids:
            msg = f"bind and unbind app_ids overlap for the same tool_id [{tool_id!r}]: {overlap_app_ids}"
            raise ValueError(msg)