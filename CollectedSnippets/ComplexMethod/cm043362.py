def _create_smart_chunks(self, html_content: str) -> Tuple[List[str], bool]:
        """
        Create smart chunks of table HTML, preserving headers in each chunk.

        Returns:
            Tuple of (chunks, has_headers)
        """
        if self.verbose:
            self._log("info", f"Creating smart chunks from {len(html_content)} characters of HTML")

        header_rows, body_rows, footer_rows, has_headers = self._extract_table_structure(html_content)

        if self.verbose:
            self._log("info", f"Table structure: {len(header_rows)} header rows, {len(body_rows)} body rows, {len(footer_rows)} footer rows")

        if not body_rows:
            if self.verbose:
                self._log("info", "No body rows to chunk, returning full content")
            return [html_content], has_headers  # No rows to chunk

        # Create header HTML (to be included in every chunk)
        header_html = ""
        if header_rows:
            thead_element = etree.Element("thead")
            for row in header_rows:
                thead_element.append(row)
            header_html = etree.tostring(thead_element, encoding='unicode')

        # Calculate rows per chunk based on token estimates
        chunks = []
        current_chunk_rows = []
        current_token_count = self._estimate_tokens(header_html)

        for row in body_rows:
            row_html = etree.tostring(row, encoding='unicode')
            row_tokens = self._estimate_tokens(row_html)

            # Check if adding this row would exceed threshold
            if current_chunk_rows and (current_token_count + row_tokens > self.chunk_token_threshold):
                # Create chunk with current rows
                chunk_html = self._create_chunk_html(header_html, current_chunk_rows, None)
                chunks.append(chunk_html)

                # Start new chunk
                current_chunk_rows = [row_html]
                current_token_count = self._estimate_tokens(header_html) + row_tokens
            else:
                current_chunk_rows.append(row_html)
                current_token_count += row_tokens

        # Add remaining rows
        if current_chunk_rows:
            # Include footer only in the last chunk
            footer_html = None
            if footer_rows:
                tfoot_element = etree.Element("tfoot")
                for row in footer_rows:
                    tfoot_element.append(row)
                footer_html = etree.tostring(tfoot_element, encoding='unicode')

            chunk_html = self._create_chunk_html(header_html, current_chunk_rows, footer_html)
            chunks.append(chunk_html)

        # Ensure minimum rows per chunk
        if len(chunks) > 1:
            chunks = self._rebalance_chunks(chunks, self.min_rows_per_chunk)

        if self.verbose:
            self._log("info", f"Created {len(chunks)} chunks for parallel processing")

        return chunks, has_headers