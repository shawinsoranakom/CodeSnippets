def parse_pdf(
        self,
        filepath: str | PathLike[str],
        binary: BytesIO | bytes | None = None,
        callback: Optional[Callable] = None,
        *,
        output_dir: Optional[str] = None, 
        lang: Optional[str] = None,        
        method: str = "auto",             
        delete_output: bool = True,
        parse_method: str = "raw",
        docling_server_url: Optional[str] = None,
        request_timeout: Optional[int] = None,
    ):
        self.outlines = extract_pdf_outlines(binary if binary is not None else filepath)

        if not self.check_installation(docling_server_url=docling_server_url):
            raise RuntimeError("Docling not available, please install `docling`")

        server_url = self._effective_server_url(docling_server_url)
        if server_url:
            return self._parse_pdf_remote(
                filepath=filepath,
                binary=binary,
                callback=callback,
                parse_method=parse_method,
                docling_server_url=server_url,
                request_timeout=request_timeout,
            )

        if binary is not None:
            tmpdir = Path(output_dir) if output_dir else Path.cwd() / ".docling_tmp"
            tmpdir.mkdir(parents=True, exist_ok=True)
            name = Path(filepath).name or "input.pdf"
            tmp_pdf = tmpdir / name
            with open(tmp_pdf, "wb") as f:
                if isinstance(binary, (bytes, bytearray)):
                    f.write(binary)
                else:
                    f.write(binary.getbuffer())
            src_path = tmp_pdf
        else:
            src_path = Path(filepath)
            if not src_path.exists():
                raise FileNotFoundError(f"PDF not found: {src_path}")

        if callback:
            callback(0.1, f"[Docling] Converting: {src_path}")

        try:
            self.__images__(str(src_path), zoomin=1)
        except Exception as e:
            self.logger.warning(f"[Docling] render pages failed: {e}")

        conv = DocumentConverter()  
        conv_res = conv.convert(str(src_path))
        doc = conv_res.document
        if callback:
            callback(0.7, f"[Docling] Parsed doc: {getattr(doc, 'num_pages', 'n/a')} pages")

        sections = self._transfer_to_sections(doc, parse_method=parse_method)
        tables = self._transfer_to_tables(doc)

        if callback:
            callback(0.95, f"[Docling] Sections: {len(sections)}, Tables: {len(tables)}")

        if binary is not None and delete_output:
            try:
                Path(src_path).unlink(missing_ok=True)
            except Exception:
                pass

        if callback:
            callback(1.0, "[Docling] Done.")
        return sections, tables