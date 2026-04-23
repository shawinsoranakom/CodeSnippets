async def fetch_page_content(url: str, max_length: Optional[int] = 50000) -> str:
        """Helper function to fetch and convert webpage content to markdown"""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Convert relative URLs to absolute
                for tag in soup.find_all(["a", "img"]):
                    if tag.get("href"):
                        tag["href"] = urljoin(url, tag["href"])
                    if tag.get("src"):
                        tag["src"] = urljoin(url, tag["src"])

                h2t = html2text.HTML2Text()
                h2t.body_width = 0
                h2t.ignore_images = False
                h2t.ignore_emphasis = False
                h2t.ignore_links = False
                h2t.ignore_tables = False

                markdown = h2t.handle(str(soup))

                if max_length and len(markdown) > max_length:
                    markdown = markdown[:max_length] + "\n...(truncated)"

                return markdown.strip()

        except Exception as e:
            return f"Error fetching content: {str(e)}"