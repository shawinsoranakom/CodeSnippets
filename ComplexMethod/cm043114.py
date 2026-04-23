async def demo_param_css_selector(client: httpx.AsyncClient):
    css_selector = ".main-content"  # Using the suggested correct selector
    payload = {
        "urls": [PYTHON_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "css_selector": css_selector  # Target specific div
                # No extraction strategy is needed to demo this parameter's effect on input HTML
            }
        }
    }
    results = await make_request(client, "/crawl", payload, f"Demo 3a: Using css_selector ('{css_selector}')")

    if results:
        result = results[0]
        if result['success'] and result.get('html'):
            # Check if the returned HTML is likely constrained
            # A simple check: does it contain expected content from within the selector,
            # and does it LACK content known to be outside (like footer links)?
            html_content = result['html']
            # Text likely within .main-content somewhere
            content_present = 'Python Software Foundation' in html_content
            # Text likely in the footer, outside .main-content
            footer_absent = 'Legal Statements' not in html_content

            console.print(
                f"  Content Check: Text inside '{css_selector}' likely present? {'[green]Yes[/]' if content_present else '[red]No[/]'}")
            console.print(
                f"  Content Check: Text outside '{css_selector}' (footer) likely absent? {'[green]Yes[/]' if footer_absent else '[red]No[/]'}")

            if not content_present or not footer_absent:
                console.print(
                    f"  [yellow]Note:[/yellow] HTML filtering might not be precise or page structure changed. Result HTML length: {len(html_content)}")
            else:
                console.print(
                    f"  [green]Verified:[/green] Returned HTML appears limited by css_selector. Result HTML length: {len(html_content)}")

        elif result['success']:
            console.print(
                "[yellow]HTML content was empty in the successful result.[/]")