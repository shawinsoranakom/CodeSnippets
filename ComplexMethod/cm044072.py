def _extract_provider_description(full_description: str, provider: str) -> str:
    r"""Extract description for a specific provider from merged description.

    Description format: "desc1 (provider: prov1);\n    desc2 (provider: prov2)"
    """
    # pylint: disable=import-outside-toplevel
    import re

    if not full_description:
        return ""

    # Check if this is a multi-provider description
    if "(provider:" not in full_description:
        return full_description.split("Multiple comma separated items allowed")[
            0
        ].strip()

    # Handle semicolons embedded in the description text
    parts = re.split(r"(\(provider:\s*[^)]+\))", full_description)

    # Find the text that comes before the provider marker we want
    for i, part in enumerate(parts):
        is_matching_provider = (
            f"provider: {provider})" in part
            or f"provider: {provider}," in part
            or f", {provider})" in part
        )
        if is_matching_provider and i > 0:
            # The description is the part before this marker
            desc = parts[i - 1].strip()
            # When a preceding text contains multiple sections separated by
            # ";\n    " (e.g. "general desc ...;\n    provider-specific desc"),
            # extract the last section which belongs to this provider marker.
            sections = re.split(r";\s*\n\s*", desc)
            if len(sections) > 1:
                desc = sections[-1].strip()
            # Remove leading semicolons and whitespace from continuation sections
            desc = re.sub(r"^;\s*", "", desc).strip()
            # Remove "Multiple comma separated items allowed" suffix
            desc = desc.split("Multiple comma separated items allowed")[0].strip()
            return desc

    # If no specific provider section found, return first section (general description)
    first_desc = full_description.split("(provider:")[0].strip()
    first_desc = first_desc.split("Multiple comma separated items allowed")[0].strip()
    return first_desc