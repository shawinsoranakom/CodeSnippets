async def generate_research_synthesis(
    query: str, 
    crawled_content: List[Dict]
) -> Tuple[str, List[Dict]]:
    """
    Use LLM to synthesize research findings:
    - Analyze all crawled content
    - Generate comprehensive answer
    - Extract citations and references
    """
    if not crawled_content:
        return "No content available for synthesis.", []

    console.print("\n[cyan]🤖 Generating research synthesis...[/cyan]")

    # Prepare content for LLM
    content_sections = []
    for i, content in enumerate(crawled_content, 1):
        section = f"""
SOURCE {i}:
Title: {content['title']}
URL: {content['url']}
Content Preview:
{content['markdown'][:1500]}...
"""
        content_sections.append(section)

    combined_content = "\n---\n".join(content_sections)

    try:
        response = await litellm.acompletion(
            model="gemini/gemini-2.5-flash-preview-04-17",
            messages=[{
                "role": "user",
                "content": f"""Research Query: "{query}"

Based on the following sources, provide a comprehensive research synthesis.

{combined_content}

Please provide:
1. An executive summary (2-3 sentences)
2. Key findings (3-5 bullet points)
3. Detailed analysis (2-3 paragraphs)
4. Future implications or trends

Format your response with clear sections and cite sources using [Source N] notation.
Keep the total response under 800 words."""
            }],
            # reasoning_effort="medium",
            temperature=0.7
        )

        synthesis = response.choices[0].message.content

        # Extract citations from the synthesis
        citations = []
        for i, content in enumerate(crawled_content, 1):
            if f"[Source {i}]" in synthesis or f"Source {i}" in synthesis:
                citations.append({
                    'source_id': i,
                    'title': content['title'],
                    'url': content['url']
                })

        return synthesis, citations

    except Exception as e:
        console.print(f"[red]❌ Synthesis generation failed: {e}[/red]")
        # Fallback to simple summary
        summary = f"Research on '{query}' found {len(crawled_content)} relevant articles:\n\n"
        for content in crawled_content[:3]:
            summary += f"- {content['title']}\n  {content['url']}\n\n"
        return summary, []