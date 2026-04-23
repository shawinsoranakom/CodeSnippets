async def main():
    async with AsyncUrlSeeder() as seed:
        # Interactive menu
        sections = {
            "1": ("Basic URL Discovery", section_1_basic_exploration),
            "2": ("Cache Management Demo", section_2_cache_demo),
            "3": ("Live Check & Metadata Extraction", section_3_live_head),
            "4": ("BM25 Relevance Scoring", section_4_bm25_scoring),
            "5": ("Complete Pipeline (Discover → Filter → Crawl)", section_5_keyword_filter_to_agent),
            "6": ("Multi-Domain Discovery", section_6_multi_domain),
            "7": ("Run All Demos", None)
        }

        console.print("\n[bold]Available Demos:[/bold]")
        for key, (title, _) in sections.items():
            console.print(f"  {key}. {title}")

        choice = Prompt.ask("\n[cyan]Which demo would you like to run?[/cyan]", 
                           choices=list(sections.keys()), 
                           default="7")

        console.print()

        if choice == "7":
            # Run all demos
            for key, (title, func) in sections.items():
                if key != "7" and func:
                    await func(seed)
                    if key != "6":  # Don't pause after the last demo
                        if not Confirm.ask("\n[yellow]Continue to next demo?[/yellow]", default=True):
                            break
                        console.print()
        else:
            # Run selected demo
            _, func = sections[choice]
            await func(seed)

        console.rule("[bold green]Demo Complete ✔︎")