async def _invoke(self, **kwargs):
        try:
            chunks = kwargs.get("chunks")
            if chunks is not None:
                kwargs["chunks"] = [c for c in chunks if c is not None]

            from_upstream = TokenizerFromUpstream.model_validate(kwargs)
        except Exception as e:
            self.set_output("_ERROR", f"Input error: {str(e)}")
            return

        self.set_output("output_format", "chunks")
        parts = sum(["full_text" in self._param.search_method, "embedding" in self._param.search_method])
        if "full_text" in self._param.search_method:
            self.callback(random.randint(1, 5) / 100.0, "Start to tokenize.")
            # Branch on the declared upstream format so an empty chunk list stays on the chunk path.
            if from_upstream.output_format == "chunks":
                chunks = from_upstream.chunks or []
                for i, ck in enumerate(chunks):
                    ck["chunk_order_int"] = i
                    ck["title_tks"] = rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", from_upstream.name))
                    ck["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(ck["title_tks"])
                    if ck.get("questions"):
                        ck["question_kwd"] = ck["questions"].split("\n")
                        ck["question_tks"] = rag_tokenizer.tokenize(str(ck["questions"]))
                    if ck.get("keywords"):
                        ck["important_kwd"] = ck["keywords"].split(",")
                        ck["important_tks"] = rag_tokenizer.tokenize(str(ck["keywords"]))
                    if ck.get("summary"):
                        ck["content_ltks"] = rag_tokenizer.tokenize(str(ck["summary"]))
                        ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(ck["content_ltks"])
                    elif ck.get("text"):
                        ck["content_ltks"] = rag_tokenizer.tokenize(ck["text"])
                        ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(ck["content_ltks"])
                    if i % 100 == 99:
                        self.callback(i * 1.0 / len(chunks) / parts)

            elif from_upstream.output_format in ["markdown", "text", "html"]:
                if from_upstream.output_format == "markdown":
                    payload = from_upstream.markdown_result
                elif from_upstream.output_format == "text":
                    payload = from_upstream.text_result
                else:
                    payload = from_upstream.html_result

                if not payload:
                    return ""

                ck = {"text": payload}
                if "full_text" in self._param.search_method:
                    ck["title_tks"] = rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", from_upstream.name))
                    ck["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(ck["title_tks"])
                    ck["content_ltks"] = rag_tokenizer.tokenize(payload)
                    ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(ck["content_ltks"])
                chunks = [ck]
            else:
                # Empty JSON payloads are valid and should remain empty downstream.
                chunks = from_upstream.json_result or []
                for i, ck in enumerate(chunks):
                    ck["title_tks"] = rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", from_upstream.name))
                    ck["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(ck["title_tks"])
                    if not ck.get("text"):
                        continue
                    ck["content_ltks"] = rag_tokenizer.tokenize(ck["text"])
                    ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(ck["content_ltks"])
                    if i % 100 == 99:
                        self.callback(i * 1.0 / len(chunks) / parts)

            self.callback(1.0 / parts, "Finish tokenizing.")

        if "embedding" in self._param.search_method:
            self.callback(random.randint(1, 5) / 100.0 + 0.5 * (parts - 1), "Start embedding inference.")

            if from_upstream.name.strip() == "":
                logging.warning("Tokenizer: empty name provided from upstream, embedding may be not accurate.")

            chunks, token_count = await self._embedding(from_upstream.name, chunks)
            self.set_output("embedding_token_consumption", token_count)

            self.callback(1.0, "Finish embedding.")

        chunks = [finalize_pdf_chunk(ck) for ck in chunks]

        self.set_output("chunks", chunks)