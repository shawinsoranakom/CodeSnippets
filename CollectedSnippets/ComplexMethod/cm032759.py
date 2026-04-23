async def _invoke(self, **kwargs):
        try:
            from_upstream = TokenChunkerFromUpstream.model_validate(kwargs)
        except Exception as e:
            self.set_output("_ERROR", f"Input error: {str(e)}")
            return

        # Build the primary delimiter regex. If no active custom delimiter exists,
        # the token chunker falls back to token-size based merging.
        delimiter_pattern = _compile_delimiter_pattern(self._param.delimiters)
        custom_pattern = "|".join(re.escape(t) for t in sorted(set(self._param.children_delimiters), key=len, reverse=True))

        self.set_output("output_format", "chunks")
        self.callback(random.randint(1, 5) / 100.0, "Start to split into chunks.")
        overlapped_percent = normalize_overlapped_percent(self._param.overlapped_percent)
        if from_upstream.output_format in ["markdown", "text", "html"]:
            payload = getattr(from_upstream, f"{from_upstream.output_format}_result") or ""
            if self._param.delimiter_mode == "one":
                self.set_output("chunks", [{"text": payload}] if payload.strip() else [])
                self.callback(1, "Done.")
                return
            cks = _split_text_by_pattern(payload, delimiter_pattern) if delimiter_pattern else naive_merge(
                payload,
                self._param.chunk_token_size,
                "",
                overlapped_percent,
            )
            if custom_pattern:
                docs = []
                for c in cks:
                    if not c.strip():
                        continue
                    for text in _split_text_by_pattern(c, custom_pattern):
                        if not text.strip():
                            continue
                        docs.append({"text": text, "mom": c})
                self.set_output("chunks", docs)
            else:
                self.set_output("chunks", [{"text": c.strip()} for c in cks if c.strip()])

            self.callback(1, "Done.")
            return

        # json
        json_result = from_upstream.json_result or []
        if self._param.delimiter_mode == "one":
            sections = []
            for item in json_result:
                text = item.get("text")
                if not isinstance(text, str):
                    text = item.get("content_with_weight")
                if isinstance(text, str) and text.strip():
                    sections.append(text)
            merged_text = "\n".join(sections)
            self.set_output("chunks", [{"text": merged_text}] if merged_text.strip() else [])
            self.callback(1, "Done.")
            return
        # Structured JSON input is normalized first, then optionally enriched with
        # media context, and finally merged only when delimiter splitting is inactive.
        chunks = _build_json_chunks(json_result, delimiter_pattern)
        _attach_context_to_media_chunks(chunks, self._param.table_context_size, self._param.image_context_size)
        if not delimiter_pattern:
            chunks = _merge_text_chunks_by_token_size(chunks, self._param.chunk_token_size, overlapped_percent)

        if custom_pattern:
            chunks = _split_chunk_docs_by_children(chunks, custom_pattern)

        await restore_pdf_text_previews(chunks, from_upstream, self._canvas)
        cks = _finalize_json_chunks(chunks)
        self.set_output("chunks", cks)
        self.callback(1, "Done.")