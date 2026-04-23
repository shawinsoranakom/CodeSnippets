async def virtual_scroll_demo(auto_mode=False):
    """
    📜 Virtual Scroll Demo
    Shows how to capture content from modern infinite scroll pages
    """
    import os
    import http.server
    import socketserver
    import threading
    from pathlib import Path

    print_banner(
        "📜 VIRTUAL SCROLL SUPPORT",
        "Capture all content from pages with DOM recycling"
    )

    # Explain the feature
    console.print(Panel(
        "[bold]What is Virtual Scroll?[/bold]\n\n"
        "Virtual Scroll handles modern web pages that use DOM recycling techniques:\n\n"
        "• [cyan]Twitter/X-like feeds[/cyan]: Content replaced as you scroll\n"
        "• [magenta]Instagram grids[/magenta]: Visual content with virtualization\n"
        "• [green]News feeds[/green]: Mixed content with different behaviors\n"
        "• [yellow]Infinite scroll[/yellow]: Captures everything, not just visible\n\n"
        "Without this, you'd only get the initially visible content!",
        title="Feature Overview",
        border_style="blue"
    ))

    await asyncio.sleep(2)

    # Start test server with HTML examples
    ASSETS_DIR = Path(__file__).parent / "assets"

    class TestServer:
        """Simple HTTP server to serve our test HTML files"""

        def __init__(self, port=8080):
            self.port = port
            self.httpd = None
            self.server_thread = None

        async def start(self):
            """Start the test server"""
            Handler = http.server.SimpleHTTPRequestHandler

            # Save current directory and change to assets directory
            self.original_cwd = os.getcwd()
            os.chdir(ASSETS_DIR)

            # Try to find an available port
            for _ in range(10):
                try:
                    self.httpd = socketserver.TCPServer(("", self.port), Handler)
                    break
                except OSError:
                    self.port += 1

            if self.httpd is None:
                raise RuntimeError("Could not find available port")

            self.server_thread = threading.Thread(target=self.httpd.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()

            # Give server time to start
            await asyncio.sleep(0.5)

            console.print(f"[green]Test server started on http://localhost:{self.port}[/green]")
            return self.port

        def stop(self):
            """Stop the test server"""
            if self.httpd:
                self.httpd.shutdown()
            # Restore original directory
            if hasattr(self, 'original_cwd'):
                os.chdir(self.original_cwd)

    server = TestServer()
    port = await server.start()

    try:
        # Demo 1: Twitter-like virtual scroll (content REPLACED)
        console.print("\n[bold yellow]Demo 1: Twitter-like Virtual Scroll - Content Replaced[/bold yellow]\n")
        console.print("[cyan]This simulates Twitter/X where only visible tweets exist in DOM[/cyan]\n")

        url = f"http://localhost:{port}/virtual_scroll_twitter_like.html"

        # First, crawl WITHOUT virtual scroll
        console.print("[red]WITHOUT Virtual Scroll:[/red]")

        config_normal = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        browser_config = BrowserConfig(
            headless=False if not auto_mode else True,
            viewport={"width": 1280, "height": 800}
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result_normal = await crawler.arun(url=url, config=config_normal)

            # Count tweets
            tweets_normal = len(set(re.findall(r'data-tweet-id="(\d+)"', result_normal.html)))
            console.print(f"• Captured only {tweets_normal} tweets (initial visible)")
            console.print(f"• HTML size: {len(result_normal.html):,} bytes\n")

        # Then, crawl WITH virtual scroll  
        console.print("[green]WITH Virtual Scroll:[/green]")

        virtual_config = VirtualScrollConfig(
            container_selector="#timeline",
            scroll_count=50,
            scroll_by="container_height",
            wait_after_scroll=0.2
        )

        config_virtual = CrawlerRunConfig(
            virtual_scroll_config=virtual_config,
            cache_mode=CacheMode.BYPASS
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result_virtual = await crawler.arun(url=url, config=config_virtual)

            tweets_virtual = len(set(re.findall(r'data-tweet-id="(\d+)"', result_virtual.html)))
            console.print(f"• Captured {tweets_virtual} tweets (all content)")
            console.print(f"• HTML size: {len(result_virtual.html):,} bytes")
            console.print(f"• [bold]{tweets_virtual / tweets_normal if tweets_normal > 0 else 'N/A':.1f}x more content![/bold]\n")

        if not auto_mode:
            console.print("\n[dim]Press Enter to continue to Demo 2...[/dim]")
            input()
        else:
            await asyncio.sleep(1)

        # Demo 2: Instagram Grid Example
        console.print("\n[bold yellow]Demo 2: Instagram Grid - Visual Grid Layout[/bold yellow]\n")
        console.print("[cyan]This shows how virtual scroll works with grid layouts[/cyan]\n")

        url2 = f"http://localhost:{port}/virtual_scroll_instagram_grid.html"

        # Configure for grid layout
        grid_config = VirtualScrollConfig(
            container_selector=".feed-container",
            scroll_count=100,  # Many scrolls for 999 posts
            scroll_by="container_height",
            wait_after_scroll=0.1 if auto_mode else 0.3
        )

        config = CrawlerRunConfig(
            virtual_scroll_config=grid_config,
            cache_mode=CacheMode.BYPASS,
            screenshot=True  # Take a screenshot
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url2, config=config)

            # Count posts in grid
            posts = re.findall(r'data-post-id="(\d+)"', result.html)
            unique_posts = sorted(set(int(id) for id in posts))

            console.print(f"[green]✅ Results:[/green]")
            console.print(f"• Posts captured: {len(unique_posts)} unique posts")
            if unique_posts:
                console.print(f"• Post IDs range: {min(unique_posts)} to {max(unique_posts)}")
                console.print(f"• Expected: 0 to 998 (999 posts total)")

                if len(unique_posts) >= 900:
                    console.print(f"• [bold green]SUCCESS! Captured {len(unique_posts)/999*100:.1f}% of all posts[/bold green]")

        if not auto_mode:
            console.print("\n[dim]Press Enter to continue to Demo 3...[/dim]")
            input()
        else:
            await asyncio.sleep(1)

        # Demo 3: Show the actual code
        console.print("\n[bold yellow]Demo 3: The Code - How It Works[/bold yellow]\n")

        # Show the actual implementation
        code = '''# Example: Crawling Twitter-like feed with virtual scroll
url = "http://localhost:8080/virtual_scroll_twitter_like.html"

# Configure virtual scroll
virtual_config = VirtualScrollConfig(
    container_selector="#timeline",      # The scrollable container
    scroll_count=50,                    # Max number of scrolls
    scroll_by="container_height",       # Scroll by container height
    wait_after_scroll=0.3              # Wait 300ms after each scroll
)

config = CrawlerRunConfig(
    virtual_scroll_config=virtual_config,
    cache_mode=CacheMode.BYPASS
)

# Use headless=False to watch it work!
browser_config = BrowserConfig(
    headless=False,
    viewport={"width": 1280, "height": 800}
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url=url, config=config)

    # Extract all tweets
    tweets = re.findall(r\'data-tweet-id="(\\d+)"\', result.html)
    unique_tweets = set(tweets)

    print(f"Captured {len(unique_tweets)} unique tweets!")
    print(f"Without virtual scroll: only ~10 tweets")
    print(f"With virtual scroll: all 500 tweets!")'''

        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Implementation", border_style="green"))

        # Summary
        console.print("\n[bold green]✨ Virtual Scroll Benefits:[/bold green]")
        console.print("• Captures ALL content, not just initially visible")
        console.print("• Handles Twitter, Instagram, LinkedIn, and more")
        console.print("• Smart scrolling with configurable parameters")
        console.print("• Essential for modern web scraping")
        console.print("• Works with any virtualized content\n")

    finally:
        # Stop the test server
        server.stop()
        console.print("[dim]Test server stopped[/dim]")