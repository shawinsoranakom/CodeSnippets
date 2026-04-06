def replace_header_permalinks(
    text: list[str],
    header_permalinks: list[HeaderPermalinkInfo],
    original_header_permalinks: list[HeaderPermalinkInfo],
) -> list[str]:
    """
    Replace permalinks in the given text with the permalinks from the original document.

    Fail if the number or level of headers does not match the original.
    """

    modified_text: list[str] = text.copy()

    if len(header_permalinks) != len(original_header_permalinks):
        raise ValueError(
            "Number of headers with permalinks does not match the number in the "
            "original document "
            f"({len(header_permalinks)} vs {len(original_header_permalinks)})"
        )

    for header_no in range(len(header_permalinks)):
        header_info = header_permalinks[header_no]
        original_header_info = original_header_permalinks[header_no]

        if header_info["hashes"] != original_header_info["hashes"]:
            raise ValueError(
                "Header levels do not match between document and original document"
                f" (found {header_info['hashes']}, expected {original_header_info['hashes']})"
                f" for header №{header_no + 1} in line {header_info['line_no']}"
            )
        line_no = header_info["line_no"] - 1
        hashes = header_info["hashes"]
        title = header_info["title"]
        permalink = original_header_info["permalink"]
        modified_text[line_no] = f"{hashes} {title}{permalink}"

    return modified_text