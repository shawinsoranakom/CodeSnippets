async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        query: str = "",
        **kwargs,
    ) -> ToolResponseBase:
        """Search documentation and return relevant sections.

        Args:
            user_id: User ID (not required for docs)
            session: Chat session
            query: Search query

        Returns:
            DocSearchResultsResponse: List of matching documentation sections
            NoResultsResponse: No results found
            ErrorResponse: Error message
        """
        query = query.strip()
        session_id = session.session_id if session else None

        if not query:
            return ErrorResponse(
                message="Please provide a search query.",
                error="Missing query parameter",
                session_id=session_id,
            )

        try:
            # Search using hybrid search for DOCUMENTATION content type only
            results, total = await search().unified_hybrid_search(
                query=query,
                content_types=[ContentType.DOCUMENTATION],
                page=1,
                page_size=MAX_RESULTS * 2,  # Fetch extra for deduplication
                min_score=0.1,  # Lower threshold for docs
            )

            if not results:
                return NoResultsResponse(
                    message=f"No documentation found for '{query}'.",
                    suggestions=[
                        "Try different keywords",
                        "Use more general terms",
                        "Check for typos in your query",
                    ],
                    session_id=session_id,
                )

            # Deduplicate by document path (keep highest scoring section per doc)
            seen_docs: dict[str, dict[str, Any]] = {}
            for result in results:
                metadata = result.get("metadata", {})
                doc_path = metadata.get("path", "")

                if not doc_path:
                    continue

                # Keep the highest scoring result for each document
                if doc_path not in seen_docs:
                    seen_docs[doc_path] = result
                elif result.get("combined_score", 0) > seen_docs[doc_path].get(
                    "combined_score", 0
                ):
                    seen_docs[doc_path] = result

            # Sort by score and take top MAX_RESULTS
            deduplicated = sorted(
                seen_docs.values(),
                key=lambda x: x.get("combined_score", 0),
                reverse=True,
            )[:MAX_RESULTS]

            if not deduplicated:
                return NoResultsResponse(
                    message=f"No documentation found for '{query}'.",
                    suggestions=[
                        "Try different keywords",
                        "Use more general terms",
                    ],
                    session_id=session_id,
                )

            # Build response
            doc_results: list[DocSearchResult] = []
            for result in deduplicated:
                metadata = result.get("metadata", {})
                doc_path = metadata.get("path", "")
                doc_title = metadata.get("doc_title", "")
                section_title = metadata.get("section_title", "")
                searchable_text = result.get("searchable_text", "")
                score = result.get("combined_score", 0)

                doc_results.append(
                    DocSearchResult(
                        title=doc_title or section_title or doc_path,
                        path=doc_path,
                        section=section_title,
                        snippet=self._create_snippet(searchable_text),
                        score=round(score, 3),
                        doc_url=self._make_doc_url(doc_path),
                    )
                )

            return DocSearchResultsResponse(
                message=f"Found {len(doc_results)} relevant documentation sections.",
                results=doc_results,
                count=len(doc_results),
                query=query,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return ErrorResponse(
                message=f"Failed to search documentation: {str(e)}",
                error="search_failed",
                session_id=session_id,
            )