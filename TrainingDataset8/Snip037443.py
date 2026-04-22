def _get_nonstreamlit_traceback(
    extracted_tb: traceback.StackSummary,
) -> List[traceback.FrameSummary]:
    return [
        entry for entry in extracted_tb if not _is_in_streamlit_package(entry.filename)
    ]