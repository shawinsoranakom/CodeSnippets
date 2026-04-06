def process_one_page(path: Path) -> bool:
    """
    Fix one translated document by comparing it to the English version.

    Returns True if processed successfully, False otherwise.
    """

    try:
        lang_code = path.parts[1]
        if lang_code == "en":
            print(f"Skipping English document: {path}")
            return True

        en_doc_path = Path("docs") / "en" / Path(*path.parts[2:])

        doc_lines = path.read_text(encoding="utf-8").splitlines()
        en_doc_lines = en_doc_path.read_text(encoding="utf-8").splitlines()

        doc_lines = check_translation(
            doc_lines=doc_lines,
            en_doc_lines=en_doc_lines,
            lang_code=lang_code,
            auto_fix=True,
            path=str(path),
        )

        # Write back the fixed document
        doc_lines.append("")  # Ensure file ends with a newline
        path.write_text("\n".join(doc_lines), encoding="utf-8")

    except ValueError as e:
        print(f"Error processing {path}: {e}")
        return False
    return True