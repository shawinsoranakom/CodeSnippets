def node_data_json(
    node: Node, *, with_schemas: bool = False
) -> dict[str, str | dict[str, Any]]:
    """Convert the data of a node to a JSON-serializable format.

    Args:
        node: The `Node` to convert.
        with_schemas: Whether to include the schema of the data if it is a Pydantic
            model.

    Returns:
        A dictionary with the type of the data and the data itself.
    """
    if node.data is None:
        json: dict[str, Any] = {}
    elif isinstance(node.data, RunnableSerializable):
        json = {
            "type": "runnable",
            "data": {
                "id": node.data.lc_id(),
                "name": node_data_str(node.id, node.data),
            },
        }
    elif isinstance(node.data, Runnable):
        json = {
            "type": "runnable",
            "data": {
                "id": to_json_not_implemented(node.data)["id"],
                "name": node_data_str(node.id, node.data),
            },
        }
    elif inspect.isclass(node.data) and is_basemodel_subclass(node.data):
        json = (
            {
                "type": "schema",
                "data": node.data.model_json_schema(
                    schema_generator=_IgnoreUnserializable
                ),
            }
            if with_schemas
            else {
                "type": "schema",
                "data": node_data_str(node.id, node.data),
            }
        )
    else:
        json = {
            "type": "unknown",
            "data": node_data_str(node.id, node.data),
        }
    if node.metadata is not None:
        json["metadata"] = node.metadata
    return json