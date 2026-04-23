def _invoke(self, **kwargs):
        file_path = None
        try:
            content = self._resolve_content(kwargs)
            output_format = self._param.output_format or "pdf"

            try:
                if output_format == "pdf":
                    file_path, file_bytes = self._generate_pdf(content)
                    mime_type = "application/pdf"
                elif output_format == "docx":
                    file_path, file_bytes = self._generate_docx(content)
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif output_format == "txt":
                    file_path, file_bytes = self._generate_txt(content)
                    mime_type = "text/plain"
                elif output_format == "markdown":
                    file_path, file_bytes = self._generate_markdown(content)
                    mime_type = "text/markdown"
                elif output_format == "html":
                    file_path, file_bytes = self._generate_html(content)
                    mime_type = "text/html"
                else:
                    raise Exception(f"Unsupported output format: {output_format}")

                filename = os.path.basename(file_path)
                if not file_bytes:
                    raise Exception("Document file is empty")

                file_size = len(file_bytes)
                doc_id = get_uuid()
                settings.STORAGE_IMPL.put(self._canvas.get_tenant_id(), doc_id, file_bytes)

                logging.info(
                    "Successfully generated %s: %s (Size: %s bytes)",
                    output_format.upper(),
                    filename,
                    file_size,
                )

                download_info = {
                    "doc_id": doc_id,
                    "filename": filename,
                    "mime_type": mime_type,
                    "size": file_size,
                }
                self.set_output("download", json.dumps(download_info))
                return download_info

            except Exception as e:
                logging.exception("Error generating %s document", output_format)
                self.set_output("_ERROR", f"Document generation failed: {str(e)}")
                raise

        except Exception as e:
            logging.exception("Error in DocGenerator._invoke")
            self.set_output("_ERROR", f"Document generation failed: {str(e)}")
            raise
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)