def _get_pdf_path(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            import tempfile
            import requests

            # Create temp file with .pdf extension
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()  # Close handle immediately; file persists due to delete=False
            self._temp_files.append(temp_file.name)

            try:
                if self.logger:
                    self.logger.info(f"Downloading PDF from {url}...")

                # Download PDF with streaming and timeout
                # Connection timeout: 10s, Read timeout: 300s (5 minutes for large PDFs)
                response = requests.get(url, stream=True, timeout=(20, 60 * 10))
                response.raise_for_status()

                # Get file size if available
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                # Write to temp file
                with open(temp_file.name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if self.logger and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if progress % 10 < 0.1:  # Log every 10%
                                self.logger.debug(f"PDF download progress: {progress:.0f}%")

                if self.logger:
                    self.logger.info(f"PDF downloaded successfully: {temp_file.name}")

                return temp_file.name

            except requests.exceptions.Timeout as e:
                # Clean up temp file if download fails
                Path(temp_file.name).unlink(missing_ok=True)
                self._temp_files.remove(temp_file.name)
                raise RuntimeError(f"Timeout downloading PDF from {url}: {str(e)}")
            except Exception as e:
                # Clean up temp file if download fails
                Path(temp_file.name).unlink(missing_ok=True)
                self._temp_files.remove(temp_file.name)
                raise RuntimeError(f"Failed to download PDF from {url}: {str(e)}")

        elif url.startswith("file://"):
            return url[7:]  # Strip file:// prefix

        return url