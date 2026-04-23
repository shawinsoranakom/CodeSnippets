def raise_error(data: dict, status: int = None):
        if "error_message" in data:
            raise ResponseError(data["error_message"])
        elif "error" in data:
            if isinstance(data["error"], str):
                if status is not None:
                    if status == 401:
                        raise MissingAuthError(f"Error {status}: {data['error']}")
                    elif status == 402:
                        raise PaymentRequiredError(f"Error {status}: {data['error']}")
                    raise ResponseError(f"Error {status}: {data['error']}")
                raise ResponseError(data["error"])
            elif isinstance(data["error"], bool):
                raise ResponseError(data)
            elif "code" in data["error"]:
                raise ResponseError("\n".join(
                    [e for e in [f'Error {data["error"]["code"]}: {data["error"]["message"]}', data["error"].get("failed_generation")] if e is not None]
                ))
            elif "message" in data["error"]:
                raise ResponseError(data["error"]["message"])
            else:
                raise ResponseError(data["error"])