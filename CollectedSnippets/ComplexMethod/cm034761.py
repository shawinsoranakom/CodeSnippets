async def _extract_from_js_bundles(self) -> List[str]:
        """Extract tokens from JavaScript bundles"""
        try:
            import aiohttp

            # Common Next.js bundle patterns
            bundle_patterns = [
                "/_next/static/chunks/",
                "/_next/static/app/",
            ]

            headers = self._get_headers()

            async with aiohttp.ClientSession() as session:
                # Try to fetch a page and extract script URLs
                async with session.get(
                    YUPP_BASE_URL,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    text = await response.text()

                # Extract script URLs
                script_urls = re.findall(r'src="([^"]*\.js[^"]*)"', text)

                for script_url in script_urls:
                    if any(pattern in script_url for pattern in bundle_patterns):
                        try:
                            full_url = (
                                script_url
                                if script_url.startswith("http")
                                else f"{YUPP_BASE_URL}{script_url}"
                            )
                            async with session.get(
                                full_url,
                                headers=headers,
                                timeout=aiohttp.ClientTimeout(total=5),
                            ) as js_response:
                                js_text = await js_response.text()

                            tokens = self._extract_tokens_from_html(js_text)
                            if tokens and len(tokens) >= MIN_REQUIRED_TOKENS:
                                print(
                                    f"[Yupp TokenExtractor] Extracted tokens "
                                    f"from JS bundle: {script_url}"
                                )
                                return tokens
                        except Exception:
                            continue

        except Exception as e:
            print(f"[Yupp TokenExtractor] JS bundle extraction failed: {e}")
            if os.getenv("DEBUG_MODE", "").lower() == "true":
                import traceback

                traceback.print_exc()

        return []