async def manage_profiles():
    """Interactive profile management menu"""
    profiler = BrowserProfiler()

    options = {
        "1": "List profiles",
        "2": "Create new profile",
        "3": "Delete profile",
        "4": "Use a profile to crawl a website",
        "5": "Exit",
    }

    while True:
        console.print(Panel("[bold cyan]Browser Profile Manager[/bold cyan]", border_style="cyan"))

        for key, value in options.items():
            color = "green" if key == "1" else "yellow" if key == "2" else "red" if key == "3" else "blue" if key == "4" else "cyan"
            console.print(f"[{color}]{key}[/{color}]. {value}")

        choice = Prompt.ask("Enter choice", choices=list(options.keys()), default="1")

        if choice == "1":
            # List profiles
            profiles = profiler.list_profiles()
            display_profiles_table(profiles)

        elif choice == "2":
            # Create profile
            await create_profile_interactive(profiler)

        elif choice == "3":
            # Delete profile
            delete_profile_interactive(profiler)

        elif choice == "4":
            # Use profile to crawl
            await use_profile_to_crawl()

        elif choice == "5":
            # Exit
            console.print("[cyan]Exiting profile manager.[/cyan]")
            break

        # Add a separator between operations
        console.print("\n")