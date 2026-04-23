def chunk_documents(self) -> DataFrame:
        documents, warning = extract_docling_documents(self.data_inputs, self.doc_key)
        if warning:
            self.status = warning

        chunker: BaseChunker
        if self.chunker == "HybridChunker":
            try:
                from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
            except ImportError as e:
                msg = (
                    "HybridChunker is not installed. Please install it with `uv pip install docling-core[chunking] "
                    "or `uv pip install transformers`"
                )
                raise ImportError(msg) from e
            max_tokens: int | None = self.max_tokens if self.max_tokens else None
            if self.provider == "Hugging Face":
                try:
                    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
                except ImportError as e:
                    msg = (
                        "HuggingFaceTokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                    )
                    raise ImportError(msg) from e
                tokenizer = HuggingFaceTokenizer.from_pretrained(
                    model_name=self.hf_model_name,
                    max_tokens=max_tokens,
                )
            elif self.provider == "OpenAI":
                try:
                    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
                except ImportError as e:
                    msg = (
                        "OpenAITokenizer is not installed."
                        " Please install it with `uv pip install docling-core[chunking]`"
                        " or `uv pip install transformers`"
                    )
                    raise ImportError(msg) from e
                if max_tokens is None:
                    max_tokens = 128 * 1024  # context window length required for OpenAI tokenizers
                tokenizer = OpenAITokenizer(
                    tokenizer=tiktoken.encoding_for_model(self.openai_model_name), max_tokens=max_tokens
                )
            chunker = HybridChunker(
                tokenizer=tokenizer,
                merge_peers=bool(self.merge_peers),
                always_emit_headings=bool(self.always_emit_headings),
            )

        elif self.chunker == "HierarchicalChunker":
            chunker = HierarchicalChunker()
        else:
            msg = f"Unknown chunker: {self.chunker}"
            raise ValueError(msg)

        results: list[Data] = []
        try:
            for doc in documents:
                for chunk in chunker.chunk(dl_doc=doc):
                    enriched_text = chunker.contextualize(chunk=chunk)
                    meta = DocMeta.model_validate(chunk.meta)

                    results.append(
                        Data(
                            data={
                                "text": enriched_text,
                                "document_id": f"{doc.origin.binary_hash}",
                                "doc_items": json.dumps([item.self_ref for item in meta.doc_items]),
                            }
                        )
                    )

        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e

        return DataFrame(results)