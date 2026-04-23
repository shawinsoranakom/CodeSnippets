async def _attempt_extraction(self) -> bool:
        """
        Attempt to extract fresh tokens from Yupp AI
        Uses multiple strategies for robustness
        """
        async with self._lock:
            if self._extraction_in_progress:
                return False
            self._extraction_in_progress = True

        try:
            # Try multiple extraction methods
            extracted_tokens = await self._extract_from_chat_page()

            if not extracted_tokens:
                extracted_tokens = await self._extract_from_main_page()

            if not extracted_tokens:
                extracted_tokens = await self._extract_from_js_bundles()

            if extracted_tokens and len(extracted_tokens) >= MIN_REQUIRED_TOKENS:
                # Update cache with extracted tokens
                async with self._lock:
                    self._cache.tokens = {
                        "new_conversation": extracted_tokens[0],
                        "existing_conversation": extracted_tokens[1]
                        if len(extracted_tokens) > 1
                        else extracted_tokens[0],
                    }
                    self._cache.last_updated = datetime.now()
                    self._cache.failed_attempts = 0
                return True

            return False

        except Exception as e:
            print(f"[Yupp TokenExtractor] Extraction failed: {e}")
            if os.getenv("DEBUG_MODE", "").lower() == "true":
                import traceback

                traceback.print_exc()
            return False
        finally:
            async with self._lock:
                self._extraction_in_progress = False