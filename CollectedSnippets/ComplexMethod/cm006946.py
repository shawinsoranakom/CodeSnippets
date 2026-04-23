def fetch_url_contents(self) -> list[dict]:
        """Load documents from the configured URLs.

        Returns:
            List[Data]: List of Data objects containing the fetched content

        Raises:
            ValueError: If no valid URLs are provided or if there's an error loading documents
        """
        try:
            urls = list({self.ensure_url(url) for url in self.urls if url.strip()})
            logger.debug(f"URLs: {urls}")
            if not urls:
                msg = "No valid URLs provided."
                raise ValueError(msg)

            all_docs = []
            for url in urls:
                logger.debug(f"Loading documents from {url}")

                try:
                    loader = self._create_loader(url)
                    docs = loader.load()

                    if not docs:
                        logger.warning(f"No documents found for {url}")
                        continue

                    logger.debug(f"Found {len(docs)} documents from {url}")
                    all_docs.extend(docs)

                except requests.exceptions.RequestException as e:
                    logger.exception(f"Error loading documents from {url}: {e}")
                    continue

            if not all_docs:
                msg = "No documents were successfully loaded from any URL"
                raise ValueError(msg)

            # data = [Data(text=doc.page_content, **doc.metadata) for doc in all_docs]
            data = [
                {
                    "text": safe_convert(doc.page_content, clean_data=True),
                    "url": doc.metadata.get("source", ""),
                    "title": doc.metadata.get("title", ""),
                    "description": doc.metadata.get("description", ""),
                    "content_type": doc.metadata.get("content_type", ""),
                    "language": doc.metadata.get("language", ""),
                }
                for doc in all_docs
            ]
        except Exception as e:
            error_msg = e.message if hasattr(e, "message") else e
            msg = f"Error loading documents: {error_msg!s}"
            logger.exception(msg)
            raise ValueError(msg) from e
        return data