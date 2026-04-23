def insert_dates(model_card_list: list[str]):
    """Insert or update release and commit dates in model cards"""
    for model_card in model_card_list:
        model_card = _normalize_model_card_name(model_card)
        if _should_skip_model_card(model_card):
            continue

        file_path = os.path.join(DOCS_PATH, model_card)

        # First replace arxiv paper links with hf paper link if possible
        replace_paper_links(file_path)

        # Read content and ensure copyright disclaimer exists
        content = _read_model_card_content(model_card)
        markers = list(re.finditer(r"-->", content))

        if len(markers) == 0:
            # No copyright marker found, adding disclaimer to the top
            content = COPYRIGHT_DISCLAIMER + "\n\n" + content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            markers = list(re.finditer(r"-->", content))

        # Get dates
        hf_commit_date = get_first_commit_date(model_name=model_card)
        paper_link = get_paper_link(model_card=model_card, path=file_path)

        if paper_link in ("No_paper", "blog"):
            release_date = r"{release_date}"
        else:
            release_date = get_release_date(paper_link)

        match = _get_dates_pattern_match(content)

        # Update or insert the dates line
        if match:
            # Preserve existing release date unless it's a placeholder
            existing_release_date = match.group(1)
            existing_hf_date = match.group(2)

            if existing_release_date not in (r"{release_date}", "None"):
                release_date = existing_release_date

            if _dates_differ_significantly(existing_hf_date, hf_commit_date) or existing_release_date != release_date:
                old_line = match.group(0)
                new_line = f"\n*This model was released on {release_date} and added to Hugging Face Transformers on {hf_commit_date}.*"
                content = content.replace(old_line, new_line)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            # Insert new dates line after copyright marker
            insert_index = markers[0].end()
            date_info = f"\n*This model was released on {release_date} and added to Hugging Face Transformers on {hf_commit_date}.*"
            content = content[:insert_index] + date_info + content[insert_index:]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)