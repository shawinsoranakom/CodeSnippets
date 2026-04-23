def calculate_link_intrinsic_score(
    link_text: str, 
    url: str, 
    title_attr: str, 
    class_attr: str, 
    rel_attr: str, 
    page_context: dict
) -> float:
    """
    Ultra-fast link quality scoring using only provided data (no DOM access needed).
    Parser-agnostic function.

    Args:
        link_text: Text content of the link
        url: Link URL
        title_attr: Title attribute of the link
        class_attr: Class attribute of the link
        rel_attr: Rel attribute of the link
        page_context: Pre-computed page context from extract_page_context()

    Returns:
        Quality score (0.0 - 10.0), higher is better
    """
    score = 0.0

    try:
        # 1. ATTRIBUTE QUALITY (string analysis - very fast)
        if title_attr and len(title_attr.strip()) > 3:
            score += 1.0

        class_str = (class_attr or '').lower()
        # Navigation/important classes boost score
        if any(nav_class in class_str for nav_class in ['nav', 'menu', 'primary', 'main', 'important']):
            score += 1.5
        # Marketing/ad classes reduce score  
        if any(bad_class in class_str for bad_class in ['ad', 'sponsor', 'track', 'promo', 'banner']):
            score -= 1.0

        rel_str = (rel_attr or '').lower()
        # Semantic rel values
        if any(good_rel in rel_str for good_rel in ['canonical', 'next', 'prev', 'chapter']):
            score += 1.0
        if any(bad_rel in rel_str for bad_rel in ['nofollow', 'sponsored', 'ugc']):
            score -= 0.5

        # 2. URL STRUCTURE QUALITY (string operations - very fast)
        url_lower = url.lower()

        # High-value path patterns
        if any(good_path in url_lower for good_path in ['/docs/', '/api/', '/guide/', '/tutorial/', '/reference/', '/manual/']):
            score += 2.0
        elif any(medium_path in url_lower for medium_path in ['/blog/', '/article/', '/post/', '/news/']):
            score += 1.0

        # Penalize certain patterns
        if any(bad_path in url_lower for bad_path in ['/admin/', '/login/', '/cart/', '/checkout/', '/track/', '/click/']):
            score -= 1.5

        # URL depth (shallow URLs often more important)
        url_depth = url.count('/') - 2  # Subtract protocol and domain
        if url_depth <= 2:
            score += 1.0
        elif url_depth > 5:
            score -= 0.5

        # HTTPS bonus
        if url.startswith('https://'):
            score += 0.5

        # 3. TEXT QUALITY (string analysis - very fast)
        if link_text:
            text_clean = link_text.strip()
            if len(text_clean) > 3:
                score += 1.0

            # Multi-word links are usually more descriptive
            word_count = len(text_clean.split())
            if word_count >= 2:
                score += 0.5
            if word_count >= 4:
                score += 0.5

            # Avoid generic link text
            generic_texts = ['click here', 'read more', 'more info', 'link', 'here']
            if text_clean.lower() in generic_texts:
                score -= 1.0

        # 4. CONTEXTUAL RELEVANCE (pre-computed page terms - very fast)
        if page_context.get('terms') and link_text:
            link_words = set(word.strip('.,!?;:"()[]{}').lower() 
                           for word in link_text.split() 
                           if len(word.strip('.,!?;:"()[]{}')) > 2)

            if link_words:
                # Calculate word overlap ratio
                overlap = len(link_words & page_context['terms'])
                if overlap > 0:
                    relevance_ratio = overlap / min(len(link_words), 10)  # Cap to avoid over-weighting
                    score += relevance_ratio * 2.0  # Up to 2 points for relevance

        # 5. DOMAIN CONTEXT BONUSES (very fast string checks)
        if page_context.get('is_docs_site', False):
            # Documentation sites: prioritize internal navigation
            if link_text and any(doc_keyword in link_text.lower() 
                               for doc_keyword in ['api', 'reference', 'guide', 'tutorial', 'example']):
                score += 1.0

    except Exception:
        # Fail gracefully - return minimal score
        score = 0.5

    # Ensure score is within reasonable bounds
    return max(0.0, min(score, 10.0))