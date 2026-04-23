async def _process_document_batch(self, doc_batch: List[Path]) -> None:
        """Process a batch of documents in parallel"""
        contents = []
        for file_path in doc_batch:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    contents.append(f.read())
            except Exception as e:
                self.logger.error(f"Error reading {file_path}: {str(e)}")
                contents.append("")  # Add empty content to maintain batch alignment

        prompt = """Given a documentation file, generate a list of atomic facts where each fact:
1. Represents a single piece of knowledge
2. Contains variations in terminology for the same concept
3. References relevant code patterns if they exist
4. Is written in a way that would match natural language queries

Each fact should follow this format:
<main_concept>: <fact_statement> | <related_terms> | <code_reference>

Example Facts:
browser_config: Configure headless mode and browser type for AsyncWebCrawler | headless, browser_type, chromium, firefox | BrowserConfig(browser_type="chromium", headless=True)
redis_connection: Redis client connection requires host and port configuration | redis setup, redis client, connection params | Redis(host='localhost', port=6379, db=0)
pandas_filtering: Filter DataFrame rows using boolean conditions | dataframe filter, query, boolean indexing | df[df['column'] > 5]

Wrap your response in <index>...</index> tags.
"""

        # Prepare messages for batch processing
        messages_list = [
            [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nGenerate index for this documentation:\n\n{content}",
                }
            ]
            for content in contents
            if content
        ]

        try:
            responses = batch_completion(
                model="anthropic/claude-3-5-sonnet-latest",
                messages=messages_list,
                logger_fn=None,
            )

            # Process responses and save index files
            for response, file_path in zip(responses, doc_batch):
                try:
                    index_content_match = re.search(
                        r"<index>(.*?)</index>",
                        response.choices[0].message.content,
                        re.DOTALL,
                    )
                    if not index_content_match:
                        self.logger.warning(
                            f"No <index>...</index> content found for {file_path}"
                        )
                        continue

                    index_content = re.sub(
                        r"\n\s*\n", "\n", index_content_match.group(1)
                    ).strip()
                    if index_content:
                        index_file = file_path.with_suffix(".q.md")
                        with open(index_file, "w", encoding="utf-8") as f:
                            f.write(index_content)
                        self.logger.info(f"Created index file: {index_file}")
                    else:
                        self.logger.warning(
                            f"No index content found in response for {file_path}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error processing response for {file_path}: {str(e)}"
                    )

        except Exception as e:
            self.logger.error(f"Error in batch completion: {str(e)}")