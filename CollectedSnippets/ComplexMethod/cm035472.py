def copy_to(
        self, host_src: str, sandbox_dest: str, recursive: bool = False
    ) -> None:
        if not os.path.exists(host_src):
            raise FileNotFoundError(f'Source file {host_src} does not exist')

        temp_zip_path: str | None = None  # Define temp_zip_path outside the try block

        try:
            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}
            file_to_upload = None
            upload_data = {}

            if recursive:
                # Create and write the zip file inside the try block
                with tempfile.NamedTemporaryFile(
                    suffix='.zip', delete=False
                ) as temp_zip:
                    temp_zip_path = temp_zip.name

                try:
                    with ZipFile(temp_zip_path, 'w') as zipf:
                        for root, _, files in os.walk(host_src):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(
                                    file_path, os.path.dirname(host_src)
                                )
                                zipf.write(file_path, arcname)

                    self.log(
                        'debug',
                        f'Opening temporary zip file for upload: {temp_zip_path}',
                    )
                    file_to_upload = open(temp_zip_path, 'rb')
                    upload_data = {'file': file_to_upload}
                except Exception as e:
                    # Ensure temp file is cleaned up if zipping fails
                    if temp_zip_path and os.path.exists(temp_zip_path):
                        os.unlink(temp_zip_path)
                    raise e  # Re-raise the exception after cleanup attempt
            else:
                file_to_upload = open(host_src, 'rb')
                upload_data = {'file': file_to_upload}

            params = {'destination': sandbox_dest, 'recursive': str(recursive).lower()}

            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/upload_file',
                files=upload_data,
                params=params,
                timeout=300,
            )
            self.log(
                'debug',
                f'Copy completed: host:{host_src} -> runtime:{sandbox_dest}. Response: {response.text}',
            )
        finally:
            if file_to_upload:
                file_to_upload.close()

            # Cleanup the temporary zip file if it was created
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    os.unlink(temp_zip_path)
                except Exception as e:
                    self.log(
                        'error',
                        f'Failed to delete temporary zip file {temp_zip_path}: {e}',
                    )