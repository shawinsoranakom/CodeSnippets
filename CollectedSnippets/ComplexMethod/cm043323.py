async def interactive_manager(self, crawl_callback=None):
        """
        Launch an interactive profile management console.

        Args:
            crawl_callback (callable, optional): Function to call when selecting option to use 
                a profile for crawling. It will be called with (profile_path, url).

        Example:
            ```python
            profiler = BrowserProfiler()

            # Define a custom crawl function
            async def my_crawl_function(profile_path, url):
                print(f"Crawling {url} with profile {profile_path}")
                # Implement your crawling logic here

            # Start interactive manager
            await profiler.interactive_manager(crawl_callback=my_crawl_function)
            ```
        """
        while True:
            self.logger.info("\nProfile Management Options:", tag="MENU")
            self.logger.info("1. Create a new profile", tag="MENU", base_color=LogColor.GREEN)
            self.logger.info("2. List available profiles", tag="MENU", base_color=LogColor.YELLOW)
            self.logger.info("3. Delete a profile", tag="MENU", base_color=LogColor.RED)

            # Only show crawl option if callback provided
            if crawl_callback:
                self.logger.info("4. Use a profile to crawl a website", tag="MENU", base_color=LogColor.CYAN)
                self.logger.info("5. Exit", tag="MENU", base_color=LogColor.MAGENTA)
                exit_option = "5"
            else:
                self.logger.info("4. Exit", tag="MENU", base_color=LogColor.MAGENTA)
                exit_option = "4"

            self.logger.info(f"\n[cyan]Enter your choice (1-{exit_option}): [/cyan]", end="")
            choice = input()

            if choice == "1":
                # Create new profile
                self.console.print("[green]Enter a name for the new profile (or press Enter for auto-generated name): [/green]", end="")
                name = input()
                await self.create_profile(name or None)

            elif choice == "2":
                # List profiles
                profiles = self.list_profiles()

                if not profiles:
                    self.logger.warning("  No profiles found. Create one first with option 1.", tag="PROFILES")
                    continue

                # Print profile information 
                self.logger.info("\nAvailable profiles:", tag="PROFILES")
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    self.logger.info(f"    Path: {profile['path']}", tag="PROFILES", base_color=LogColor.YELLOW)
                    self.logger.info(f"    Created: {profile['created'].strftime('%Y-%m-%d %H:%M:%S')}", tag="PROFILES")
                    self.logger.info(f"    Browser type: {profile['type']}", tag="PROFILES")
                    self.logger.info("", tag="PROFILES")  # Empty line for spacing

            elif choice == "3":
                # Delete profile
                profiles = self.list_profiles()
                if not profiles:
                    self.logger.warning("No profiles found to delete", tag="PROFILES")
                    continue

                # Display numbered list
                self.logger.info("\nAvailable profiles:", tag="PROFILES", base_color=LogColor.YELLOW)
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")

                # Get profile to delete
                self.console.print("[red]Enter the number of the profile to delete (or 'c' to cancel): [/red]", end="")
                profile_idx = input()
                if profile_idx.lower() == 'c':
                    continue

                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_name = profiles[idx]["name"]
                        self.logger.info(f"Deleting profile: [yellow]{profile_name}[/yellow]", tag="PROFILES")

                        # Confirm deletion
                        self.console.print("[red]Are you sure you want to delete this profile? (y/n): [/red]", end="")
                        confirm = input()
                        if confirm.lower() == 'y':
                            success = self.delete_profile(profiles[idx]["path"])

                            if success:
                                self.logger.success(f"Profile {profile_name} deleted successfully", tag="PROFILES")
                            else:
                                self.logger.error(f"Failed to delete profile {profile_name}", tag="PROFILES")
                    else:
                        self.logger.error("Invalid profile number", tag="PROFILES")
                except ValueError:
                    self.logger.error("Please enter a valid number", tag="PROFILES")

            elif choice == "4" and crawl_callback:
                # Use profile to crawl a site
                profiles = self.list_profiles()
                if not profiles:
                    self.logger.warning("No profiles found. Create one first.", tag="PROFILES")
                    continue

                # Display numbered list
                self.logger.info("\nAvailable profiles:", tag="PROFILES", base_color=LogColor.YELLOW)
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")

                # Get profile to use
                self.console.print("[cyan]Enter the number of the profile to use (or 'c' to cancel): [/cyan]", end="")
                profile_idx = input()
                if profile_idx.lower() == 'c':
                    continue

                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_path = profiles[idx]["path"]
                        self.console.print("[cyan]Enter the URL to crawl: [/cyan]", end="")
                        url = input()
                        if url:
                            # Call the provided crawl callback
                            await crawl_callback(profile_path, url)
                        else:
                            self.logger.error("No URL provided", tag="CRAWL")
                    else:
                        self.logger.error("Invalid profile number", tag="PROFILES")
                except ValueError:
                    self.logger.error("Please enter a valid number", tag="PROFILES")

            elif choice == exit_option:
                # Exit
                self.logger.info("Exiting profile management", tag="MENU")
                break

            else:
                self.logger.error(f"Invalid choice. Please enter a number between 1 and {exit_option}.", tag="MENU")