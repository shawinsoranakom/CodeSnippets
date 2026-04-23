def print_result_summary(results: List[Dict[str, Any]], title: str = "Crawl Results Summary", max_items: int = 3):
    """Prints a concise summary of crawl results."""
    if not results:
        console.print(f"[yellow]{title}: No results received.[/]")
        return

    console.print(Panel(f"[bold]{title}[/]",
                  border_style="green", expand=False))
    count = 0
    for result in results:
        if count >= max_items:
            console.print(
                f"... (showing first {max_items} of {len(results)} results)")
            break
        count += 1
        success_icon = "[green]✔[/]" if result.get('success') else "[red]✘[/]"
        url = result.get('url', 'N/A')
        status = result.get('status_code', 'N/A')
        content_info = ""
        if result.get('extracted_content'):
            content_str = json.dumps(result['extracted_content'])
            snippet = (
                content_str[:70] + '...') if len(content_str) > 70 else content_str
            content_info = f" | Extracted: [cyan]{snippet}[/]"
        elif result.get('markdown'):
            content_info = f" | Markdown: [cyan]Present[/]"
        elif result.get('html'):
            content_info = f" | HTML Size: [cyan]{len(result['html'])}[/]"

        console.print(
            f"{success_icon} URL: [link={url}]{url}[/link] (Status: {status}){content_info}")
        if "metadata" in result and "depth" in result["metadata"]:
            console.print(f"  Depth: {result['metadata']['depth']}")
        if not result.get('success') and result.get('error_message'):
            console.print(f"  [red]Error: {result['error_message']}[/]")