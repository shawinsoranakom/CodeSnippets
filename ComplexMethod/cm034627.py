def detect_file_type(binary_data: bytes) -> tuple[str, str] | None:
    """
    Detect file type from magic number / header signature.

    Args:
        binary_data (bytes): File binary data

    Returns:
        tuple: (extension, MIME type)

    Raises:
        ValueError: If file type is unknown
    """

    # ---- Images ----
    if binary_data.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    elif binary_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    elif binary_data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif", "image/gif"
    elif binary_data.startswith(b"RIFF") and binary_data[8:12] == b"WEBP":
        return ".webp", "image/webp"
    elif binary_data.startswith(b"BM"):
        return ".bmp", "image/bmp"
    elif binary_data.startswith(b"II*\x00") or binary_data.startswith(b"MM\x00*"):
        return ".tiff", "image/tiff"
    elif binary_data.startswith(b"\x00\x00\x01\x00"):
        return ".ico", "image/x-icon"
    elif binary_data.startswith(b"\x00\x00\x00\x0cjP  \x0d\x0a\x87\x0a"):
        return ".jp2", "image/jp2"
    elif len(binary_data) > 12 and binary_data[4:8] == b"ftyp":
        brand = binary_data[8:12]
        if brand in [b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"]:
            return ".heic", "image/heif"
        elif brand in [b"avif"]:
            return ".avif", "image/avif"
        else:
            return ".mp4", "video/mp4"
    elif binary_data.lstrip().startswith((b"<?xml", b"<svg")):
        return ".svg", "image/svg+xml"

    # ---- Documents ----
    elif binary_data.startswith(b"%PDF"):
        return ".pdf", "application/pdf"
    elif binary_data.startswith(b"PK\x03\x04"):
        return ".zip", "application/zip-based"
          # could be docx/xlsx/pptx/jar/apk/odt
    elif binary_data.startswith(b"\xd0\xcf\x11\xe0"):
        return ".doc", "application/vnd.ms-office"
    elif binary_data.startswith(b"{\\rtf"):
        return ".rtf", "application/rtf"
    elif binary_data.startswith(b"7z\xbc\xaf\x27\x1c"):
        return ".7z", "application/x-7z-compressed"
    elif binary_data.startswith(b"Rar!\x1a\x07\x00"):
        return ".rar", "application/vnd.rar"
    elif binary_data.startswith(b"\x1f\x8b"):
        return ".gz", "application/gzip"
    elif binary_data.startswith(b"BZh"):
        return ".bz2", "application/x-bzip2"
    elif binary_data.startswith(b"\xfd7zXZ\x00"):
        return ".xz", "application/x-xz"

    # ---- Executables / Libraries ----
    elif binary_data.startswith(b"MZ"):
        return ".exe", "application/x-msdownload"
    elif binary_data.startswith(b"\x7fELF"):
        return ".elf", "application/x-elf"
    elif binary_data.startswith(b"\xca\xfe\xba\xbe") or binary_data.startswith(
            b"\xca\xfe\xd0\x0d"
    ):
        return ".class", "application/java-vm"
    elif (
            binary_data.startswith(b"\x50\x4b\x03\x04")
            and b"META-INF" in binary_data[:200]
    ):
        return ".jar", "application/java-archive"

    # ---- Audio ----
    elif binary_data.startswith(b"ID3") or binary_data[0:2] == b"\xff\xfb":
        return ".mp3", "audio/mpeg"
    elif binary_data.startswith(b"OggS"):
        return ".ogg", "audio/ogg"
    elif binary_data.startswith(b"fLaC"):
        return ".flac", "audio/flac"
    elif binary_data.startswith(b"RIFF") and binary_data[8:12] == b"WAVE":
        return ".wav", "audio/wav"
    elif binary_data.startswith(b"MThd"):
        return ".mid", "audio/midi"

    # ---- Video ----
    elif binary_data.startswith(b"\x00\x00\x00") and b"ftyp" in binary_data[4:12]:
        return ".mp4", "video/mp4"
    elif binary_data.startswith(b"RIFF") and binary_data[8:12] == b"AVI ":
        return ".avi", "video/x-msvideo"
    elif binary_data.startswith(b"OggS"):
        return ".ogv", "video/ogg"
    elif binary_data.startswith(b"\x1a\x45\xdf\xa3"):
        return ".mkv", "video/webm"
    elif binary_data.startswith(b"\x00\x00\x01\xba"):
        return ".mpg", "video/mpeg"

    # ---- Text / Scripts ----
    elif binary_data.lstrip().startswith(b"#!"):
        return ".sh", "text/x-script"
    elif binary_data.lstrip().startswith((b"{", b"[")):
        return ".json", "application/json"
    elif binary_data.lstrip().startswith((b"<", b"<!DOCTYPE")):
        return ".html", "text/html"
    elif binary_data.lstrip().startswith(b"<?xml"):
        return ".xml", "application/xml"
    elif all(32 <= b <= 127 or b in (9, 10, 13) for b in binary_data[:100]):
        return ".txt", "text/plain"

    else:
        raise ValueError("Unknown or unsupported file type")