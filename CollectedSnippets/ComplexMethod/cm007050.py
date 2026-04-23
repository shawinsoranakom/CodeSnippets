def split_text(self) -> list[Data]:
        """Split the input data into semantically meaningful chunks."""
        try:
            embeddings = getattr(self, "embeddings", None)
            if embeddings is None:
                error_msg = "An embeddings model is required for SemanticTextSplitter."
                raise ValueError(error_msg)

            if not self.data_inputs:
                error_msg = "Data inputs cannot be empty."
                raise ValueError(error_msg)

            documents = []
            for _input in self.data_inputs:
                if isinstance(_input, Data):
                    documents.append(_input.to_lc_document())
                else:
                    error_msg = f"Invalid data input type: {_input}"
                    raise TypeError(error_msg)

            if not documents:
                error_msg = "No valid Data objects found in data_inputs."
                raise ValueError(error_msg)

            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            splitter_params = {
                "embeddings": embeddings,
                "breakpoint_threshold_type": self.breakpoint_threshold_type or "percentile",
                "breakpoint_threshold_amount": self.breakpoint_threshold_amount,
                "number_of_chunks": self.number_of_chunks,
                "buffer_size": self.buffer_size,
            }

            if self.sentence_split_regex:
                splitter_params["sentence_split_regex"] = self.sentence_split_regex

            splitter = SemanticChunker(**splitter_params)
            docs = splitter.create_documents(texts, metadatas=metadatas)

            data = self._docs_to_data(docs)
            self.status = data

        except Exception as e:
            error_msg = f"An error occurred during semantic splitting: {e}"
            raise RuntimeError(error_msg) from e

        else:
            return data