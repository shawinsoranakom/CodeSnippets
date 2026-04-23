def _generate_documents(self, html_content: str) -> Iterator[Document]:
        """Private method that performs a DFS traversal over the DOM and yields.

        Document objects on-the-fly. This approach maintains the same splitting logic
        (headers vs. non-headers, chunking, etc.) while walking the DOM explicitly in
        code.

        Args:
            html_content: The raw HTML content.

        Yields:
            Document objects as they are created.

        Raises:
            ImportError: If BeautifulSoup is not installed.
        """
        if not _HAS_BS4:
            msg = (
                "Unable to import BeautifulSoup. Please install via `pip install bs4`."
            )
            raise ImportError(msg)

        soup = BeautifulSoup(html_content, "html.parser")
        body = soup.body or soup

        # Dictionary of active headers:
        #   key = user-defined header name (e.g. "Header 1")
        #   value = tuple of header_text, level, dom_depth
        active_headers: dict[str, tuple[str, int, int]] = {}
        current_chunk: list[str] = []

        def finalize_chunk() -> Document | None:
            """Finalize the accumulated chunk into a single Document."""
            if not current_chunk:
                return None

            final_text = "  \n".join(line for line in current_chunk if line.strip())
            current_chunk.clear()
            if not final_text.strip():
                return None

            final_meta = {k: v[0] for k, v in active_headers.items()}
            return Document(page_content=final_text, metadata=final_meta)

        # We'll use a stack for DFS traversal
        stack = [body]
        while stack:
            node = stack.pop()
            children = list(node.children)

            stack.extend(
                child for child in reversed(children) if isinstance(child, Tag)
            )

            tag = getattr(node, "name", None)
            if not tag:
                continue

            text_elements = [
                str(child).strip() for child in _find_all_strings(node, recursive=False)
            ]
            node_text = " ".join(elem for elem in text_elements if elem)
            if not node_text:
                continue

            dom_depth = len(list(node.parents))

            # If this node is one of our headers
            if tag in self.header_tags:
                # If we're aggregating, finalize whatever chunk we had
                if not self.return_each_element:
                    doc = finalize_chunk()
                    if doc:
                        yield doc

                # Determine numeric level (h1->1, h2->2, etc.)
                try:
                    level = int(tag[1:])
                except ValueError:
                    level = 9999

                # Remove any active headers that are at or deeper than this new level
                headers_to_remove = [
                    k for k, (_, lvl, d) in active_headers.items() if lvl >= level
                ]
                for key in headers_to_remove:
                    del active_headers[key]

                # Add/Update the active header
                header_name = self.header_mapping[tag]
                active_headers[header_name] = (node_text, level, dom_depth)

                # Always yield a Document for the header
                header_meta = {k: v[0] for k, v in active_headers.items()}
                yield Document(page_content=node_text, metadata=header_meta)

            else:
                headers_out_of_scope = [
                    k for k, (_, _, d) in active_headers.items() if dom_depth < d
                ]
                for key in headers_out_of_scope:
                    del active_headers[key]

                if self.return_each_element:
                    # Yield each element's text as its own Document
                    meta = {k: v[0] for k, v in active_headers.items()}
                    yield Document(page_content=node_text, metadata=meta)
                else:
                    # Accumulate text in our chunk
                    current_chunk.append(node_text)

        # If we're aggregating and have leftover chunk, yield it
        if not self.return_each_element:
            doc = finalize_chunk()
            if doc:
                yield doc