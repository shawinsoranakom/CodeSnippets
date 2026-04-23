def extract_embed_file(target: Union[bytes, bytearray]) -> List[Tuple[str, bytes]]:
    """
    Only extract the 'first layer' of embedding, returning raw (filename, bytes).
    """
    top = bytes(target)
    head = top[:8]
    out: List[Tuple[str, bytes]] = []
    seen = set()

    def push(b: bytes, name_hint: str = ""):
        h10 = _sha10(b)
        if h10 in seen:
            return
        seen.add(h10)
        ext = _guess_ext(b)
        # If name_hint has an extension use its basename; else fallback to guessed ext
        if "." in name_hint:
            fname = name_hint.split("/")[-1]
        else:
            fname = f"{h10}{ext}"
        out.append((fname, b))

    # OOXML/ZIP container (docx/xlsx/pptx)
    if _is_zip(head):
        try:
            with zipfile.ZipFile(io.BytesIO(top), "r") as z:
                embed_dirs = (
                    "word/embeddings/", "word/objects/", "word/activex/",
                    "xl/embeddings/", "ppt/embeddings/"
                )
                for name in z.namelist():
                    low = name.lower()
                    if any(low.startswith(d) for d in embed_dirs):
                        try:
                            b = z.read(name)
                            push(b, name)
                        except Exception:
                            pass
        except Exception:
            pass
        return out

    # OLE container (doc/ppt/xls)
    if _is_ole(head):
        try:
            with olefile.OleFileIO(io.BytesIO(top)) as ole:
                for entry in ole.listdir():
                    p = "/".join(entry)
                    try:
                        data = ole.openstream(entry).read()
                    except Exception:
                        continue
                    if not data:
                        continue
                    if "Ole10Native" in p or "ole10native" in p.lower():
                        data = _extract_ole10native_payload(data)
                    push(data, p)
        except Exception:
            pass
        return out

    return out