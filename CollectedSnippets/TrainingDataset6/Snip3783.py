def endpoint(
        info: Annotated[dict, Depends(extract_request_info)],
    ):
        return info