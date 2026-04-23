async def list_dataflows(
    output_format: Literal["json", "markdown"] = "json",
) -> OBBject:
    """List all available IMF dataflows.

    Returns an OBBject containing either a JSON dictionary of dataflows
    or a markdown string under the 'results' attribute.
    """
    metadata = ImfMetadata()
    dataflows = metadata.dataflows

    if output_format == "markdown":
        all_tables = metadata.list_all_dataflow_tables()
        md_text = ""

        for dataflow_id in sorted(dataflows.keys()):
            details = dataflows[dataflow_id]
            indicators = metadata.get_indicators_in(dataflow_id)
            params = metadata.get_dataflow_parameters(dataflow_id)
            md_text += f"## `{dataflow_id}` - {details.get('name', '')}\n\n"

            if indicators:
                md_text += f"**Number of Series:** {len(indicators)}\n\n"

            if params:
                escaped_params = [f"`{param}`" for param in list(params)]
                md_text += f"**Dimensions:** {', '.join(escaped_params)}\n\n"

            presentations = all_tables.get(dataflow_id, [])

            if presentations:
                md_text += "### Presentation Tables\n\n"
                seen_names: set[str] = set()

                for pres in presentations:
                    pres_name = pres.get("name", "").strip()

                    if pres_name in seen_names:
                        continue

                    seen_names.add(pres_name)

                    pres_id = pres.get("id", "")
                    pres_desc = pres.get("description", "").strip()
                    friendly_name = pres.get("friendly_name", "")
                    symbol = f"{dataflow_id}::{pres_id}"
                    md_text += f"#### {pres_name}\n\n"

                    if friendly_name:
                        md_text += f"**Friendly Name:** `{friendly_name}`\n\n"

                    md_text += f"**Symbol:** `{symbol}`\n\n"

                    if pres_desc and pres_desc != pres_name:
                        md_text += f"{pres_desc}\n\n"

            md_text += f"{details.get('description', '').strip()}\n\n"
            md_text += "---\n\n"

        return OBBject(results=md_text)

    return OBBject(results=dataflows)