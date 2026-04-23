def extract_page_context(page_title: str, headlines_text: str, meta_description: str, base_url: str) -> dict:
    """
    Extract page context for link scoring - called ONCE per page for performance.
    Parser-agnostic function that takes pre-extracted data.

    Args:
        page_title: Title of the page
        headlines_text: Combined text from h1, h2, h3 elements
        meta_description: Meta description content
        base_url: Base URL of the page

    Returns:
        Dictionary containing page context data for fast link scoring
    """
    context = {
        'terms': set(),
        'headlines': headlines_text or '',
        'meta_description': meta_description or '',
        'domain': '',
        'is_docs_site': False
    }

    try:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        context['domain'] = parsed.netloc.lower()

        # Check if this is a documentation/reference site
        context['is_docs_site'] = any(indicator in context['domain'] 
                                    for indicator in ['docs.', 'api.', 'developer.', 'reference.'])

        # Create term set for fast intersection (performance optimization)
        all_text = ((page_title or '') + ' ' + context['headlines'] + ' ' + context['meta_description']).lower()
        # Simple tokenization - fast and sufficient for scoring
        context['terms'] = set(word.strip('.,!?;:"()[]{}') 
                             for word in all_text.split() 
                             if len(word.strip('.,!?;:"()[]{}')) > 2)

    except Exception:
        # Fail gracefully - return empty context
        pass

    return context