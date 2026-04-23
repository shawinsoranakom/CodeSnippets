def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        with zipfile.ZipFile(file_stream, "r") as z:
            # Extracts metadata (title, authors, language, publisher, date, description, cover) from an EPUB file."""

            # Locate content.opf
            container_dom = minidom.parse(z.open("META-INF/container.xml"))
            opf_path = container_dom.getElementsByTagName("rootfile")[0].getAttribute(
                "full-path"
            )

            # Parse content.opf
            opf_dom = minidom.parse(z.open(opf_path))
            metadata: Dict[str, Any] = {
                "title": self._get_text_from_node(opf_dom, "dc:title"),
                "authors": self._get_all_texts_from_nodes(opf_dom, "dc:creator"),
                "language": self._get_text_from_node(opf_dom, "dc:language"),
                "publisher": self._get_text_from_node(opf_dom, "dc:publisher"),
                "date": self._get_text_from_node(opf_dom, "dc:date"),
                "description": self._get_text_from_node(opf_dom, "dc:description"),
                "identifier": self._get_text_from_node(opf_dom, "dc:identifier"),
            }

            # Extract manifest items (ID → href mapping)
            manifest = {
                item.getAttribute("id"): item.getAttribute("href")
                for item in opf_dom.getElementsByTagName("item")
            }

            # Extract spine order (ID refs)
            spine_items = opf_dom.getElementsByTagName("itemref")
            spine_order = [item.getAttribute("idref") for item in spine_items]

            # Convert spine order to actual file paths
            base_path = "/".join(
                opf_path.split("/")[:-1]
            )  # Get base directory of content.opf
            spine = [
                f"{base_path}/{manifest[item_id]}" if base_path else manifest[item_id]
                for item_id in spine_order
                if item_id in manifest
            ]

            # Extract and convert the content
            markdown_content: List[str] = []
            for file in spine:
                if file in z.namelist():
                    with z.open(file) as f:
                        filename = os.path.basename(file)
                        extension = os.path.splitext(filename)[1].lower()
                        mimetype = MIME_TYPE_MAPPING.get(extension)
                        converted_content = self._html_converter.convert(
                            f,
                            StreamInfo(
                                mimetype=mimetype,
                                extension=extension,
                                filename=filename,
                            ),
                        )
                        markdown_content.append(converted_content.markdown.strip())

            # Format and add the metadata
            metadata_markdown = []
            for key, value in metadata.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                if value:
                    metadata_markdown.append(f"**{key.capitalize()}:** {value}")

            markdown_content.insert(0, "\n".join(metadata_markdown))

            return DocumentConverterResult(
                markdown="\n\n".join(markdown_content), title=metadata["title"]
            )