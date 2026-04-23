def _markdown(self, name, blob, **kwargs):
        """Parse markdown files into text/json sections."""
        from functools import reduce

        from rag.app.naive import Markdown as naive_markdown_parser
        from rag.nlp import concat_img

        self.callback(random.randint(1, 5) / 100.0, "Start to work on a markdown.")
        conf = self._param.setups["markdown"]
        self.set_output("output_format", conf["output_format"])
        flatten_media_to_text = conf.get("flatten_media_to_text")

        markdown_parser = naive_markdown_parser()
        sections, tables, section_images = markdown_parser(
            name,
            blob,
            separate_tables=False,
            delimiter=conf.get("delimiter"),
            return_section_images=True,
        )

        if conf.get("output_format") == "json":
            json_results = []

            for idx, (section_text, _) in enumerate(sections):
                json_result = {
                    "text": section_text,
                }

                images = []
                if section_images and len(section_images) > idx and section_images[idx] is not None:
                    images.append(section_images[idx])
                if images:
                    # If multiple images found, combine them using concat_img
                    combined_image = reduce(concat_img, images) if len(images) > 1 else images[0]
                    json_result["image"] = combined_image
                json_result["doc_type_kwd"] = (
                    "text"
                    if flatten_media_to_text or json_result.get("image") is None
                    else "image"
                )
                json_results.append(json_result)

            for table in tables:
                table_text = table[0][1] if table and table[0] else ""
                if table_text:
                    json_results.append(
                        {
                            "text": table_text,
                            "doc_type_kwd": "text" if flatten_media_to_text else "table",
                        }
                    )

            enhance_media_sections_with_vision(
                json_results,
                self._canvas._tenant_id,
                conf.get("vlm"),
                callback=self.callback,
            )
            self.set_output("json", json_results)
        else:
            texts = [section_text for section_text, _ in sections if section_text]
            texts.extend(table[0][1] for table in tables if table and table[0] and table[0][1])
            self.set_output("text", "\n".join(texts))