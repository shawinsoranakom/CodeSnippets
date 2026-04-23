def crawl_documentation(firecrawl_api_key: str, url: str, output_dir: Optional[str] = None):
    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
    pages = []

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    response = firecrawl.crawl_url(
        url,
        params={
            'limit': 5,
            'scrapeOptions': {
                'formats': ['markdown', 'html']
            }
        }
    )

    while True:
        for page in response.get('data', []):
            content = page.get('markdown') or page.get('html', '')
            metadata = page.get('metadata', {})
            source_url = metadata.get('sourceURL', '')

            if output_dir and content:
                filename = f"{uuid.uuid4()}.md"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            pages.append({
                "content": content,
                "url": source_url,
                "metadata": {
                    "title": metadata.get('title', ''),
                    "description": metadata.get('description', ''),
                    "language": metadata.get('language', 'en'),
                    "crawl_date": datetime.now().isoformat()
                }
            })

        next_url = response.get('next')
        if not next_url:
            break

        response = firecrawl.get(next_url)
        time.sleep(1)

    return pages