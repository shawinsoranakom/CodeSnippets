def _get_mime_type_prefixes(types: List[DocumentIntelligenceFileType]) -> List[str]:
    """Get the MIME type prefixes for the given file types."""
    prefixes: List[str] = []
    for type_ in types:
        if type_ == DocumentIntelligenceFileType.DOCX:
            prefixes.append(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        elif type_ == DocumentIntelligenceFileType.PPTX:
            prefixes.append(
                "application/vnd.openxmlformats-officedocument.presentationml"
            )
        elif type_ == DocumentIntelligenceFileType.XLSX:
            prefixes.append(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif type_ == DocumentIntelligenceFileType.HTML:
            prefixes.append("text/html")
            prefixes.append("application/xhtml+xml")
        elif type_ == DocumentIntelligenceFileType.PDF:
            prefixes.append("application/pdf")
            prefixes.append("application/x-pdf")
        elif type_ == DocumentIntelligenceFileType.JPEG:
            prefixes.append("image/jpeg")
        elif type_ == DocumentIntelligenceFileType.PNG:
            prefixes.append("image/png")
        elif type_ == DocumentIntelligenceFileType.BMP:
            prefixes.append("image/bmp")
        elif type_ == DocumentIntelligenceFileType.TIFF:
            prefixes.append("image/tiff")
    return prefixes