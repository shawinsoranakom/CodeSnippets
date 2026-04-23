async def demo_extract_css(client: httpx.AsyncClient):
    # Schema to extract book titles and prices
    book_schema = {
        "name": "BookList",
        "baseSelector": "ol.row li.col-xs-6",
        "fields": [
            {"name": "title", "selector": "article.product_pod h3 a",
                "type": "attribute", "attribute": "title"},
            {"name": "price", "selector": "article.product_pod .price_color", "type": "text"},
        ]
    }
    payload = {
        "urls": [BOOKS_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                    "params": {
                        "schema": {
                            "type": "dict", 
                            "value": book_schema
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 4a: JSON/CSS Extraction")

    if results and results[0].get("success") and results[0].get("extracted_content"):
        try:
            extracted_data = json.loads(results[0]["extracted_content"])
            if isinstance(extracted_data, list) and extracted_data:
                console.print("[cyan]Sample Extracted Books (CSS):[/]")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Title", style="dim")
                table.add_column("Price")
                for item in extracted_data[:5]:  # Show first 5
                    table.add_row(item.get('title', 'N/A'),
                                  item.get('price', 'N/A'))
                console.print(table)
            else:
                console.print(
                    "[yellow]CSS extraction did not return a list of results.[/]")
                console.print(extracted_data)
        except json.JSONDecodeError:
            console.print("[red]Failed to parse extracted_content as JSON.[/]")
        except Exception as e:
            console.print(
                f"[red]Error processing extracted CSS content: {e}[/]")