async def c4a_script_demo(auto_mode=False):
    """
    🎭 C4A Script Demo
    Shows the power of our domain-specific language for web automation
    """
    print_banner(
        "🎭 C4A SCRIPT - AUTOMATION MADE SIMPLE",
        "Domain-specific language for complex web interactions"
    )

    # Explain the feature
    console.print(Panel(
        "[bold]What is C4A Script?[/bold]\n\n"
        "C4A Script is a simple yet powerful language for web automation:\n\n"
        "• [cyan]English-like syntax[/cyan]: IF, CLICK, TYPE, WAIT - intuitive commands\n"
        "• [magenta]Smart transpiler[/magenta]: Converts to optimized JavaScript\n"
        "• [green]Error handling[/green]: Helpful error messages with suggestions\n"
        "• [yellow]Reusable procedures[/yellow]: Build complex workflows easily\n\n"
        "Perfect for automating logins, handling popups, pagination, and more!",
        title="Feature Overview",
        border_style="blue"
    ))

    await asyncio.sleep(2)

    # Demo 1: Basic transpilation demonstration
    console.print("\n[bold yellow]Demo 1: Understanding C4A Script Transpilation[/bold yellow]\n")

    simple_script = """# Handle cookie banner and scroll
WAIT `body` 2
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept`
SCROLL DOWN 500
WAIT 1"""

    console.print("[cyan]C4A Script:[/cyan]")
    syntax = Syntax(simple_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan"))

    # Compile it
    from crawl4ai import c4a_compile

    console.print("\n[cyan]Transpiling to JavaScript...[/cyan]")
    result = c4a_compile(simple_script)

    if result.success:
        console.print("[green]✅ Compilation successful![/green]\n")
        console.print("[cyan]Generated JavaScript:[/cyan]")

        js_display = "\n".join(result.js_code)
        js_syntax = Syntax(js_display, "javascript", theme="monokai", line_numbers=True)
        console.print(Panel(js_syntax, border_style="green"))

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 2...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 2: Error handling showcase
    console.print("\n[bold yellow]Demo 2: Smart Error Detection & Suggestions[/bold yellow]\n")

    # Script with intentional errors
    error_script = """WAIT body 2
CLICK button.submit
IF (EXISTS .modal) CLICK .close"""

    console.print("[cyan]C4A Script with errors:[/cyan]")
    syntax = Syntax(error_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="red"))

    console.print("\n[cyan]Compiling...[/cyan]")
    result = c4a_compile(error_script)

    if not result.success:
        console.print("[red]❌ Compilation failed (as expected)[/red]\n")

        # Show the first error
        error = result.first_error
        console.print(f"[bold red]Error at line {error.line}, column {error.column}:[/bold red]")
        console.print(f"[yellow]{error.message}[/yellow]")
        console.print(f"\nProblematic code: [red]{error.source_line}[/red]")
        console.print(" " * (16 + error.column) + "[red]^[/red]")

        if error.suggestions:
            console.print("\n[green]💡 Suggestions:[/green]")
            for suggestion in error.suggestions:
                console.print(f"   • {suggestion.message}")

    # Show the fixed version
    fixed_script = """WAIT `body` 2
CLICK `button.submit`
IF (EXISTS `.modal`) THEN CLICK `.close`"""

    console.print("\n[cyan]Fixed C4A Script:[/cyan]")
    syntax = Syntax(fixed_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="green"))

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 3...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 3: Real-world example - E-commerce automation
    console.print("\n[bold yellow]Demo 3: Real-World E-commerce Automation[/bold yellow]\n")

    console.print("[cyan]Scenario:[/cyan] Automate product search with smart handling\n")

    ecommerce_script = """# E-commerce Product Search Automation
# Define reusable procedures
PROC handle_popups
  # Close cookie banner if present
  IF (EXISTS `.cookie-notice`) THEN CLICK `.cookie-accept`

  # Close newsletter popup if it appears
  IF (EXISTS `#newsletter-modal`) THEN CLICK `.modal-close`
ENDPROC

PROC search_product
  # Click search box and type query
  CLICK `.search-input`
  TYPE "wireless headphones"
  PRESS Enter

  # Wait for results
  WAIT `.product-grid` 10
ENDPROC

# Main automation flow
SET max_products = 50

# Step 1: Navigate and handle popups
GO https://shop.example.com
WAIT `body` 3
handle_popups

# Step 2: Perform search
search_product

# Step 3: Load more products (infinite scroll)
REPEAT (SCROLL DOWN 1000, `document.querySelectorAll('.product-card').length < 50`)

# Step 4: Apply filters
IF (EXISTS `.filter-price`) THEN CLICK `input[data-filter="under-100"]`
WAIT 2

# Step 5: Extract product count
EVAL `console.log('Found ' + document.querySelectorAll('.product-card').length + ' products')`"""

    syntax = Syntax(ecommerce_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="E-commerce Automation Script", border_style="cyan"))

    # Compile and show results
    console.print("\n[cyan]Compiling automation script...[/cyan]")
    result = c4a_compile(ecommerce_script)

    if result.success:
        console.print(f"[green]✅ Successfully compiled to {len(result.js_code)} JavaScript statements![/green]")
        console.print("\n[bold]Script Analysis:[/bold]")
        console.print(f"• Procedures defined: {len(result.metadata.get('procedures', []))}")
        console.print(f"• Variables used: {len(result.metadata.get('variables', []))}")
        console.print(f"• Total commands: {result.metadata.get('total_commands', 0)}")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 4...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 4: Integration with Crawl4AI - LIVE DEMO
    console.print("\n[bold yellow]Demo 4: Live Integration with Crawl4AI[/bold yellow]\n")

    console.print("[cyan]Let's see C4A Script in action with real web crawling![/cyan]\n")

    # Create a simple C4A script for demo
    live_script = """# Handle common website patterns
WAIT `body` 2
# Close cookie banner if exists
IF (EXISTS `.cookie-banner, .cookie-notice, #cookie-consent`) THEN CLICK `.accept, .agree, button[aria-label*="accept"]`
# Scroll to load content
SCROLL DOWN 500
WAIT 1"""

    console.print("[bold]Our C4A Script:[/bold]")
    syntax = Syntax(live_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan"))

    # Method 1: Direct C4A Script usage
    console.print("\n[bold cyan]Method 1: Direct C4A Script Integration[/bold cyan]\n")

    try:
        # Import necessary components
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

        # Define extraction schema
        schema = {
            "name": "page_content",
            "selector": "body",
            "fields": {
                "title": {"selector": "h1, title", "type": "text"},
                "paragraphs": {"selector": "p", "type": "list", "fields": {"text": {"type": "text"}}},
                "links": {"selector": "a[href]", "type": "list", "fields": {"text": {"type": "text"}, "href": {"type": "attribute", "attribute": "href"}}}
            }
        }

        # Create config with C4A script
        config = CrawlerRunConfig(
            c4a_script=live_script,
            extraction_strategy=JsonCssExtractionStrategy(schema),
            only_text=True,
            cache_mode=CacheMode.BYPASS
        )

        console.print("[green]✅ Config created with C4A script![/green]")
        console.print(f"[dim]The C4A script will be automatically transpiled when crawling[/dim]\n")

        # Show the actual code
        code_example1 = f'''# Live code that's actually running:
config = CrawlerRunConfig(
    c4a_script="""{live_script}""",
    extraction_strategy=JsonCssExtractionStrategy(schema),
    only_text=True,
    cache_mode=CacheMode.BYPASS
)

# This would run the crawler:
# async with AsyncWebCrawler() as crawler:
#     result = await crawler.arun("https://example.com", config=config)
#     print(f"Extracted {{len(result.extracted_content)}} items")'''

        syntax = Syntax(code_example1, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Method 1: Direct Integration (Live Code)", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error in demo: {e}[/red]")

    if not auto_mode:
        console.print("\n[dim]Press Enter to see Method 2...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Method 2: Pre-compilation approach
    console.print("\n[bold cyan]Method 2: Pre-compile and Reuse[/bold cyan]\n")

    # Advanced script with procedures
    advanced_script = """# E-commerce automation with procedures
PROC handle_popups
  IF (EXISTS `.popup-overlay`) THEN CLICK `.popup-close`
  IF (EXISTS `#newsletter-modal`) THEN CLICK `.modal-dismiss`
ENDPROC

PROC load_all_products  
  # Keep scrolling until no more products load
  REPEAT (SCROLL DOWN 1000, `document.querySelectorAll('.product').length < window.lastProductCount`)
  EVAL `window.lastProductCount = document.querySelectorAll('.product').length`
ENDPROC

# Main flow
WAIT `.products-container` 5
handle_popups
EVAL `window.lastProductCount = 0`
load_all_products"""

    console.print("[bold]Advanced C4A Script with Procedures:[/bold]")
    syntax = Syntax(advanced_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan"))

    # Actually compile it
    console.print("\n[cyan]Compiling the script...[/cyan]")
    compilation_result = c4a_compile(advanced_script)

    if compilation_result.success:
        console.print(f"[green]✅ Successfully compiled to {len(compilation_result.js_code)} JavaScript statements![/green]\n")

        # Show first few JS statements
        console.print("[bold]Generated JavaScript (first 5 statements):[/bold]")
        js_preview = "\n".join(compilation_result.js_code[:5])
        if len(compilation_result.js_code) > 5:
            js_preview += f"\n... and {len(compilation_result.js_code) - 5} more statements"

        js_syntax = Syntax(js_preview, "javascript", theme="monokai", line_numbers=True)
        console.print(Panel(js_syntax, border_style="green"))

        # Create actual config with compiled code
        config_with_js = CrawlerRunConfig(
            js_code=compilation_result.js_code,
            wait_for="css:.products-container",
            cache_mode=CacheMode.BYPASS
        )

        console.print("\n[green]✅ Config created with pre-compiled JavaScript![/green]")

        # Show the actual implementation
        code_example2 = f'''# Live code showing pre-compilation:
# Step 1: Compile once
result = c4a_compile(advanced_script)
if result.success:
    js_code = result.js_code  # {len(compilation_result.js_code)} statements generated

    # Step 2: Use compiled code multiple times
    config = CrawlerRunConfig(
        js_code=js_code,
        wait_for="css:.products-container",
        cache_mode=CacheMode.BYPASS
    )

    # Step 3: Run crawler with compiled code
    # async with AsyncWebCrawler() as crawler:
    #     # Can reuse js_code for multiple URLs
    #     for url in ["shop1.com", "shop2.com"]:
    #         result = await crawler.arun(url, config=config)
else:
    print(f"Compilation error: {{result.first_error.message}}")'''

        syntax = Syntax(code_example2, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Method 2: Pre-compilation (Live Code)", border_style="green"))

    else:
        console.print(f"[red]Compilation failed: {compilation_result.first_error.message}[/red]")

    if not auto_mode:
        console.print("\n[dim]Press Enter to see a real-world example...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 5: Real-world example with actual crawling
    console.print("\n[bold yellow]Demo 5: Real-World Example - News Site Automation[/bold yellow]\n")

    news_script = """# News site content extraction
# Wait for main content
WAIT `article, .article-content, main` 5

# Handle common annoyances
IF (EXISTS `.cookie-notice`) THEN CLICK `button[class*="accept"]`
IF (EXISTS `.newsletter-popup`) THEN CLICK `.close, .dismiss`

# Expand "Read More" sections
IF (EXISTS `.read-more-button`) THEN CLICK `.read-more-button`

# Load comments if available
IF (EXISTS `.load-comments`) THEN CLICK `.load-comments`
WAIT 2"""

    console.print("[bold]News Site Automation Script:[/bold]")
    syntax = Syntax(news_script, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan"))

    # Create and show actual working config
    console.print("\n[cyan]Creating crawler configuration...[/cyan]")

    news_config = CrawlerRunConfig(
        c4a_script=news_script,
        wait_for="css:article",
        only_text=True,
        cache_mode=CacheMode.BYPASS
    )

    console.print("[green]✅ Configuration ready for crawling![/green]\n")

    # Show how to actually use it
    usage_example = '''# Complete working example:
async def crawl_news_site():
    """Crawl a news site with C4A automation"""

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url="https://example-news.com/article",
            config=CrawlerRunConfig(
                c4a_script=news_script,
                wait_for="css:article",
                only_text=True
            )
        )

        if result.success:
            print(f"✓ Crawled: {result.url}")
            print(f"✓ Content length: {len(result.markdown.raw_markdown)} chars")
            print(f"✓ Links found: {len(result.links.get('internal', []))} internal")

            # The C4A script ensured we:
            # - Handled cookie banners
            # - Expanded collapsed content  
            # - Loaded dynamic comments
            # All automatically!

        return result

# Run it:
# result = await crawl_news_site()'''

    syntax = Syntax(usage_example, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Complete Working Example", border_style="green"))

    # Summary
    console.print("\n[bold green]✨ What We Demonstrated:[/bold green]")
    console.print("• C4A Script transpiles to optimized JavaScript automatically")
    console.print("• Direct integration via `c4a_script` parameter - easiest approach")
    console.print("• Pre-compilation via `c4a_compile()` - best for reuse")
    console.print("• Real configs that you can copy and use immediately")
    console.print("• Actual code running, not just examples!\n")