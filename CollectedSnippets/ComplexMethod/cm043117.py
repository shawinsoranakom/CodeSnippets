async def demo_extract_llm(client: httpx.AsyncClient):
    if not os.getenv("OPENAI_API_KEY"):  # Basic check for a common key
        console.rule(
            "[bold yellow]Demo 4b: LLM Extraction (SKIPPED)[/]", style="yellow")
        console.print(
            "Set an LLM API key (e.g., OPENAI_API_KEY) in your .env file or environment.")
        return

    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "instruction": "Extract title and author into JSON.",
                        "llm_config": {  # Optional: Specify provider if not default
                            "type": "LLMConfig",
                            "params": {}
                            # Relies on server's default provider from config.yml & keys from .llm.env
                            # "params": {
                                # "provider": "openai/gpt-4o-mini",
                                # "api_key": os.getenv("OPENAI_API_KEY")  # Optional: Override key
                            # }
                        },
                        "schema": {  # Request structured output
                            "type": "dict",
                            "value": {
                                "title": "BookInfo", "type": "object",
                                "properties": {
                                    "book_title": {"type": "string"},
                                    "book_author": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 4b: LLM Extraction")

    if results and results[0].get("success") and results[0].get("extracted_content"):
        try:
            extracted_data = json.loads(results[0]["extracted_content"])
            # Handle potential list wrapper from server
            if isinstance(extracted_data, list) and extracted_data:
                extracted_data = extracted_data[0]

            if isinstance(extracted_data, dict):
                console.print("[cyan]Extracted Data (LLM):[/]")
                syntax = Syntax(json.dumps(extracted_data, indent=2),
                                "json", theme="monokai", line_numbers=False)
                console.print(Panel(syntax, border_style="cyan", expand=False))
            else:
                console.print(
                    "[yellow]LLM extraction did not return expected dictionary.[/]")
                console.print(extracted_data)
        except json.JSONDecodeError:
            console.print(
                "[red]Failed to parse LLM extracted_content as JSON.[/]")
        except Exception as e:
            console.print(
                f"[red]Error processing extracted LLM content: {e}[/]")