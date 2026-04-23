def _docx(self, name, blob, **kwargs):
        """Parse DOCX files and optionally remove table-of-contents content."""
        self.callback(random.randint(1, 5) / 100.0, "Start to work on a DOCX document")
        conf = self._param.setups["docx"]
        self.set_output("output_format", conf["output_format"])
        flatten_media_to_text = conf.get("flatten_media_to_text")

        if re.search(r"\.doc$", name, re.IGNORECASE):
            self.set_output("file", {**kwargs.get("file", {}), "outlines": []})
            try:
                from tika import parser as tika_parser
            except Exception as e:
                msg = f"tika not available: {e}. Unsupported .doc parsing."
                self.callback(0.8, msg)
                logging.warning(f"{msg} for {name}.")
                return

            doc_parsed = tika_parser.from_buffer(io.BytesIO(blob))
            content = doc_parsed.get("content")
            if content is None:
                msg = f"tika.parser got empty content from {name}."
                self.callback(0.8, msg)
                logging.warning(msg)
                return

            sections = [line.strip() for line in content.splitlines() if line and line.strip()]
            if conf.get("remove_toc"):
                sections = remove_toc_word(sections, [])

            if conf.get("output_format") == "json":
                self.set_output(
                    "json",
                    [{"text": line, "image": None, "doc_type_kwd": "text"} for line in sections],
                )
            elif conf.get("output_format") == "markdown":
                # Tika gives us plain text lines, so join with blank lines to preserve paragraph boundaries in markdown.
                self.set_output("markdown", "\n\n".join(sections))

            self.callback(0.8, "Finish parsing.")
            return

        docx_parser = Docx()

        # Extract heading-based outlines for metadata and TOC removal.
        outlines = extract_word_outlines(name, blob)
        self.set_output("file", {**kwargs.get("file", {}), "outlines": outlines})

        # JSON output keeps text/image blocks and appends table HTML as table items.
        if conf.get("output_format") == "json":
            main_sections = docx_parser(name, binary=blob)
            if conf.get("remove_toc"):
                main_sections = remove_toc_word(main_sections, outlines)
            sections = []
            for text, image, html in main_sections:
                sections.append(
                    {
                        "text": text,
                        "image": image,
                        "doc_type_kwd": "text" if flatten_media_to_text or image is None else "image",
                    }
                )
                if html:
                    sections.append(
                        {
                            "text": html,
                            "image": None,
                            "doc_type_kwd": "text" if flatten_media_to_text else "table",
                        }
                    )
            enhance_media_sections_with_vision(
                sections,
                self._canvas._tenant_id,
                conf.get("vlm"),
                callback=self.callback,
            )

            self.set_output("json", sections)

        # Markdown output removes TOC on plain markdown lines before writing back.
        elif conf.get("output_format") == "markdown":
            markdown_text = docx_parser.to_markdown(name, binary=blob)
            if conf.get("remove_toc"):
                markdown_text = "\n".join(remove_toc_word(markdown_text.split("\n"), outlines))

            self.set_output("markdown", markdown_text)