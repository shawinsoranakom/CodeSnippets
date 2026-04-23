def _extract_results(resp: ChatCompletion, *, limit: int) -> list[WebSearchResult]:
    """Pull ``url_citation`` annotations from the response.

    Shared across both tiers — OpenRouter normalises the annotation
    schema across Perplexity's sonar models into
    ``Annotation.url_citation`` (typed in ``openai.types.chat``).  The
    ``content`` snippet is an OpenRouter extension on the otherwise-
    typed ``AnnotationURLCitation``; pydantic stashes unknown fields in
    ``model_extra``, which we read there rather than via ``getattr``.
    """
    if not resp.choices:
        return []
    annotations = resp.choices[0].message.annotations or []
    out: list[WebSearchResult] = []
    for ann in annotations:
        if len(out) >= limit:
            break
        if ann.type != "url_citation":
            continue
        citation = ann.url_citation
        extras = citation.model_extra or {}
        snippet_raw = extras.get("content")
        snippet = (snippet_raw or "")[:_SNIPPET_MAX_CHARS] if snippet_raw else ""
        out.append(
            WebSearchResult(
                title=citation.title,
                url=citation.url,
                snippet=snippet,
                page_age=None,
            )
        )
    return out