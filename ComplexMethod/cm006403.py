async def update_component_field_value(
    flow_id_or_name: str,
    component_id: str,
    field_name: str,
    new_value: Any,
    user_id: str | UUID,
) -> dict[str, Any]:
    """Update the value of a specific field in a component and persist to database.

    Args:
        flow_id_or_name: Flow ID (UUID) or endpoint name.
        component_id: The component/vertex ID.
        field_name: The name of the field to update.
        new_value: The new value to set.
        user_id: User ID (required for authorization).

    Returns:
        Dictionary containing:
        - success: Boolean indicating if update was successful
        - field_name: The field name that was updated
        - old_value: The previous value
        - new_value: The new value that was set
        - component_id: The component ID
        - flow_id: The flow ID
        - error: Error message if update failed

    Example:
        >>> result = await update_component_field_value(
        ...     "my-flow",
        ...     "ChatInput-abc",
        ...     "input_value",
        ...     "Hello, world!",
        ...     user_id="user-123"
        ... )
        >>> print(result["success"])
    """
    try:
        # Load the flow
        flow = await get_flow_by_id_or_endpoint_name(flow_id_or_name, user_id)

        if flow is None:
            return {"error": f"Flow {flow_id_or_name} not found", "success": False}

        if flow.data is None:
            return {"error": f"Flow {flow_id_or_name} has no data", "success": False}

        flow_id_str = str(flow.id)

        # Find the component in the flow data
        flow_data = flow.data.copy()
        nodes = flow_data.get("nodes", [])

        component_found = False
        old_value = None

        for node in nodes:
            if node.get("id") == component_id:
                component_found = True
                template = node.get("data", {}).get("node", {}).get("template", {})

                if field_name not in template:
                    available_fields = list(template.keys())
                    return {
                        "error": f"Field {field_name} not found in component {component_id}",
                        "available_fields": available_fields,
                        "success": False,
                    }

                old_value = template[field_name].get("value")
                template[field_name]["value"] = new_value
                break

        if not component_found:
            return {
                "error": f"Component {component_id} not found in flow {flow_id_or_name}",
                "success": False,
            }

        # Update the flow in the database
        async with session_scope() as session:
            # Get the database flow object
            db_flow = await session.get(Flow, UUID(flow_id_str))

            if not db_flow:
                return {"error": f"Flow {flow_id_str} not found in database", "success": False}

            # Verify user has permission
            if str(db_flow.user_id) != str(user_id):
                return {"error": "User does not have permission to update this flow", "success": False}

            # Update the flow data
            db_flow.data = flow_data
            session.add(db_flow)
            await session.commit()
            await session.refresh(db_flow)

    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error updating field {field_name} in {component_id} of {flow_id_or_name}: {e}")
        return {"error": str(e), "success": False}
    else:
        return {
            "success": True,
            "field_name": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "component_id": component_id,
            "flow_id": flow_id_str,
            "flow_name": flow.name,
        }
    finally:
        await logger.ainfo("Updating field value completed")