def _merge_head_data(
        self, 
        original_links: Links, 
        head_results: List[Dict[str, Any]],
        config: CrawlerRunConfig
    ) -> Links:
        """
        Merge head extraction results back into Link objects.

        Args:
            original_links: Original Links object
            head_results: Results from head extraction

        Returns:
            Links object with head_data attached to matching links
        """
        # Create URL to head_data mapping (key by both final and original URL for redirects)
        url_to_head_data = {}
        for result in head_results:
            url = result.get("url")
            head_info = {
                "head_data": result.get("head_data", {}),
                "status": result.get("status", "unknown"),
                "error": result.get("error"),
                "relevance_score": result.get("relevance_score")
            }
            if url:
                url_to_head_data[url] = head_info
            original_url = result.get("original_url")
            if original_url and original_url != url:
                url_to_head_data[original_url] = head_info

        # Update internal links
        updated_internal = []
        for link in original_links.internal:
            if link.href in url_to_head_data:
                head_info = url_to_head_data[link.href]
                # Create new Link object with head data and scoring
                contextual_score = head_info.get("relevance_score")

                updated_link = Link(
                    href=link.href,
                    text=link.text,
                    title=link.title,
                    base_domain=link.base_domain,
                    head_data=head_info["head_data"],
                    head_extraction_status=head_info["status"],
                    head_extraction_error=head_info.get("error"),
                    intrinsic_score=getattr(link, 'intrinsic_score', None),
                    contextual_score=contextual_score
                )

                # Add relevance score to head_data for backward compatibility
                if contextual_score is not None:
                    updated_link.head_data = updated_link.head_data or {}
                    updated_link.head_data["relevance_score"] = contextual_score

                # Calculate total score combining intrinsic and contextual scores
                updated_link.total_score = calculate_total_score(
                    intrinsic_score=updated_link.intrinsic_score,
                    contextual_score=updated_link.contextual_score,
                    score_links_enabled=getattr(config, 'score_links', False),
                    query_provided=bool(config.link_preview_config.query)
                )

                updated_internal.append(updated_link)
            else:
                # Calculate total_score even without head data, using intrinsic_score
                link.total_score = calculate_total_score(
                    intrinsic_score=getattr(link, 'intrinsic_score', None),
                    contextual_score=None,
                    score_links_enabled=getattr(config, 'score_links', False),
                    query_provided=bool(config.link_preview_config.query)
                )
                updated_internal.append(link)

        # Update external links
        updated_external = []
        for link in original_links.external:
            if link.href in url_to_head_data:
                head_info = url_to_head_data[link.href]
                # Create new Link object with head data and scoring
                contextual_score = head_info.get("relevance_score")

                updated_link = Link(
                    href=link.href,
                    text=link.text,
                    title=link.title,
                    base_domain=link.base_domain,
                    head_data=head_info["head_data"],
                    head_extraction_status=head_info["status"],
                    head_extraction_error=head_info.get("error"),
                    intrinsic_score=getattr(link, 'intrinsic_score', None),
                    contextual_score=contextual_score
                )

                # Add relevance score to head_data for backward compatibility
                if contextual_score is not None:
                    updated_link.head_data = updated_link.head_data or {}
                    updated_link.head_data["relevance_score"] = contextual_score

                # Calculate total score combining intrinsic and contextual scores
                updated_link.total_score = calculate_total_score(
                    intrinsic_score=updated_link.intrinsic_score,
                    contextual_score=updated_link.contextual_score,
                    score_links_enabled=getattr(config, 'score_links', False),
                    query_provided=bool(config.link_preview_config.query)
                )

                updated_external.append(updated_link)
            else:
                # Calculate total_score even without head data, using intrinsic_score
                link.total_score = calculate_total_score(
                    intrinsic_score=getattr(link, 'intrinsic_score', None),
                    contextual_score=None,
                    score_links_enabled=getattr(config, 'score_links', False),
                    query_provided=bool(config.link_preview_config.query)
                )
                updated_external.append(link)

        # Sort links by relevance score if available
        if any(hasattr(link, 'head_data') and link.head_data and 'relevance_score' in link.head_data 
               for link in updated_internal + updated_external):

            def get_relevance_score(link):
                if hasattr(link, 'head_data') and link.head_data and 'relevance_score' in link.head_data:
                    return link.head_data['relevance_score']
                return 0.0

            updated_internal.sort(key=get_relevance_score, reverse=True)
            updated_external.sort(key=get_relevance_score, reverse=True)

        return Links(
            internal=updated_internal,
            external=updated_external
        )