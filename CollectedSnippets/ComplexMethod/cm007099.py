def process_files(
        self,
        file_list: list[BaseFileComponent.BaseFile],
    ) -> list[BaseFileComponent.BaseFile]:
        """Process input files.

        - advanced_mode => Docling in a separate process.
        - Otherwise => standard parsing in current process (optionally threaded).
        """
        if not file_list:
            msg = "No files to process."
            raise ValueError(msg)

        # Validate image files to detect content/extension mismatches
        # This prevents API errors like "Image does not match the provided media type"
        image_extensions = {"jpeg", "jpg", "png", "gif", "webp", "bmp", "tiff"}
        settings = get_settings_service().settings
        for file in file_list:
            extension = file.path.suffix[1:].lower()
            if extension in image_extensions:
                # Read bytes based on storage type
                try:
                    if settings.storage_type == "s3":
                        # For S3 storage, use storage service to read file bytes
                        file_path_str = str(file.path)
                        content = run_until_complete(read_file_bytes(file_path_str))
                    else:
                        # For local storage, read bytes directly from filesystem
                        content = file.path.read_bytes()

                    is_valid, error_msg = validate_image_content_type(
                        str(file.path),
                        content=content,
                    )
                    if not is_valid:
                        self.log(error_msg)
                        if not self.silent_errors:
                            raise ValueError(error_msg)
                except (OSError, FileNotFoundError) as e:
                    self.log(f"Could not read file for validation: {e}")
                    # Continue - let it fail later with better error

        # Validate that files requiring Docling are only processed when advanced mode is enabled
        if not self.advanced_mode:
            for file in file_list:
                extension = file.path.suffix[1:].lower()
                if extension in self.DOCLING_ONLY_EXTENSIONS:
                    if is_astra_cloud_environment():
                        msg = (
                            f"File '{file.path.name}' has extension '.{extension}' which requires "
                            f"Advanced Parser mode. Advanced Parser is not available in cloud environments."
                        )
                    else:
                        msg = (
                            f"File '{file.path.name}' has extension '.{extension}' which requires "
                            f"Advanced Parser mode. Please enable 'Advanced Parser' to process this file."
                        )
                    self.log(msg)
                    raise ValueError(msg)

        def process_file_standard(file_path: str, *, silent_errors: bool = False) -> Data | None:
            try:
                return parse_text_file_to_data(file_path, silent_errors=silent_errors)
            except FileNotFoundError as e:
                self.log(f"File not found: {file_path}. Error: {e}")
                if not silent_errors:
                    raise
                return None
            except Exception as e:
                self.log(f"Unexpected error processing {file_path}: {e}")
                if not silent_errors:
                    raise
                return None

        docling_compatible = all(self._is_docling_compatible(str(f.path)) for f in file_list)

        # Advanced path: Check if ALL files are compatible with Docling
        if self.advanced_mode and docling_compatible:
            final_return: list[BaseFileComponent.BaseFile] = []
            for file in file_list:
                file_path = str(file.path)
                advanced_data: Data | None = self._process_docling_in_subprocess(file_path)

                # Handle None case - Docling processing failed or returned None
                if advanced_data is None:
                    error_data = Data(
                        data={
                            "file_path": file_path,
                            "error": "Docling processing returned no result. Check logs for details.",
                        },
                    )
                    final_return.extend(self.rollup_data([file], [error_data]))
                    continue

                # --- UNNEST: expand each element in `doc` to its own Data row
                payload = getattr(advanced_data, "data", {}) or {}

                # Check for errors first
                if "error" in payload:
                    error_msg = payload.get("error", "Unknown error")
                    error_data = Data(
                        data={
                            "file_path": file_path,
                            "error": error_msg,
                            **{k: v for k, v in payload.items() if k not in ("error", "file_path")},
                        },
                    )
                    final_return.extend(self.rollup_data([file], [error_data]))
                    continue

                doc_rows = payload.get("doc")
                if isinstance(doc_rows, list) and doc_rows:
                    # Non-empty list of structured rows
                    rows: list[Data | None] = [
                        Data(
                            data={
                                "file_path": file_path,
                                **(item if isinstance(item, dict) else {"value": item}),
                            },
                        )
                        for item in doc_rows
                    ]
                    final_return.extend(self.rollup_data([file], rows))
                elif isinstance(doc_rows, list) and not doc_rows:
                    # Empty list - file was processed but no text content found
                    # Create a Data object indicating no content was extracted
                    self.log(f"No text extracted from '{file_path}', creating placeholder data")
                    empty_data = Data(
                        data={
                            "file_path": file_path,
                            "text": "(No text content extracted from image)",
                            "info": "Image processed successfully but contained no extractable text",
                            **{k: v for k, v in payload.items() if k != "doc"},
                        },
                    )
                    final_return.extend(self.rollup_data([file], [empty_data]))
                else:
                    # If not structured, keep as-is (e.g., markdown export or error dict)
                    # Ensure file_path is set for proper rollup matching
                    if not payload.get("file_path"):
                        payload["file_path"] = file_path
                        # Create new Data with file_path
                        advanced_data = Data(
                            data=payload,
                            text=getattr(advanced_data, "text", None),
                        )
                    final_return.extend(self.rollup_data([file], [advanced_data]))
            return final_return

        # Standard multi-file (or single non-advanced) path
        concurrency = max(1, self.concurrency_multithreading)

        file_paths = [str(f.path) for f in file_list]
        self.log(f"Starting parallel processing of {len(file_paths)} files with concurrency: {concurrency}.")
        my_data = parallel_load_data(
            file_paths,
            silent_errors=self.silent_errors,
            load_function=process_file_standard,
            max_concurrency=concurrency,
        )
        return self.rollup_data(file_list, my_data)