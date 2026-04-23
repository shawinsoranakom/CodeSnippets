def _process_docling_subprocess_impl(self, local_file_path: str, original_file_path: str) -> Data | None:
        """Implementation of Docling subprocess processing.

        Args:
            local_file_path: Path to local file to process
            original_file_path: Original file path to include in metadata
        Returns:
            Data object with processed content
        """
        args: dict[str, Any] = {
            "file_path": local_file_path,
            "markdown": bool(self.markdown),
            "image_mode": str(self.IMAGE_MODE),
            "md_image_placeholder": str(self.md_image_placeholder),
            "md_page_break_placeholder": str(self.md_page_break_placeholder),
            "pipeline": str(self.pipeline),
            "ocr_engine": (
                self.ocr_engine if self.ocr_engine and self.ocr_engine != "None" and self.pipeline != "vlm" else None
            ),
        }

        # Child script for isolating the docling processing
        child_script = textwrap.dedent(
            r"""
            import json, sys

            def try_imports():
                try:
                    from docling.datamodel.base_models import ConversionStatus, InputFormat  # type: ignore
                    from docling.document_converter import DocumentConverter  # type: ignore
                    from docling_core.types.doc import ImageRefMode  # type: ignore
                    return ConversionStatus, InputFormat, DocumentConverter, ImageRefMode, "latest"
                except Exception as e:
                    raise e

            def create_converter(strategy, input_format, DocumentConverter, pipeline, ocr_engine):
                # --- Standard PDF/IMAGE pipeline (your existing behavior), with optional OCR ---
                if pipeline == "standard":
                    try:
                        from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore
                        from docling.document_converter import PdfFormatOption  # type: ignore

                        pipe = PdfPipelineOptions()
                        pipe.do_ocr = False

                        if ocr_engine:
                            try:
                                from docling.models.factories import get_ocr_factory  # type: ignore
                                pipe.do_ocr = True
                                fac = get_ocr_factory(allow_external_plugins=False)
                                pipe.ocr_options = fac.create_options(kind=ocr_engine)
                            except Exception:
                                # If OCR setup fails, disable it
                                pipe.do_ocr = False

                        fmt = {}
                        if hasattr(input_format, "PDF"):
                            fmt[getattr(input_format, "PDF")] = PdfFormatOption(pipeline_options=pipe)
                        if hasattr(input_format, "IMAGE"):
                            fmt[getattr(input_format, "IMAGE")] = PdfFormatOption(pipeline_options=pipe)

                        return DocumentConverter(format_options=fmt)
                    except Exception:
                        return DocumentConverter()

                # --- Vision-Language Model (VLM) pipeline ---
                if pipeline == "vlm":
                    try:
                        from docling.datamodel.pipeline_options import VlmPipelineOptions
                        from docling.datamodel.vlm_model_specs import GRANITEDOCLING_MLX, GRANITEDOCLING_TRANSFORMERS
                        from docling.document_converter import PdfFormatOption
                        from docling.pipeline.vlm_pipeline import VlmPipeline

                        vl_pipe = VlmPipelineOptions(
                            vlm_options=GRANITEDOCLING_TRANSFORMERS,
                        )

                        if sys.platform == "darwin":
                            try:
                                import mlx_vlm
                                vl_pipe.vlm_options = GRANITEDOCLING_MLX
                            except ImportError as e:
                                raise e

                        # VLM paths generally don't need OCR; keep OCR off by default here.
                        fmt = {}
                        if hasattr(input_format, "PDF"):
                            fmt[getattr(input_format, "PDF")] = PdfFormatOption(
                            pipeline_cls=VlmPipeline,
                            pipeline_options=vl_pipe
                        )
                        if hasattr(input_format, "IMAGE"):
                            fmt[getattr(input_format, "IMAGE")] = PdfFormatOption(
                            pipeline_cls=VlmPipeline,
                            pipeline_options=vl_pipe
                        )

                        return DocumentConverter(format_options=fmt)
                    except Exception as e:
                        raise e

                # --- Fallback: default converter with no special options ---
                return DocumentConverter()

            def export_markdown(document, ImageRefMode, image_mode, img_ph, pg_ph):
                try:
                    mode = getattr(ImageRefMode, image_mode.upper(), image_mode)
                    return document.export_to_markdown(
                        image_mode=mode,
                        image_placeholder=img_ph,
                        page_break_placeholder=pg_ph,
                    )
                except Exception:
                    try:
                        return document.export_to_text()
                    except Exception:
                        return str(document)

            def to_rows(doc_dict):
                rows = []
                for t in doc_dict.get("texts", []):
                    prov = t.get("prov") or []
                    page_no = None
                    if prov and isinstance(prov, list) and isinstance(prov[0], dict):
                        page_no = prov[0].get("page_no")
                    rows.append({
                        "page_no": page_no,
                        "label": t.get("label"),
                        "text": t.get("text"),
                        "level": t.get("level"),
                    })
                return rows

            def main():
                cfg = json.loads(sys.stdin.read())
                file_path = cfg["file_path"]
                markdown = cfg["markdown"]
                image_mode = cfg["image_mode"]
                img_ph = cfg["md_image_placeholder"]
                pg_ph = cfg["md_page_break_placeholder"]
                pipeline = cfg["pipeline"]
                ocr_engine = cfg.get("ocr_engine")
                meta = {"file_path": file_path}

                try:
                    ConversionStatus, InputFormat, DocumentConverter, ImageRefMode, strategy = try_imports()
                    converter = create_converter(strategy, InputFormat, DocumentConverter, pipeline, ocr_engine)
                    try:
                        res = converter.convert(file_path)
                    except Exception as e:
                        print(json.dumps({"ok": False, "error": f"Docling conversion error: {e}", "meta": meta}))
                        return

                    ok = False
                    if hasattr(res, "status"):
                        try:
                            ok = (res.status == ConversionStatus.SUCCESS) or (str(res.status).lower() == "success")
                        except Exception:
                            ok = (str(res.status).lower() == "success")
                    if not ok and hasattr(res, "document"):
                        ok = getattr(res, "document", None) is not None
                    if not ok:
                        print(json.dumps({"ok": False, "error": "Docling conversion failed", "meta": meta}))
                        return

                    doc = getattr(res, "document", None)
                    if doc is None:
                        print(json.dumps({"ok": False, "error": "Docling produced no document", "meta": meta}))
                        return

                    # Extract DoclingDocument metadata
                    if hasattr(doc, "name") and doc.name:
                        meta["name"] = doc.name
                    if hasattr(doc, "origin") and doc.origin is not None:
                        origin = doc.origin
                        if hasattr(origin, "filename") and origin.filename:
                            meta["filename"] = origin.filename
                        if hasattr(origin, "binary_hash") and origin.binary_hash:
                            meta["document_id"] = str(origin.binary_hash)
                        if hasattr(origin, "mimetype") and origin.mimetype:
                            meta["mimetype"] = origin.mimetype

                    if markdown:
                        text = export_markdown(doc, ImageRefMode, image_mode, img_ph, pg_ph)
                        print(json.dumps({"ok": True, "mode": "markdown", "text": text, "meta": meta}))
                        return

                    # structured
                    try:
                        doc_dict = doc.export_to_dict()
                    except Exception as e:
                        print(json.dumps({"ok": False, "error": f"Docling export_to_dict failed: {e}", "meta": meta}))
                        return

                    rows = to_rows(doc_dict)
                    print(json.dumps({"ok": True, "mode": "structured", "doc": rows, "meta": meta}))
                except Exception as e:
                    print(
                        json.dumps({
                            "ok": False,
                            "error": f"Docling processing error: {e}",
                            "meta": {"file_path": file_path},
                        })
                    )

            if __name__ == "__main__":
                main()
            """
        )

        # Validate file_path to avoid command injection or unsafe input.
        # Note: $ is intentionally not blocked here because the path is passed as JSON via
        # stdin to the subprocess, not interpolated in a shell command.
        if not isinstance(args["file_path"], str) or any(c in args["file_path"] for c in [";", "|", "&", "`"]):
            return Data(data={"error": "Unsafe file path detected.", "file_path": args["file_path"]})

        # Use Popen with a polling loop instead of blocking subprocess.run().
        # This lets us emit periodic log messages that keep the SSE event stream
        # alive in multi-worker (Gunicorn) deployments, preventing the job queue
        # from being cleaned up while Docling is still processing.
        docling_timeout = 600  # 10 minutes; large PDFs with OCR may need this
        poll_interval = 5  # seconds between progress heartbeats

        proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-u", "-c", child_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Send input and close stdin so child can proceed
        proc.stdin.write(json.dumps(args).encode("utf-8"))
        proc.stdin.close()

        start = time.monotonic()
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed >= docling_timeout:
                proc.kill()
                proc.wait()
                return Data(
                    data={
                        "error": (
                            f"Docling processing timed out after {docling_timeout}s. "
                            "Consider using the standalone Docling component for large documents."
                        ),
                        "file_path": original_file_path,
                    },
                )
            # Heartbeat: emit a log so the graph event stream stays active
            self.log(f"Docling processing in progress ({int(elapsed)}s elapsed)...")
            time.sleep(poll_interval)

        stdout_bytes = proc.stdout.read()
        stderr_bytes = proc.stderr.read()
        proc.stdout.close()
        proc.stderr.close()

        if not stdout_bytes:
            err_msg = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else "no output from child process"
            return Data(data={"error": f"Docling subprocess error: {err_msg}", "file_path": original_file_path})

        try:
            result = json.loads(stdout_bytes.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            err_msg = stderr_bytes.decode("utf-8", errors="replace")
            return Data(
                data={
                    "error": f"Invalid JSON from Docling subprocess: {e}. stderr={err_msg}",
                    "file_path": original_file_path,
                },
            )

        if not result.get("ok"):
            error_msg = result.get("error", "Unknown Docling error")
            # Override meta file_path with original_file_path to ensure correct path matching
            meta = result.get("meta", {})
            meta["file_path"] = original_file_path
            return Data(data={"error": error_msg, **meta})

        meta = result.get("meta", {})
        # Override meta file_path with original_file_path to ensure correct path matching
        # The subprocess returns the temp file path, but we need the original S3/local path for rollup_data
        meta["file_path"] = original_file_path
        if result.get("mode") == "markdown":
            exported_content = str(result.get("text", ""))
            return Data(
                text=exported_content,
                data={"exported_content": exported_content, "export_format": self.EXPORT_FORMAT, **meta},
            )

        rows = list(result.get("doc", []))
        return Data(data={"doc": rows, "export_format": self.EXPORT_FORMAT, **meta})