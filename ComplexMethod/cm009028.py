def _apply_mask_strategy(content: str, matches: list[PIIMatch]) -> str:
    result = content
    for match in sorted(matches, key=operator.itemgetter("start"), reverse=True):
        value = match["value"]
        pii_type = match["type"]
        if pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:  # noqa: PLR2004
                domain_parts = parts[1].split(".")
                masked = (
                    f"{parts[0]}@****.{domain_parts[-1]}"
                    if len(domain_parts) > 1
                    else f"{parts[0]}@****"
                )
            else:
                masked = "****"
        elif pii_type == "credit_card":
            digits_only = "".join(c for c in value if c.isdigit())
            separator = "-" if "-" in value else " " if " " in value else ""
            if separator:
                masked = (
                    f"****{separator}****{separator}****{separator}"
                    f"{digits_only[-_UNMASKED_CHAR_NUMBER:]}"
                )
            else:
                masked = f"************{digits_only[-_UNMASKED_CHAR_NUMBER:]}"
        elif pii_type == "ip":
            octets = value.split(".")
            masked = f"*.*.*.{octets[-1]}" if len(octets) == _IPV4_PARTS_NUMBER else "****"
        elif pii_type == "mac_address":
            separator = ":" if ":" in value else "-"
            masked = (
                f"**{separator}**{separator}**{separator}**{separator}**{separator}{value[-2:]}"
            )
        elif pii_type == "url":
            masked = "[MASKED_URL]"
        else:
            masked = (
                f"****{value[-_UNMASKED_CHAR_NUMBER:]}"
                if len(value) > _UNMASKED_CHAR_NUMBER
                else "****"
            )
        result = result[: match["start"]] + masked + result[match["end"] :]
    return result