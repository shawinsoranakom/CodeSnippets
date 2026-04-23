def _format_sparc_rejection(self, reflection_result) -> str:
        """Format SPARC rejection into a helpful error message."""
        if not reflection_result.issues:
            return "Error: Tool call validation failed - please review your approach and try again"

        error_parts = ["Tool call validation failed:"]

        for issue in reflection_result.issues:
            error_parts.append(f"\n• {issue.explanation}")
            if issue.correction:
                try:
                    correction_data = issue.correction
                    if isinstance(correction_data, dict):
                        if "corrected_function_name" in correction_data:
                            error_parts.append(f"  💡 Suggested function: {correction_data['corrected_function_name']}")
                        elif "tool_call" in correction_data:
                            suggested_args = correction_data["tool_call"].get("arguments", {})
                            error_parts.append(f"  💡 Suggested parameters: {suggested_args}")
                except (AttributeError, KeyError, TypeError):
                    # If correction parsing fails, skip it
                    pass

        error_parts.append("\nPlease adjust your approach and try again.")
        return "\n".join(error_parts)