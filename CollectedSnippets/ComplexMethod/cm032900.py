def should_skip_raptor(
        file_type: Optional[str] = None,
        parser_id: str = "",
        parser_config: Optional[dict] = None,
        raptor_config: Optional[dict] = None
) -> bool:
    """
    Determine if Raptor should be skipped for a given document.

    This function implements the logic to automatically disable Raptor for:
    1. Excel files (.xls, .xlsx, .csv, etc.)
    2. PDFs with tabular data (using table parser or html4excel)

    Args:
        file_type: File extension (e.g., ".xlsx", ".pdf")
        parser_id: Parser ID being used
        parser_config: Parser configuration dict
        raptor_config: Raptor configuration dict (can override with auto_disable_for_structured_data)

    Returns:
        True if Raptor should be skipped, False otherwise
    """
    parser_config = parser_config or {}
    raptor_config = raptor_config or {}

    # Check if auto-disable is explicitly disabled in config
    if raptor_config.get("auto_disable_for_structured_data", True) is False:
        logging.info("Raptor auto-disable is turned off via configuration")
        return False

    # Check for Excel/CSV files
    if is_structured_file_type(file_type):
        logging.info(f"Skipping Raptor for structured file type: {file_type}")
        return True

    # Check for tabular PDFs
    if file_type and file_type.lower() in [".pdf", "pdf"]:
        if is_tabular_pdf(parser_id, parser_config):
            logging.info(f"Skipping Raptor for tabular PDF (parser_id={parser_id})")
            return True

    return False