def process_media(self) -> Data:
        """Process audio or video file and extract structured data."""
        # Validate inputs
        error_msg = self._check_inputs()
        if error_msg:
            self.status = error_msg
            return Data(data={"error": error_msg})

        try:
            # Import and initialize client
            vlmrun_class = self._import_vlmrun()
            client = vlmrun_class(api_key=self.api_key)
            all_results = []

            # Handle multiple files
            if self.media_files:
                files_to_process = self.media_files if isinstance(self.media_files, list) else [self.media_files]
                for idx, media_file in enumerate(files_to_process):
                    self.status = f"Processing file {idx + 1} of {len(files_to_process)}..."
                    result = self._process_single_media(client, Path(media_file), Path(media_file).name)
                    all_results.append(result)

            # Handle URL
            elif self.media_url:
                result = self._process_single_media(client, self.media_url, self.media_url)
                all_results.append(result)

            # Return clean, flexible output structure
            output_data = {
                "results": all_results,
                "total_files": len(all_results),
            }
            self.status = f"Successfully processed {len(all_results)} file(s)"
            return Data(data=output_data)

        except ImportError as e:
            self.status = str(e)
            return Data(data={"error": str(e)})
        except (ValueError, ConnectionError, TimeoutError) as e:
            logger.opt(exception=True).debug("Error processing media with VLM Run")
            error_msg = f"Processing failed: {e!s}"
            self.status = error_msg
            return Data(data={"error": error_msg})
        except (AttributeError, KeyError, OSError) as e:
            logger.opt(exception=True).debug("Unexpected error processing media with VLM Run")
            error_msg = f"Unexpected error: {e!s}"
            self.status = error_msg
            return Data(data={"error": error_msg})