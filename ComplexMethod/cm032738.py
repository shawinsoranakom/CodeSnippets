def check(self):
        pdf_config = self.setups.get("pdf", {})
        if pdf_config:
            pdf_parse_method = pdf_config.get("parse_method", "")
            self.check_empty(pdf_parse_method, "Parse method abnormal.")

            if pdf_parse_method.lower() not in ["deepdoc", "plain_text", "mineru", "docling", "tcadp parser", "paddleocr"]:
                self.check_empty(pdf_config.get("lang", ""), "PDF VLM language")

            pdf_output_format = pdf_config.get("output_format", "")
            self.check_valid_value(pdf_output_format, "PDF output format abnormal.", self.allowed_output_format["pdf"])

        spreadsheet_config = self.setups.get("spreadsheet", "")
        if spreadsheet_config:
            spreadsheet_output_format = spreadsheet_config.get("output_format", "")
            self.check_valid_value(spreadsheet_output_format, "Spreadsheet output format abnormal.", self.allowed_output_format["spreadsheet"])

        doc_config = self.setups.get("doc", "")
        if doc_config:
            doc_output_format = doc_config.get("output_format", "")
            self.check_valid_value(doc_output_format, "DOC output format abnormal.", self.allowed_output_format["doc"])

        docx_config = self.setups.get("docx", "")
        if docx_config:
            docx_output_format = docx_config.get("output_format", "")
            self.check_valid_value(docx_output_format, "DOCX output format abnormal.", self.allowed_output_format["docx"])

        slides_config = self.setups.get("slides", "")
        if slides_config:
            slides_output_format = slides_config.get("output_format", "")
            self.check_valid_value(slides_output_format, "Slides output format abnormal.", self.allowed_output_format["slides"])

        image_config = self.setups.get("image", "")
        if image_config:
            image_parse_method = image_config.get("parse_method", "")
            if image_parse_method not in ["ocr"]:
                self.check_empty(image_config.get("lang", ""), "Image VLM language")

        text_config = self.setups.get("markdown", "")
        if text_config:
            text_output_format = text_config.get("output_format", "")
            self.check_valid_value(text_output_format, "Markdown output format abnormal.", self.allowed_output_format["markdown"])

        code_config = self.setups.get("text&code", "")
        if code_config:
            code_output_format = code_config.get("output_format", "")
            self.check_valid_value(code_output_format, "Text&Code output format abnormal.", self.allowed_output_format["text&code"])

        html_config = self.setups.get("html", "")
        if html_config:
            html_output_format = html_config.get("output_format", "")
            self.check_valid_value(html_output_format, "HTML output format abnormal.", self.allowed_output_format["html"])

        audio_config = self.setups.get("audio", "")
        if audio_config:
            audio_vlm = audio_config.get("vlm") or {}
            self.check_empty(audio_vlm.get("llm_id"), "Audio VLM")

        video_config = self.setups.get("video", "")
        if video_config:
            video_vlm = video_config.get("vlm") or {}
            self.check_empty(video_vlm.get("llm_id"), "Video VLM")
        email_config = self.setups.get("email", "")
        if email_config:
            email_output_format = email_config.get("output_format", "")
            self.check_valid_value(email_output_format, "Email output format abnormal.", self.allowed_output_format["email"])

        epub_config = self.setups.get("epub", "")
        if epub_config:
            epub_output_format = epub_config.get("output_format", "")
            self.check_valid_value(epub_output_format, "EPUB output format abnormal.", self.allowed_output_format["epub"])