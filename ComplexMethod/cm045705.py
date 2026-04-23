def _chunk(
        self,
        elements: Iterable[Element],
        chunking_mode: ChunkingMode | None,
        chunking_kwargs: dict,
    ) -> list[tuple[str, dict]]:

        with optional_imports("xpack-llm-docs"):
            from unstructured.chunking.basic import chunk_elements
            from unstructured.chunking.title import chunk_by_title

        docs: list[tuple[str, dict]]

        chunking_mode = chunking_mode or self.chunking_mode

        if chunking_mode == "basic":
            chunked_elements = chunk_elements(elements, **chunking_kwargs)
            docs = [self._extract_element_meta(el) for el in chunked_elements]

        elif chunking_mode == "by_title":
            chunked_elements = chunk_by_title(elements, **chunking_kwargs)
            docs = [self._extract_element_meta(el) for el in chunked_elements]

        elif chunking_mode == "elements":
            docs = [self._extract_element_meta(el) for el in elements]

        elif chunking_mode == "paged":
            text_dict: dict[int, str] = defaultdict(str)
            meta_dict: dict[int, dict] = defaultdict(dict)

            for element in elements:
                el, metadata = self._extract_element_meta(element)
                page_number = metadata.get("page_number", 1)

                # Append text and update metadata for the given page_number
                text_dict[page_number] += el + "\n\n"
                meta_dict[page_number] = self._combine_metadata(
                    meta_dict[page_number], metadata
                )

            # Convert the dict to a list of dicts representing documents
            docs = [
                (text_dict[key], meta_dict[key])
                for key in sorted(list(text_dict.keys()))
            ]

        elif chunking_mode == "single":
            metadata = {}
            for element in elements:
                if hasattr(element, "metadata"):
                    metadata = self._combine_metadata(
                        metadata, element.metadata.to_dict()
                    )
            text = "\n\n".join([str(el) for el in elements])
            docs = [(text, metadata)]

        return docs