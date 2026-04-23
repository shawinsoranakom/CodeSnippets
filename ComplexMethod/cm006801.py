def build_data_from_result_data(result_data: ResultData) -> list[Data]:
    """Build a list of data from the given ResultData.

    Args:
        result_data (ResultData): The ResultData object containing the result data.

    Returns:
        List[Data]: A list of data built from the ResultData.

    """
    messages = result_data.messages

    if not messages:
        return []
    data = []

    # Handle results without chat messages (calling flow)
    if not messages:
        # Result with a single record
        if isinstance(result_data.artifacts, dict):
            data.append(Data(data=result_data.artifacts))
        # List of artifacts
        elif isinstance(result_data.artifacts, list):
            for artifact in result_data.artifacts:
                # If multiple records are found as artifacts, return as-is
                if isinstance(artifact, Data):
                    data.append(artifact)
                else:
                    # Warn about unknown output type
                    logger.warning(f"Unable to build record output from unknown ResultData.artifact: {artifact}")
        # Chat or text output
        elif result_data.results:
            data.append(Data(data={"result": result_data.results}, text_key="result"))
            return data
        else:
            return []

    if isinstance(result_data.results, dict):
        for name, result in result_data.results.items():
            dataobj: Data | Message | None
            dataobj = result if isinstance(result, Message) else Data(data=result, text_key=name)

            data.append(dataobj)
    else:
        data.append(Data(data=result_data.results))
    return data