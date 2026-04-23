def supports_filename(filename: str):
    if filename.endswith(".pdf"):
        if has_pypdf2:
            return True
        elif has_pdfplumber:
            return True
        elif has_pdfminer:
            return True
        raise MissingRequirementsError(f'Install "pypdf2" requirements | pip install -U g4f[files]')
    elif filename.endswith(".docx"):
        if has_docx:
            return True
        elif has_docx2txt:
            return True
        raise MissingRequirementsError(f'Install "docx" requirements | pip install -U g4f[files]')
    elif has_odfpy and filename.endswith(".odt"):
        return True
    elif has_ebooklib and filename.endswith(".epub"):
        return True
    elif has_openpyxl and filename.endswith(".xlsx"):
        return True
    elif filename.endswith(".html"):
        if not has_beautifulsoup4:
            raise MissingRequirementsError(f'Install "beautifulsoup4" requirements | pip install -U g4f[files]')
        return True
    elif filename.endswith(".zip"):
        return True
    elif filename.endswith("package-lock.json") and filename != FILE_LIST:
        return False
    else:
        extension = os.path.splitext(filename)[1][1:]
        if extension in PLAIN_FILE_EXTENSIONS:
            return True
    return False