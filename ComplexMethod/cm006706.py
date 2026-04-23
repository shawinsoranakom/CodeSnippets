def get_type(payload):
    # Importing here to avoid circular imports
    from lfx.schema.data import Data
    from lfx.schema.dataframe import DataFrame
    from lfx.schema.message import Message

    result = LogType.UNKNOWN
    match payload:
        case Message():
            result = LogType.MESSAGE

        case Data():
            result = LogType.DATA

        case dict():
            result = LogType.OBJECT

        case list() | DataFrame():
            result = LogType.ARRAY

        case str():
            result = LogType.TEXT

    if result == LogType.UNKNOWN and (
        (payload and isinstance(payload, Generator))
        or (isinstance(payload, Message) and isinstance(payload.text, Generator))
    ):
        result = LogType.STREAM

    return result