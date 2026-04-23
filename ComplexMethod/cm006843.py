def extract_text_from_result(results: list) -> str:
    """Extract just the text content from the results."""
    for result in results:
        if (
            hasattr(result, "vertex")
            and result.vertex.custom_component
            and result.vertex.custom_component.display_name == "Chat Output"
        ):
            message: dict | Message = result.result_dict.results.get("message")
            try:
                # Return just the text content
                if isinstance(message, dict):
                    text_content = message.get("text") if message.get("text") else str(message)
                else:
                    text_content = message.text
                return str(text_content)
            except AttributeError:
                # Fallback to string representation
                return str(message)
    return "No response generated"