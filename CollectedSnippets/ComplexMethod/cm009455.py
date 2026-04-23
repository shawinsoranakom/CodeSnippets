def _generate_response_from_error(error: BaseException) -> list[ChatGeneration]:
    if hasattr(error, "response"):
        response = error.response
        metadata: dict = {}
        if hasattr(response, "json"):
            try:
                metadata["body"] = response.json()
            except Exception:
                try:
                    metadata["body"] = getattr(response, "text", None)
                except Exception:
                    metadata["body"] = None
        if hasattr(response, "headers"):
            try:
                metadata["headers"] = dict(response.headers)
            except Exception:
                metadata["headers"] = None
        if hasattr(response, "status_code"):
            metadata["status_code"] = response.status_code
        if hasattr(error, "request_id"):
            metadata["request_id"] = error.request_id
        generations = [
            ChatGeneration(message=AIMessage(content="", response_metadata=metadata))
        ]
    else:
        generations = []

    return generations