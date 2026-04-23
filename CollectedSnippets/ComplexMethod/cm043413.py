def process(self, pdf_path: Path) -> PDFProcessResult:
        # Import inside method to allow dependency to be optional
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")

        start_time = time()
        result = PDFProcessResult(
            metadata=PDFMetadata(),
            pages=[],
            version="1.1"
        )

        try:
            with pdf_path.open('rb') as file:
                reader = PdfReader(file)
                result.metadata = self._extract_metadata(pdf_path, reader)

                # Handle image directory
                image_dir = None
                if self.extract_images and self.save_images_locally:
                    if self.image_save_dir:
                        image_dir = Path(self.image_save_dir)
                        image_dir.mkdir(exist_ok=True, parents=True)
                    else:
                        self._temp_dir = tempfile.mkdtemp(prefix='pdf_images_')
                        image_dir = Path(self._temp_dir)

                for page_num, page in enumerate(reader.pages):
                    self.current_page_number = page_num + 1
                    pdf_page = self._process_page(page, image_dir)
                    result.pages.append(pdf_page)

        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise
        finally:
            # Cleanup temp directory if it was created
            if self._temp_dir and not self.image_save_dir:
                import shutil
                try:
                    shutil.rmtree(self._temp_dir)
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {str(e)}")

        result.processing_time = time() - start_time
        return result