def get_message(payload):
    # Importing here to avoid circular imports
    from lfx.schema.data import Data

    message = None
    if hasattr(payload, "data"):
        message = payload.data

    elif hasattr(payload, "model_dump"):
        message = payload.model_dump()

    if message is None and isinstance(payload, dict | str | Data):
        message = payload.data if isinstance(payload, Data) else payload

    if isinstance(message, Series):
        return message if not message.empty else payload

    return message or payload