def process_contents_settings(contents: Optional[ContentSettings]) -> Dict[str, Any]:
    """Process ContentSettings into API payload format."""
    if not contents:
        return {}

    content_settings = {}

    # Handle text field (can be boolean or object)
    text_value = process_text_field(contents.text)
    if text_value is not None:
        content_settings["text"] = text_value

    # Handle highlights
    if contents.highlights:
        highlights_dict: Dict[str, Any] = {
            "numSentences": contents.highlights.num_sentences,
            "highlightsPerUrl": contents.highlights.highlights_per_url,
        }
        if contents.highlights.query:
            highlights_dict["query"] = contents.highlights.query
        content_settings["highlights"] = highlights_dict

    if contents.summary:
        summary_dict = {}
        if contents.summary.query:
            summary_dict["query"] = contents.summary.query
        if contents.summary.schema:
            summary_dict["schema"] = contents.summary.schema
        content_settings["summary"] = summary_dict

    if contents.livecrawl:
        content_settings["livecrawl"] = contents.livecrawl.value

    if contents.livecrawl_timeout is not None:
        content_settings["livecrawlTimeout"] = contents.livecrawl_timeout

    if contents.subpages is not None:
        content_settings["subpages"] = contents.subpages

    if contents.subpage_target:
        content_settings["subpageTarget"] = contents.subpage_target

    if contents.extras:
        extras_dict = {}
        if contents.extras.links:
            extras_dict["links"] = contents.extras.links
        if contents.extras.image_links:
            extras_dict["imageLinks"] = contents.extras.image_links
        content_settings["extras"] = extras_dict

    context_value = process_context_field(contents.context)
    if context_value is not None:
        content_settings["context"] = context_value

    return content_settings