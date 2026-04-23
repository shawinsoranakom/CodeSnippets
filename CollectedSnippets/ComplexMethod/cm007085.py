def _convert_document(client: httpx.Client, file_path: Path, options: dict[str, Any]) -> Data | None:
            encoded_doc = base64.b64encode(file_path.read_bytes()).decode()
            payload = {
                "options": options,
                "sources": [{"kind": "file", "base64_string": encoded_doc, "filename": file_path.name}],
            }

            response = client.post(f"{base_url}/convert/source/async", json=payload)
            response.raise_for_status()
            task = response.json()

            http_failures = 0
            retry_status_start = 500
            retry_status_end = 600
            start_wait_time = time.monotonic()
            while task["task_status"] not in ("success", "failure"):
                # Check if processing exceeds the maximum poll timeout
                processing_time = time.monotonic() - start_wait_time
                if processing_time >= self.max_poll_timeout:
                    msg = (
                        f"Processing time {processing_time=} exceeds the maximum poll timeout {self.max_poll_timeout=}."
                        "Please increase the max_poll_timeout parameter or review why the processing "
                        "takes long on the server."
                    )
                    self.log(msg)
                    raise RuntimeError(msg)

                # Call for a new status update
                time.sleep(2)
                response = client.get(f"{base_url}/status/poll/{task['task_id']}")

                # Check if the status call gets into 5xx errors and retry
                if retry_status_start <= response.status_code < retry_status_end:
                    http_failures += 1
                    if http_failures > self.MAX_500_RETRIES:
                        self.log(f"The status requests got a http response {response.status_code} too many times.")
                        return None
                    continue

                # Update task status
                task = response.json()

            result_resp = client.get(f"{base_url}/result/{task['task_id']}")
            result_resp.raise_for_status()
            result = result_resp.json()

            if "json_content" not in result["document"] or result["document"]["json_content"] is None:
                self.log("No JSON DoclingDocument found in the result.")
                return None

            try:
                doc = DoclingDocument.model_validate(result["document"]["json_content"])
                return Data(data={"doc": doc, "file_path": str(file_path)})
            except ValidationError as e:
                self.log(f"Error validating the document. {e}")
                return None