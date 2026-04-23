async def interactive_menu():
    """Interactive menu to select demos"""
    from rich.prompt import Prompt

    demos = {
        "1": ("Link Preview & Scoring", link_preview_demo),
        "2": ("Adaptive Crawling", adaptive_crawling_demo),
        "3": ("Virtual Scroll", virtual_scroll_demo),
        "4": ("URL Seeder", url_seeder_demo),
        "5": ("C4A Script", c4a_script_demo),
        "6": ("LLM Context Builder", lambda auto: console.print("[yellow]LLM Context demo coming soon![/yellow]")),
        "7": ("Run All Demos", None),  # Special case
        "0": ("Exit", None)
    }

    while True:
        # Clear screen for better presentation
        console.clear()

        print_banner(
            "🚀 CRAWL4AI v0.7.0 SHOWCASE",
            "Interactive Demo Menu"
        )

        console.print("\n[bold cyan]Select a demo to run:[/bold cyan]\n")

        for key, (name, _) in demos.items():
            if key == "0":
                console.print(f"\n[dim]{key}. {name}[/dim]")
            else:
                console.print(f"{key}. {name}")

        choice = Prompt.ask("\n[bold]Enter your choice[/bold]", choices=list(demos.keys()))

        if choice == "0":
            console.print("\n[yellow]Thanks for exploring Crawl4AI v0.7.0![/yellow]")
            break
        elif choice == "7":
            # Run all demos
            console.clear()
            for key in ["1", "3", "4", "5"]:  # Link Preview, Virtual Scroll, URL Seeder, C4A Script
                name, demo_func = demos[key]
                if demo_func:
                    await demo_func(auto_mode=True)
                    console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
        else:
            name, demo_func = demos[choice]
            if demo_func:
                console.clear()
                await demo_func(auto_mode=False)
                console.print("\n[dim]Press Enter to return to menu...[/dim]")
                input()