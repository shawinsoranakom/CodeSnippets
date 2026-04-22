def generate_download_filename_from_title(title_string: str) -> str:
    """Generated download filename from page title string."""

    title_string = title_string.replace(" · Streamlit", "")
    file_name_string = clean_filename(title_string)
    title_string = snake_case_to_camel_case(file_name_string)
    return append_date_time_to_string(title_string)