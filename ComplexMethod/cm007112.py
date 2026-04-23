def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        try:
            from nv_ingest_client.client import Ingestor
        except ImportError as e:
            msg = (
                "NVIDIA Retriever Extraction (nv-ingest) dependencies missing. "
                "Please install them using your package manager. (e.g. uv pip install langflow[nv-ingest])"
            )
            raise ImportError(msg) from e

        if not file_list:
            err_msg = "No files to process."
            self.log(err_msg)
            raise ValueError(err_msg)

        # Check if all files are PDFs when high resolution mode is enabled
        if self.high_resolution:
            for file in file_list:
                try:
                    with file.path.open("rb") as f:
                        PdfReader(f)
                except Exception as exc:
                    error_msg = "High-resolution mode only supports valid PDF files."
                    self.log(error_msg)
                    raise ValueError(error_msg) from exc

        file_paths = [str(file.path) for file in file_list]

        self.base_url: str | None = self.base_url.strip() if self.base_url else None
        if self.base_url:
            try:
                urlparse(self.base_url)
            except Exception as e:
                error_msg = f"Invalid Base URL format: {e}"
                self.log(error_msg)
                raise ValueError(error_msg) from e
        else:
            base_url_error = "Base URL is required"
            raise ValueError(base_url_error)

        self.log(
            f"Creating Ingestor for Base URL: {self.base_url!r}",
        )

        try:
            ingestor = (
                Ingestor(
                    message_client_kwargs={
                        "base_url": self.base_url,
                        "headers": {"Authorization": f"Bearer {self.api_key}"},
                        "max_retries": 3,
                        "timeout": 60,
                    }
                )
                .files(file_paths)
                .extract(
                    extract_text=self.extract_text,
                    extract_tables=self.extract_tables,
                    extract_charts=self.extract_charts,
                    extract_images=self.extract_images,
                    extract_infographics=self.extract_infographics,
                    text_depth=self.text_depth,
                    **({"extract_method": "nemoretriever_parse"} if self.high_resolution else {}),
                )
            )

            if self.extract_images:
                if self.dedup_images:
                    ingestor = ingestor.dedup(content_type="image", filter=True)

                if self.filter_images:
                    ingestor = ingestor.filter(
                        content_type="image",
                        min_size=self.min_image_size,
                        min_aspect_ratio=self.min_aspect_ratio,
                        max_aspect_ratio=self.max_aspect_ratio,
                        filter=True,
                    )

                if self.caption_images:
                    ingestor = ingestor.caption()

            if self.extract_text and self.split_text:
                ingestor = ingestor.split(
                    tokenizer="intfloat/e5-large-unsupervised",
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    params={"split_source_types": ["PDF"]},
                )

            result = ingestor.ingest()
        except Exception as e:
            ingest_error = f"Error during ingestion: {e}"
            self.log(ingest_error)
            raise

        self.log(f"Results: {result}")

        data: list[Data | None] = []
        document_type_text = "text"
        document_type_structured = "structured"

        # Result is a list of segments as determined by the text_depth option (if "document" then only one segment)
        # each segment is a list of elements (text, structured, image)
        for segment in result:
            if segment:
                for element in segment:
                    document_type = element.get("document_type")
                    metadata = element.get("metadata", {})
                    source_metadata = metadata.get("source_metadata", {})

                    if document_type == document_type_text:
                        data.append(
                            Data(
                                text=metadata.get("content", ""),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    # Both charts and tables are returned as "structured" document type,
                    # with extracted text in "table_content"
                    elif document_type == document_type_structured:
                        table_metadata = metadata.get("table_metadata", {})

                        # reformat chart/table images as binary data
                        if "content" in metadata:
                            metadata["content"] = {"$binary": metadata["content"]}

                        data.append(
                            Data(
                                text=table_metadata.get("table_content", ""),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    elif document_type == "image":
                        image_metadata = metadata.get("image_metadata", {})

                        # reformat images as binary data
                        if "content" in metadata:
                            metadata["content"] = {"$binary": metadata["content"]}

                        data.append(
                            Data(
                                text=image_metadata.get("caption", "No caption available"),
                                file_path=source_metadata.get("source_name", ""),
                                document_type=document_type,
                                metadata=metadata,
                            )
                        )
                    else:
                        self.log(f"Unsupported document type {document_type}")
        self.status = data or "No data"

        # merge processed data with BaseFile objects
        return self.rollup_data(file_list, data)