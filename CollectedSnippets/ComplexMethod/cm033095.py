def _parse_pdf_remote(
        self,
        filepath: str | PathLike[str],
        binary: BytesIO | bytes | None = None,
        callback: Optional[Callable] = None,
        *,
        parse_method: str = "raw",
        docling_server_url: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ):
        server_url = self._effective_server_url(docling_server_url)
        if not server_url:
            raise RuntimeError("[Docling] DOCLING_SERVER_URL is not configured.")

        timeout = request_timeout or self.request_timeout
        if binary is not None:
            if isinstance(binary, (bytes, bytearray)):
                pdf_bytes = bytes(binary)
            else:
                pdf_bytes = bytes(binary.getbuffer())
        else:
            src_path = Path(filepath)
            if not src_path.exists():
                raise FileNotFoundError(f"PDF not found: {src_path}")
            with open(src_path, "rb") as f:
                pdf_bytes = f.read()

        if callback:
            callback(0.2, f"[Docling] Requesting external server: {server_url}")

        filename = Path(filepath).name or "input.pdf"
        b64 = base64.b64encode(pdf_bytes).decode("ascii")
        v1_payload = {
            "options": {
                "from_formats": ["pdf"],
                "to_formats": ["json", "md", "text"],
            },
            "sources": [
                {
                    "kind": "file",
                    "filename": filename,
                    "base64_string": b64,
                }
            ],
        }
        v1alpha_payload = {
            "options": {
                "from_formats": ["pdf"],
                "to_formats": ["json", "md", "text"],
            },
            "file_sources": [
                {
                    "filename": filename,
                    "base64_string": b64,
                }
            ],
        }
        errors = []
        response_json = None
        for endpoint, payload in (
            ("/v1/convert/source", v1_payload),
            ("/v1alpha/convert/source", v1alpha_payload),
        ):
            try:
                resp = requests.post(
                    f"{server_url}{endpoint}",
                    json=payload,
                    timeout=timeout,
                )
                if resp.status_code < 300:
                    response_json = resp.json()
                    break
                errors.append(f"{endpoint}: HTTP {resp.status_code} {resp.text[:300]}")
            except Exception as exc:
                errors.append(f"{endpoint}: {exc}")

        if response_json is None:
            raise RuntimeError("[Docling] remote convert failed: " + " | ".join(errors))

        docs = self._extract_remote_document_entries(response_json)
        if not docs:
            raise RuntimeError("[Docling] remote response does not contain parsed documents.")

        sections: list[tuple[str, ...]] = []
        tables = []
        for doc in docs:
            md = doc.get("md_content")
            txt = doc.get("text_content")
            if isinstance(md, str) and md.strip():
                sections.extend(self._sections_from_remote_text(md, parse_method=parse_method))
            elif isinstance(txt, str) and txt.strip():
                sections.extend(self._sections_from_remote_text(txt, parse_method=parse_method))

            json_content = doc.get("json_content")
            if isinstance(json_content, dict):
                md_fallback = json_content.get("md_content")
                if isinstance(md_fallback, str) and md_fallback.strip() and not sections:
                    sections.extend(self._sections_from_remote_text(md_fallback, parse_method=parse_method))

        if callback:
            callback(0.95, f"[Docling] Remote sections: {len(sections)}")
        return sections, tables