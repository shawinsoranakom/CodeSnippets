def _spreadsheet(self, name, blob, **kwargs):
        """Parse spreadsheet files and normalize them into html/json/markdown output."""
        self.callback(random.randint(1, 5) / 100.0, "Start to work on a Spreadsheet.")
        conf = self._param.setups["spreadsheet"]
        self.set_output("output_format", conf["output_format"])
        flatten_media_to_text = conf.get("flatten_media_to_text")

        parse_method = conf.get("parse_method", "deepdoc")

        # Handle TCADP parser
        if parse_method.lower() == "tcadp parser":
            table_result_type = conf.get("table_result_type", "1")
            markdown_image_response_type = conf.get("markdown_image_response_type", "1")
            tcadp_parser = TCADPParser(
                table_result_type=table_result_type,
                markdown_image_response_type=markdown_image_response_type,
            )
            if not tcadp_parser.check_installation():
                raise RuntimeError("TCADP parser not available. Please check Tencent Cloud API configuration.")

            # Determine file type based on extension
            if re.search(r"\.xlsx?$", name, re.IGNORECASE):
                file_type = "XLSX"
            else:
                file_type = "CSV"

            self.callback(0.2, f"Using TCADP parser for {file_type} file.")
            sections, tables = tcadp_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                file_type=file_type,
                file_start_page=1,
                file_end_page=1000,
            )

            # Process TCADP parser output based on configured output_format
            output_format = conf.get("output_format", "html")

            if output_format == "html":
                # For HTML output, combine sections and tables into HTML
                html_content = ""
                for section, position_tag in sections:
                    if section:
                        html_content += section + "\n"
                for table in tables:
                    if table:
                        html_content += table + "\n"

                self.set_output("html", html_content)

            elif output_format == "json":
                # For JSON output, create a list of text items
                result = []
                # Add sections as text
                for section, position_tag in sections:
                    if section:
                        result.append({"text": section, "doc_type_kwd": "text"})
                # Add tables as text
                for table in tables:
                    if table:
                        result.append(
                            {
                                "text": table,
                                "doc_type_kwd": "text" if flatten_media_to_text else "table",
                            }
                        )

                self.set_output("json", result)

            elif output_format == "markdown":
                # For markdown output, combine into markdown
                md_content = ""
                for section, position_tag in sections:
                    if section:
                        md_content += section + "\n\n"
                for table in tables:
                    if table:
                        md_content += table + "\n\n"

                self.set_output("markdown", md_content)
        else:
            # Default DeepDOC parser
            spreadsheet_parser = ExcelParser()
            if conf.get("output_format") == "html":
                htmls = spreadsheet_parser.html(blob, 1000000000)
                self.set_output("html", htmls[0])
            elif conf.get("output_format") == "json":
                self.set_output("json", [{"text": txt, "doc_type_kwd": "text"} for txt in spreadsheet_parser(blob) if txt])
            elif conf.get("output_format") == "markdown":
                self.set_output("markdown", spreadsheet_parser.markdown(blob))