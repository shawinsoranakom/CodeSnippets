def _slides(self, name, blob, **kwargs):
        """Parse presentation files into json sections."""
        self.callback(random.randint(1, 5) / 100.0, "Start to work on a PowerPoint Document")

        conf = self._param.setups["slides"]
        self.set_output("output_format", conf["output_format"])

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
            if re.search(r"\.pptx?$", name, re.IGNORECASE):
                file_type = "PPTX"
            else:
                file_type = "PPT"

            self.callback(0.2, f"Using TCADP parser for {file_type} file.")

            sections, tables = tcadp_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                file_type=file_type,
                file_start_page=1,
                file_end_page=1000,
            )

            # Process TCADP parser output - PPT only supports json format
            output_format = conf.get("output_format", "json")
            if output_format == "json":
                # For JSON output, create a list of text items
                result = []
                # Add sections as text
                for section, position_tag in sections:
                    if section:
                        result.append({"text": section, "doc_type_kwd": "text"})
                # Add tables as text
                for table in tables:
                    if table:
                        result.append({"text": table, "doc_type_kwd": "table"})

                self.set_output("json", result)
        else:
            # Default DeepDOC parser (supports .pptx format)
            from deepdoc.parser.ppt_parser import RAGFlowPptParser as ppt_parser

            ppt_parser = ppt_parser()
            txts = ppt_parser(blob, 0, 100000, None)

            sections = [{"text": section, "doc_type_kwd": "text"} for section in txts if section.strip()]

            # json
            assert conf.get("output_format") == "json", "have to be json for ppt"
            if conf.get("output_format") == "json":
                self.set_output("json", sections)