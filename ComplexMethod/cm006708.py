def build_output_logs(vertex, result) -> dict:
    """Build output logs from vertex outputs and results."""
    # Importing here to avoid circular imports
    from lfx.schema.dataframe import DataFrame
    from lfx.serialization.serialization import serialize

    outputs: dict[str, OutputValue] = {}
    component_instance: Component = result[0]
    for index, output in enumerate(vertex.outputs):
        if component_instance.status is None:
            payload = component_instance.get_results()
            output_result = payload.get(output["name"])
        else:
            payload = component_instance.get_artifacts()
            output_result = payload.get(output["name"], {}).get("raw")
        message = get_message(output_result)
        type_ = get_type(output_result)

        match type_:
            case LogType.STREAM if "stream_url" in message:
                message = StreamURL(location=message["stream_url"])

            case LogType.STREAM:
                message = ""

            case LogType.MESSAGE if hasattr(message, "message"):
                message = message.message

            case LogType.UNKNOWN:
                message = ""

            case LogType.ARRAY:
                if isinstance(message, DataFrame):
                    message = message.to_dict(orient="records")
                message = [serialize(item) for item in message]
        name = output.get("name", f"output_{index}")
        outputs |= {name: OutputValue(message=message, type=type_).model_dump()}

    return outputs