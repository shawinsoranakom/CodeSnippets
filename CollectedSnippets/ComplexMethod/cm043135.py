async def save_research_results(result: ResearchResult, config: ResearchConfig) -> Tuple[str, str]:
    """
    Save research results in JSON and Markdown formats

    Returns:
        Tuple of (json_path, markdown_path)
    """
    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename based on query and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = result.query.original_query[:50].replace(" ", "_").replace("/", "_")
    base_filename = f"{timestamp}_{query_slug}"

    json_path = None
    md_path = None

    # Save JSON
    if config.save_json:
        json_path = output_dir / f"{base_filename}.json"
        with open(json_path, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
        console.print(f"\n[green]💾 JSON saved: {json_path}[/green]")

    # Save Markdown
    if config.save_markdown:
        md_path = output_dir / f"{base_filename}.md"

        # Create formatted markdown
        md_content = [
            f"# Research Report: {result.query.original_query}",
            f"\n**Generated on:** {result.metadata.get('timestamp', 'N/A')}",
            f"\n**Domain:** {result.metadata.get('domain', 'N/A')}",
            f"\n**Processing time:** {result.metadata.get('duration', 'N/A')}",
            "\n---\n",
            "## Query Information",
            f"- **Original Query:** {result.query.original_query}",
            f"- **Enhanced Query:** {result.query.enhanced_query or 'N/A'}",
            f"- **Search Patterns:** {', '.join(result.query.search_patterns or [])}",
            "\n## Statistics",
            f"- **URLs Discovered:** {len(result.discovered_urls)}",
            f"- **URLs Crawled:** {len(result.crawled_content)}",
            f"- **Sources Cited:** {len(result.citations)}",
            "\n## Research Synthesis\n",
            result.synthesis,
            "\n## Sources\n"
        ]

        # Add citations
        for citation in result.citations:
            md_content.append(f"### [{citation['source_id']}] {citation['title']}")
            md_content.append(f"- **URL:** [{citation['url']}]({citation['url']})")
            md_content.append("")

        # Add discovered URLs summary
        md_content.extend([
            "\n## Discovered URLs (Top 10)\n",
            "| Score | URL | Title |",
            "|-------|-----|-------|"
        ])

        for url_data in result.discovered_urls[:10]:
            score = url_data.get('relevance_score', 0)
            url = url_data.get('url', '')
            title = 'N/A'
            if 'head_data' in url_data and url_data['head_data']:
                title = url_data['head_data'].get('title', 'N/A')[:60] + '...'
            md_content.append(f"| {score:.3f} | {url[:50]}... | {title} |")

        # Write markdown
        with open(md_path, 'w') as f:
            f.write('\n'.join(md_content))

        console.print(f"[green]📄 Markdown saved: {md_path}[/green]")

    return str(json_path) if json_path else None, str(md_path) if md_path else None