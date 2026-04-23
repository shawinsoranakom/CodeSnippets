def detect_dataset_format(dataset):
    """
    Detects dataset format by inspecting structure.

    Returns:
        dict: {
            "format": "alpaca" | "sharegpt" | "chatml" | "unknown",
            "chat_column": "messages" | "conversations" | None,
            "needs_standardization": bool,
            "sample_keys": list of keys found in messages (for debugging)
        }
    """
    column_names = set(next(iter(dataset)).keys())

    # Check for Alpaca
    alpaca_columns = {"instruction", "output"}
    if alpaca_columns.issubset(column_names):
        return {
            "format": "alpaca",
            "chat_column": None,
            "needs_standardization": False,
            "sample_keys": [],
        }

    # Check for chat-based formats (messages or conversations)
    chat_column = None
    if "messages" in column_names:
        chat_column = "messages"
    elif "conversations" in column_names:
        chat_column = "conversations"
    elif "texts" in column_names:
        chat_column = "texts"

    if chat_column:
        # Inspect the structure to determine if ShareGPT or ChatML
        try:
            sample = next(iter(dataset))
            chat_data = sample[chat_column]

            if chat_data and len(chat_data) > 0:
                first_msg = chat_data[0]
                msg_keys = set(first_msg.keys())

                # ShareGPT uses "from" and "value"
                if "from" in msg_keys or "value" in msg_keys:
                    return {
                        "format": "sharegpt",
                        "chat_column": chat_column,
                        "needs_standardization": True,
                        "sample_keys": list(msg_keys),
                    }

                # ChatML uses "role" and "content"
                elif "role" in msg_keys and "content" in msg_keys:
                    return {
                        "format": "chatml",
                        "chat_column": chat_column,
                        "needs_standardization": False,
                        "sample_keys": list(msg_keys),
                    }

                # Unknown structure but has chat column
                else:
                    return {
                        "format": "unknown",
                        "chat_column": chat_column,
                        "needs_standardization": None,
                        "sample_keys": list(msg_keys),
                    }
        except Exception as e:
            return {
                "format": "unknown",
                "chat_column": chat_column,
                "needs_standardization": None,
                "sample_keys": [],
                "error": str(e),
            }

    # No recognized format
    return {
        "format": "unknown",
        "chat_column": None,
        "needs_standardization": None,
        "sample_keys": [],
    }