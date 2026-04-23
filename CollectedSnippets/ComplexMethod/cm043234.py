def _build_feedback_message(
        validation_result: dict,
        schema: dict,
        attempt: int,
        is_repeated: bool,
    ) -> str:
        """Build a structured feedback message from a validation result."""
        vr = validation_result
        parts = []

        parts.append(f"## Schema Validation — Attempt {attempt}")

        # Base selector
        if vr["base_elements_found"] == 0:
            parts.append(
                f"**CRITICAL:** baseSelector `{schema.get('baseSelector', '')}` "
                f"matched **0 elements**. The schema cannot extract anything."
            )
            if vr["top_level_structure"]:
                parts.append(
                    "Here is the top-level HTML structure so you can pick a valid selector:\n```\n"
                    + vr["top_level_structure"]
                    + "\n```"
                )
        else:
            parts.append(
                f"baseSelector matched **{vr['base_elements_found']}** element(s)."
            )

        # Field coverage table
        if vr["field_details"]:
            parts.append(
                f"\n**Field coverage:** {vr['populated_fields']}/{vr['total_fields']} fields have data\n"
            )
            parts.append("| Field | Populated | Sample |")
            parts.append("|-------|-----------|--------|")
            for fd in vr["field_details"]:
                sample = fd["sample_value"] or "*(empty)*"
                parts.append(
                    f"| {fd['name']} | {fd['populated_count']}/{fd['total_count']} | {sample} |"
                )

        # Issues
        if vr["issues"]:
            parts.append("\n**Issues:**")
            for issue in vr["issues"]:
                parts.append(f"- {issue}")

        # Sample base HTML when all fields empty
        if vr["populated_fields"] == 0 and vr["sample_base_html"]:
            parts.append(
                "\nHere is the innerHTML of the first base element — "
                "use it to find correct child selectors:\n```html\n"
                + vr["sample_base_html"]
                + "\n```"
            )

        # Repeated schema warning
        if is_repeated:
            parts.append(
                "\n**WARNING:** You returned the exact same schema as before. "
                "You MUST change the selectors to fix the issues above."
            )

        parts.append(
            "\nPlease fix the schema and return ONLY valid JSON, nothing else."
        )
        return "\n".join(parts)