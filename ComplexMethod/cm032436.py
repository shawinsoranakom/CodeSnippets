def _make_epub(chapters, include_container=True, spine_order=None):
    """Build a minimal EPUB ZIP in memory.

    Args:
        chapters: list of (filename, html_content) tuples.
        include_container: whether to include META-INF/container.xml.
        spine_order: optional list of filenames for spine ordering.
                     Defaults to the order of `chapters`.
    """
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")

        if include_container:
            container_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
                "  <rootfiles>"
                '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                "  </rootfiles>"
                "</container>"
            )
            zf.writestr("META-INF/container.xml", container_xml)

            if spine_order is None:
                spine_order = [fn for fn, _ in chapters]

            manifest_items = ""
            for i, (fn, _) in enumerate(chapters):
                manifest_items += f'<item id="ch{i}" href="{fn}" media-type="application/xhtml+xml"/>'

            spine_refs = ""
            fn_to_id = {fn: f"ch{i}" for i, (fn, _) in enumerate(chapters)}
            for fn in spine_order:
                spine_refs += f'<itemref idref="{fn_to_id[fn]}"/>'

            opf_xml = (
                f'<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0">  <manifest>{manifest_items}</manifest>  <spine>{spine_refs}</spine></package>'
            )
            zf.writestr("OEBPS/content.opf", opf_xml)

        for fn, content in chapters:
            path = f"OEBPS/{fn}" if include_container else fn
            zf.writestr(path, content)

    return buf.getvalue()