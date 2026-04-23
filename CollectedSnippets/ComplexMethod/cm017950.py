def _get_file_extensions(types: List[DocumentIntelligenceFileType]) -> List[str]:
    """Get the file extensions for the given file types."""
    extensions: List[str] = []
    for type_ in types:
        if type_ == DocumentIntelligenceFileType.DOCX:
            extensions.append(".docx")
        elif type_ == DocumentIntelligenceFileType.PPTX:
            extensions.append(".pptx")
        elif type_ == DocumentIntelligenceFileType.XLSX:
            extensions.append(".xlsx")
        elif type_ == DocumentIntelligenceFileType.PDF:
            extensions.append(".pdf")
        elif type_ == DocumentIntelligenceFileType.JPEG:
            extensions.append(".jpg")
            extensions.append(".jpeg")
        elif type_ == DocumentIntelligenceFileType.PNG:
            extensions.append(".png")
        elif type_ == DocumentIntelligenceFileType.BMP:
            extensions.append(".bmp")
        elif type_ == DocumentIntelligenceFileType.TIFF:
            extensions.append(".tiff")
        elif type_ == DocumentIntelligenceFileType.HTML:
            extensions.append(".html")
    return extensions