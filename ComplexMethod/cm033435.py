def repair_pdf_with_ghostscript(input_bytes):
    """Attempt to repair corrupt PDF bytes via Ghostscript. Returns original bytes on failure or timeout."""
    if input_bytes is None or len(input_bytes) == 0:
        return input_bytes if input_bytes is not None else b""
    if len(input_bytes) > MAX_BLOB_SIZE_PDF:
        return input_bytes

    if shutil.which("gs") is None:
        return input_bytes

    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_in, tempfile.NamedTemporaryFile(suffix=".pdf") as temp_out:
        temp_in.write(input_bytes)
        temp_in.flush()

        cmd = [
            "gs",
            "-o",
            temp_out.name,
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            temp_in.name,
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=GHOSTSCRIPT_TIMEOUT_SEC,
            )
            if proc.returncode != 0:
                return input_bytes
            temp_out.seek(0)
            repaired_bytes = temp_out.read()
            if not repaired_bytes:
                return input_bytes
            return repaired_bytes
        except subprocess.TimeoutExpired:
            return input_bytes
        except Exception:
            return input_bytes