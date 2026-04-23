def extract_structured_result(results: list, *, extract_text: bool = True) -> dict:
    """Extract structured result data from the results."""
    for result in results:
        if (
            hasattr(result, "vertex")
            and result.vertex.custom_component
            and result.vertex.custom_component.display_name == "Chat Output"
        ):
            message: Message = result.result_dict.results["message"]
            try:
                result_message = message.text if extract_text and hasattr(message, "text") else message
            except (AttributeError, TypeError, ValueError) as e:
                return {
                    "text": str(message),
                    "type": "message",
                    "component": result.vertex.custom_component.display_name,
                    "component_id": result.vertex.id,
                    "success": True,
                    "warning": f"Could not extract text properly: {e}",
                }

            return {
                "result": result_message,
                "type": "message",
                "component": result.vertex.custom_component.display_name,
                "component_id": result.vertex.id,
                "success": True,
            }
    return {"text": "No response generated", "type": "error", "success": False}