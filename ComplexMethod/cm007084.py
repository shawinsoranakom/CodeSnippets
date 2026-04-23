def process_files(self, file_list: list[BaseFileComponent.BaseFile]) -> list[BaseFileComponent.BaseFile]:
        # Check that docling is installed without actually importing it.
        # The real import (PyTorch, transformers, etc.) happens in the child
        # subprocess.  Importing it here would spike memory and get the
        # Gunicorn worker SIGKILL'd by the OOM killer.
        import importlib.util

        if importlib.util.find_spec("docling") is None:
            msg = (
                "Docling is an optional dependency. Install with `uv pip install 'langflow[docling]'` or refer to the "
                "documentation on how to install optional dependencies."
            )
            raise ImportError(msg)

        file_paths = [str(file.path) for file in file_list if file.path]

        if not file_paths:
            self.log("No files to process.")
            return file_list

        pic_desc_config: dict | None = None
        if self.pic_desc_llm is not None:
            pic_desc_config = _serialize_pydantic_model(self.pic_desc_llm)

        args = {
            "file_paths": file_paths,
            "pipeline": self.pipeline,
            "ocr_engine": self.ocr_engine,
            "do_picture_classification": self.do_picture_classification,
            "pic_desc_config": pic_desc_config,
            "pic_desc_prompt": self.pic_desc_prompt,
        }

        # Use Popen with a polling loop (same pattern as Read File advanced mode).
        # This avoids multiprocessing/threading issues under Gunicorn and keeps the
        # SSE event stream alive via periodic heartbeat logs.
        docling_timeout = 600  # 10 minutes
        poll_interval = 5

        # Use a temporary file for stdout to avoid pipe buffer deadlocks.
        # Docling (and its transitive imports: PyTorch, transformers, etc.) can
        # write large amounts of output.  With subprocess.PIPE the OS pipe
        # buffer (~16 KB on macOS) fills up, the child blocks on write, and the
        # parent - which only reads *after* the child exits - waits forever.
        import tempfile

        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            proc = subprocess.Popen(  # noqa: S603
                [sys.executable, "-u", "-c", self._CHILD_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=stdout_file,
                stderr=stderr_file,
            )
            proc.stdin.write(json.dumps(args).encode("utf-8"))
            proc.stdin.close()

            start = time.monotonic()
            while proc.poll() is None:
                elapsed = time.monotonic() - start
                if elapsed >= docling_timeout:
                    proc.kill()
                    proc.wait()
                    msg = (
                        f"Docling processing timed out after {docling_timeout}s. Try processing fewer or smaller files."
                    )
                    raise TimeoutError(msg)
                self.log(f"Docling processing in progress ({int(elapsed)}s elapsed)...")
                time.sleep(poll_interval)

            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout_bytes = stdout_file.read()
            stderr_bytes = stderr_file.read()

        if not stdout_bytes:
            err_msg = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else "no output"
            msg = f"Docling subprocess error: {err_msg}"
            raise RuntimeError(msg)

        try:
            payload = json.loads(stdout_bytes.decode("utf-8"))
        except Exception as e:
            err_msg = stderr_bytes.decode("utf-8", errors="replace")
            msg = f"Invalid JSON from Docling subprocess: {e}. stderr={err_msg}"
            raise RuntimeError(msg) from e

        if not payload.get("ok"):
            error_msg = payload.get("error", "Unknown Docling error")
            if "not installed" in error_msg.lower():
                raise ImportError(error_msg)
            raise RuntimeError(error_msg)

        # Reconstruct DoclingDocument objects from JSON dicts returned by the child
        from docling_core.types.doc import DoclingDocument

        raw_results = payload.get("results", [])
        processed_data: list[Data | None] = []
        for r in raw_results:
            if r is None:
                processed_data.append(None)
                continue
            try:
                doc = DoclingDocument.model_validate(r["document"])
            except Exception:  # noqa: BLE001
                # Fall back to keeping the raw dict if validation fails
                doc = r["document"]
            processed_data.append(Data(data={"doc": doc, "file_path": r["file_path"]}))

        return self.rollup_data(file_list, processed_data)