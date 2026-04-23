def parse_pdf(
        self,
        filepath: str | PathLike[str],
        binary: BytesIO | bytes,
        callback: Optional[Callable] = None,
        *,
        output_dir: Optional[str] = None,
        file_type: str = "PDF",
        file_start_page: Optional[int] = 1,
        file_end_page: Optional[int] = 1000,
        delete_output: Optional[bool] = True,
        max_retries: Optional[int] = 1,
    ) -> tuple:
        """Parse PDF document"""

        self.outlines = extract_pdf_outlines(binary if binary else filepath)
        temp_file = None
        created_tmp_dir = False

        try:
            # Handle input file
            if binary:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.write(binary)
                temp_file.close()
                file_path = temp_file.name
                self.logger.info(f"[TCADP] Received binary PDF -> {os.path.basename(file_path)}")
                if callback:
                    callback(0.1, f"[TCADP] Received binary PDF -> {os.path.basename(file_path)}")
            else:
                file_path = str(filepath)
                if not os.path.exists(file_path):
                    if callback:
                        callback(-1, f"[TCADP] PDF file does not exist: {file_path}")
                    raise FileNotFoundError(f"[TCADP] PDF file does not exist: {file_path}")

            # Convert file to Base64 format
            if callback:
                callback(0.2, "[TCADP] Converting file to Base64 format")

            file_base64 = self._file_to_base64(file_path, binary)
            if callback:
                callback(0.25, f"[TCADP] File converted to Base64, size: {len(file_base64)} characters")

            # Create Tencent Cloud API client
            client = TencentCloudAPIClient(self.secret_id, self.secret_key, self.region)

            # Call document parsing API (with retry mechanism)
            if callback:
                callback(0.3, "[TCADP] Starting to call Tencent Cloud document parsing API")

            result = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        self.logger.info(f"[TCADP] Retry attempt {attempt + 1}")
                        if callback:
                            callback(0.3 + attempt * 0.1, f"[TCADP] Retry attempt {attempt + 1}")
                        time.sleep(2 ** attempt)  # Exponential backoff

                    config = {
                        "TableResultType": self.table_result_type,
                        "MarkdownImageResponseType": self.markdown_image_response_type
                    }

                    self.logger.info(f"[TCADP] API request config - TableResultType: {self.table_result_type}, MarkdownImageResponseType: {self.markdown_image_response_type}")

                    result = client.reconstruct_document_sse(
                        file_type=file_type,
                        file_base64=file_base64,
                        file_start_page=file_start_page,
                        file_end_page=file_end_page,
                        config=config
                    )

                    if result:
                        self.logger.info(f"[TCADP] Attempt {attempt + 1} successful")
                        break
                    else:
                        self.logger.warning(f"[TCADP] Attempt {attempt + 1} failed, result is None")

                except Exception as e:
                    self.logger.error(f"[TCADP] Attempt {attempt + 1} exception: {e}")
                    if attempt == max_retries - 1:
                        raise

            if not result:
                error_msg = f"[TCADP] Document parsing failed, retried {max_retries} times"
                self.logger.error(error_msg)
                if callback:
                    callback(-1, error_msg)
                raise RuntimeError(error_msg)

            # Get download link
            download_url = result.get("DocumentRecognizeResultUrl")
            if not download_url:
                if callback:
                    callback(-1, "[TCADP] No parsing result download link obtained")
                raise RuntimeError("[TCADP] No parsing result download link obtained")

            if callback:
                callback(0.6, f"[TCADP] Parsing result download link: {download_url}")

            # Set output directory
            if output_dir:
                out_dir = Path(output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
            else:
                out_dir = Path(tempfile.mkdtemp(prefix="adp_pdf_"))
                created_tmp_dir = True

            # Download result file
            zip_path = client.download_result_file(download_url, str(out_dir))
            if not zip_path:
                if callback:
                    callback(-1, "[TCADP] Failed to download parsing result")
                raise RuntimeError("[TCADP] Failed to download parsing result")

            if callback:
                # Shorten file path display, only show filename
                zip_filename = os.path.basename(zip_path)
                callback(0.8, f"[TCADP] Parsing result downloaded: {zip_filename}")

            # Extract ZIP file content
            content_data = self._extract_content_from_zip(zip_path)
            self.logger.info(f"[TCADP] Extracted {len(content_data)} content blocks")

            if callback:
                callback(0.9, f"[TCADP] Extracted {len(content_data)} content blocks")

            # Convert to sections and tables format
            sections = self._parse_content_to_sections(content_data)
            tables = self._parse_content_to_tables(content_data)

            self.logger.info(f"[TCADP] Parsing completed: {len(sections)} sections, {len(tables)} tables")

            if callback:
                callback(1.0, f"[TCADP] Parsing completed: {len(sections)} sections, {len(tables)} tables")

            return sections, tables

        finally:
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

            if delete_output and created_tmp_dir and out_dir.exists():
                try:
                    shutil.rmtree(out_dir)
                except Exception:
                    pass