def stream_read_files(bucket_dir: Path, filenames: list[str], delete_files: bool = False) -> Iterator[str]:
    for filename in filenames:
        if filename.startswith(DOWNLOADS_FILE):
            continue
        file_path: Path = bucket_dir / filename
        if not file_path.exists() or file_path.lstat().st_size <= 0:
            continue
        extension = os.path.splitext(filename)[1][1:]
        if filename.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(bucket_dir)
                try:
                    yield from stream_read_files(bucket_dir, [f for f in zip_ref.namelist() if supports_filename(f)], delete_files)
                except zipfile.BadZipFile:
                    pass
                finally:
                    if delete_files:
                        for unlink in zip_ref.namelist()[::-1]:
                            filepath = os.path.join(bucket_dir, unlink)
                            if os.path.exists(filepath):
                                if os.path.isdir(filepath):
                                    os.rmdir(filepath)
                                else:
                                    os.unlink(filepath)
            continue
        yield f"<!-- File: {filename} -->\n"
        if has_pypdf2 and filename.endswith(".pdf"):
            try:
                reader = PyPDF2.PdfReader(file_path)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    yield page.extract_text()
            except PdfReadError:
                continue
        if has_pdfplumber and filename.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    yield page.extract_text()
        if has_pdfminer and filename.endswith(".pdf"):
            yield extract_text(file_path)
        elif has_docx and filename.endswith(".docx"):
            doc = Document(file_path)
            for para in doc.paragraphs:
                yield para.text
        elif has_docx2txt and filename.endswith(".docx"):
            yield docx2txt.process(file_path)
        elif has_odfpy and filename.endswith(".odt"):
            textdoc = load(file_path)
            allparas = textdoc.getElementsByType(P)
            for p in allparas:
                yield p.firstChild.data if p.firstChild else ""
        elif has_ebooklib and filename.endswith(".epub"):
            book = epub.read_epub(file_path)
            for doc_item in book.get_items():
                if doc_item.get_type() == ebooklib.ITEM_DOCUMENT:
                    yield doc_item.get_content().decode(errors='ignore')
        elif has_openpyxl and filename.endswith(".xlsx"):
            df = pd.read_excel(file_path)
            for row in df.itertuples(index=False):
                yield " ".join(str(cell) for cell in row)
        elif has_beautifulsoup4 and filename.endswith(".html"):
            yield from scrape_text(file_path.read_text(errors="ignore"))
        elif extension in PLAIN_FILE_EXTENSIONS:
            yield file_path.read_text(errors="ignore").strip()
        yield f"\n<-- End -->\n\n"