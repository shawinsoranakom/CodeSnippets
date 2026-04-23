def _format_results(
        self,
        results: list[SearchResult],
        answer: Optional[str] = None,
        include_raw_content: bool = False,
    ) -> str:
        """Format search results for display."""
        output_parts = []

        # Include AI-generated answer if available
        if answer:
            output_parts.append(f"## AI Summary\n{answer}\n")

        output_parts.append("## Search Results")

        for i, r in enumerate(results, 1):
            result_text = (
                f"### {i}. {r.title}\n"
                f"**URL:** {r.url}\n"
                f"**Excerpt:** {r.content or 'N/A'}"
            )
            if r.score is not None:
                result_text += f"\n**Relevance:** {r.score:.2f}"
            if include_raw_content and r.raw_content:
                # Truncate raw content to avoid overwhelming output
                content_preview = r.raw_content[:2000]
                if len(r.raw_content) > 2000:
                    content_preview += "... [truncated]"
                result_text += f"\n**Full Content:**\n{content_preview}"

            output_parts.append(result_text)

        return "\n\n".join(output_parts)