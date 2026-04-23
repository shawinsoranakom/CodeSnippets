def convert_to_localized_md(model_list: str, localized_model_list: str, format_str: str) -> tuple[bool, str]:
    """
    Compare the model list from the main README to the one in a localized README.

    Args:
        model_list (`str`): The model list in the main README.
        localized_model_list (`str`): The model list in one of the localized README.
        format_str (`str`):
            The template for a model entry in the localized README (look at the `format_model_list` in the entries of
            `LOCALIZED_READMES` for examples).

    Returns:
        `Tuple[bool, str]`: A tuple where the first value indicates if the READMEs match or not, and the second value
        is the correct localized README.
    """

    def _rep(match):
        title, model_link, paper_affiliations, paper_title_link, paper_authors, supplements = match.groups()
        return format_str.format(
            title=title,
            model_link=model_link,
            paper_affiliations=paper_affiliations,
            paper_title_link=paper_title_link,
            paper_authors=paper_authors,
            supplements=" " + supplements.strip() if len(supplements) != 0 else "",
        )

    # This regex captures metadata from an English model description, including model title, model link,
    # affiliations of the paper, title of the paper, authors of the paper, and supplemental data (see DistilBERT for
    # example).
    _re_capture_meta = re.compile(
        r"\*\*\[([^\]]*)\]\(([^\)]*)\)\*\* \(from ([^)]*)\)[^\[]*([^\)]*\)).*?by (.*?[A-Za-z\*]{2,}?)\. (.*)$"
    )
    # This regex is used to synchronize title link.
    _re_capture_title_link = re.compile(r"\*\*\[([^\]]*)\]\(([^\)]*)\)\*\*")
    # This regex is used to synchronize paper title and link.
    _re_capture_paper_link = re.compile(r" \[([^\]]*)\]\(([^\)]*)\)")

    if len(localized_model_list) == 0:
        localized_model_index = {}
    else:
        try:
            localized_model_index = {
                re.search(r"\*\*\[([^\]]*)", line).groups()[0]: line
                for line in localized_model_list.strip().split("\n")
            }
        except AttributeError:
            raise AttributeError("A model name in localized READMEs cannot be recognized.")

    model_keys = [re.search(r"\*\*\[([^\]]*)", line).groups()[0] for line in model_list.strip().split("\n")]

    # We exclude keys in localized README not in the main one.
    readmes_match = not any(k not in model_keys for k in localized_model_index)
    localized_model_index = {k: v for k, v in localized_model_index.items() if k in model_keys}

    for model in model_list.strip().split("\n"):
        title, model_link = _re_capture_title_link.search(model).groups()
        if title not in localized_model_index:
            readmes_match = False
            # Add an anchor white space behind a model description string for regex.
            # If metadata cannot be captured, the English version will be directly copied.
            localized_model_index[title] = _re_capture_meta.sub(_rep, model + " ")
        elif _re_fill_pattern.search(localized_model_index[title]) is not None:
            update = _re_capture_meta.sub(_rep, model + " ")
            if update != localized_model_index[title]:
                readmes_match = False
                localized_model_index[title] = update
        else:
            # Synchronize title link
            converted_model = _re_capture_title_link.sub(
                f"**[{title}]({model_link})**", localized_model_index[title], count=1
            )

            # Synchronize paper title and its link (if found)
            paper_title_link = _re_capture_paper_link.search(model)
            if paper_title_link is not None:
                paper_title, paper_link = paper_title_link.groups()
                converted_model = _re_capture_paper_link.sub(
                    f" [{paper_title}]({paper_link})", converted_model, count=1
                )

            if converted_model != localized_model_index[title]:
                readmes_match = False
                localized_model_index[title] = converted_model

    sorted_index = sorted(localized_model_index.items(), key=lambda x: x[0].lower())

    return readmes_match, "\n".join(x[1] for x in sorted_index) + "\n"