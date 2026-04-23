def process_batch(self, pdf_path: Path) -> PDFProcessResult:
        """Like process() but processes PDF pages in parallel batches"""
        # Import inside method to allow dependency to be optional
        try:
            from pypdf import PdfReader
            import pypdf  # For type checking
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with 'pip install crawl4ai[pdf]'")

        import concurrent.futures
        import threading

        # Initialize pypdf thread support
        if not hasattr(threading.current_thread(), "_children"): 
            threading.current_thread()._children = set()

        start_time = time()
        result = PDFProcessResult(
            metadata=PDFMetadata(),
            pages=[],
            version="1.1" 
        )

        try:
            # Get metadata and page count from main thread
            with pdf_path.open('rb') as file:
                reader = PdfReader(file)
                result.metadata = self._extract_metadata(pdf_path, reader)
                total_pages = len(reader.pages)

            # Handle image directory setup
            image_dir = None
            if self.extract_images and self.save_images_locally:
                if self.image_save_dir:
                    image_dir = Path(self.image_save_dir)
                    image_dir.mkdir(exist_ok=True, parents=True)
                else:
                    self._temp_dir = tempfile.mkdtemp(prefix='pdf_images_')
                    image_dir = Path(self._temp_dir)

            def process_page_safely(page_num: int):
                # Each thread opens its own file handle
                with pdf_path.open('rb') as file:
                    thread_reader = PdfReader(file)
                    page = thread_reader.pages[page_num]
                    self.current_page_number = page_num + 1
                    return self._process_page(page, image_dir)

            # Process pages in parallel batches
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                futures = []
                for page_num in range(total_pages):
                    future = executor.submit(process_page_safely, page_num)
                    futures.append((page_num + 1, future))

                # Collect results in order
                result.pages = [None] * total_pages
                for page_num, future in futures:
                    try:
                        pdf_page = future.result()
                        result.pages[page_num - 1] = pdf_page
                    except Exception as e:
                        logger.error(f"Failed to process page {page_num}: {str(e)}")
                        raise

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