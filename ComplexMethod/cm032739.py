def _pdf(self, name, blob, **kwargs):
        """Parse PDF files into structured boxes or markdown/json output."""
        self.callback(random.randint(1, 5) / 100.0, "Start to work on a PDF.")
        conf = self._param.setups["pdf"]
        self.set_output("output_format", conf["output_format"])
        flatten_media_to_text = conf.get("flatten_media_to_text")
        pdf_parser = None

        # Optional PDF post-processing flags applied after parsing.
        abstract_enabled = "abstract" in conf.get("preprocess", [])
        author_enabled = "author" in conf.get("preprocess", [])

        # Normalize parser selection and optional provider-specific model name.
        raw_parse_method = conf.get("parse_method", "")
        parser_model_name = None
        parse_method = raw_parse_method
        parse_method = parse_method or ""
        if isinstance(raw_parse_method, str):
            lowered = raw_parse_method.lower()
            if lowered.endswith("@mineru"):
                parser_model_name = raw_parse_method.rsplit("@", 1)[0]
                parse_method = "MinerU"
            elif lowered.endswith("@paddleocr"):
                parser_model_name = raw_parse_method.rsplit("@", 1)[0]
                parse_method = "PaddleOCR"

        # DeepDOC returns structured page boxes directly.
        if parse_method.lower() == "deepdoc":
            pdf_parser = RAGFlowPdfParser()
            bboxes = pdf_parser.parse_into_bboxes(blob, callback=self.callback)
            if conf.get("enable_multi_column"):
                bboxes = reorder_multi_column_bboxes(pdf_parser, bboxes)

        # Plain text only keeps extracted text lines.
        elif parse_method.lower() == "plain_text":
            pdf_parser = PlainParser()
            lines, _ = pdf_parser(blob)
            bboxes = [{"text": t, "layout_type": "text"} for t, _ in lines]

        # MinerU/PaddleOCR/Docling/TCADP all return line-like sections that need
        # to be converted into the shared bbox-like structure used below.
        elif parse_method.lower() == "mineru":

            def resolve_mineru_llm_name():
                configured = parser_model_name or conf.get("mineru_llm_name")
                if configured:
                    return configured

                tenant_id = self._canvas._tenant_id
                if not tenant_id:
                    return None

                from api.db.services.tenant_llm_service import TenantLLMService

                env_name = TenantLLMService.ensure_mineru_from_env(tenant_id)
                candidates = TenantLLMService.query(tenant_id=tenant_id, llm_factory="MinerU", model_type=LLMType.OCR.value)
                if candidates:
                    return candidates[0].llm_name
                return env_name

            parser_model_name = resolve_mineru_llm_name()
            if not parser_model_name:
                raise RuntimeError("MinerU model not configured. Please add MinerU in Model Providers or set MINERU_* env.")

            tenant_id = self._canvas._tenant_id
            ocr_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.OCR, parser_model_name)
            ocr_model = LLMBundle(tenant_id, ocr_model_config, lang=conf.get("lang", "Chinese"))
            pdf_parser = ocr_model.mdl

            lines, _ = pdf_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                parse_method="pipeline",
                lang=conf.get("lang", "Chinese"),
            )
            bboxes = []
            for line in lines or []:
                if not isinstance(line, tuple) or len(line) < 3:
                    continue

                t, layout_type, poss = line[0], line[1], line[2]
                box = {
                    "text": t,
                    "layout_type": layout_type or "text",
                }
                positions = [[pos[0][-1] + 1, *pos[1:]] for pos in pdf_parser.extract_positions(poss)]
                if positions:
                    box["positions"] = positions
                image = pdf_parser.crop(poss, 1)
                if image is not None:
                    box["image"] = image
                bboxes.append(box)

        elif parse_method.lower() == "docling":
            pdf_parser = DoclingParser(docling_server_url=os.environ.get("DOCLING_SERVER_URL", ""))
            lines, _ = pdf_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                parse_method="pipeline",
                docling_server_url=os.environ.get("DOCLING_SERVER_URL", ""),
            )
            bboxes = []
            for item in lines or []:
                if not isinstance(item, tuple) or len(item) < 3:
                    continue
                text, layout_type, poss = item[0], item[1], item[2]
                box = {
                    "text": text,
                    "layout_type": layout_type or "text",
                }
                if isinstance(poss, str) and poss:
                    positions = [[pos[0][-1] + 1, *pos[1:]] for pos in pdf_parser.extract_positions(poss)]
                    if positions:
                        box["positions"] = positions
                    image = pdf_parser.crop(poss, 1)
                    if image is not None:
                        box["image"] = image
                bboxes.append(box)

        elif parse_method.lower() == "tcadp parser":
            # ADP is a document parsing tool using Tencent Cloud API
            table_result_type = conf.get("table_result_type", "1")
            markdown_image_response_type = conf.get("markdown_image_response_type", "1")
            pdf_parser = TCADPParser(
                table_result_type=table_result_type,
                markdown_image_response_type=markdown_image_response_type,
            )
            sections, _ = pdf_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                file_type="PDF",
                file_start_page=1,
                file_end_page=1000,
            )
            bboxes = []
            for section, position_tag in sections:
                if position_tag:
                    match = re.match(r"@@([0-9-]+)\t([0-9.]+)\t([0-9.]+)\t([0-9.]+)\t([0-9.]+)##", position_tag)
                    if match:
                        pn, x0, x1, top, bott = match.groups()
                        bboxes.append(
                            {
                                "page_number": int(pn.split("-")[0]),
                                "x0": float(x0),
                                "x1": float(x1),
                                "top": float(top),
                                "bottom": float(bott),
                                "text": section,
                                "layout_type": "text",
                            }
                        )
                    else:
                        bboxes.append({"text": section, "layout_type": "text"})
                else:
                    bboxes.append({"text": section, "layout_type": "text"})

        elif parse_method.lower() == "paddleocr":

            def resolve_paddleocr_llm_name():
                configured = parser_model_name or conf.get("paddleocr_llm_name")
                if configured:
                    return configured

                tenant_id = self._canvas._tenant_id
                if not tenant_id:
                    return None

                from api.db.services.tenant_llm_service import TenantLLMService

                env_name = TenantLLMService.ensure_paddleocr_from_env(tenant_id)
                candidates = TenantLLMService.query(tenant_id=tenant_id, llm_factory="PaddleOCR", model_type=LLMType.OCR.value)
                if candidates:
                    return candidates[0].llm_name
                return env_name

            parser_model_name = resolve_paddleocr_llm_name()
            if not parser_model_name:
                raise RuntimeError("PaddleOCR model not configured. Please add PaddleOCR in Model Providers or set PADDLEOCR_* env.")

            tenant_id = self._canvas._tenant_id
            ocr_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.OCR, parser_model_name)
            ocr_model = LLMBundle(tenant_id, ocr_model_config)
            pdf_parser = ocr_model.mdl

            lines, _ = pdf_parser.parse_pdf(
                filepath=name,
                binary=blob,
                callback=self.callback,
                parse_method="pipeline",
            )
            bboxes = []
            for line in lines or []:
                if not isinstance(line, tuple) or len(line) < 3:
                    continue

                t, layout_type, poss = line[0], line[1], line[2]
                box = {
                    "text": t,
                    "layout_type": layout_type or "text",
                }
                positions = [[pos[0][-1] + 1, *pos[1:]] for pos in pdf_parser.extract_positions(poss)]
                if positions:
                    box["positions"] = positions
                image = pdf_parser.crop(poss)
                if image is not None:
                    box["image"] = image
                bboxes.append(box)

        # Vision parser treats each page as a large image block.
        else:
            if conf.get("parse_method"):
                vision_model_config = get_model_config_by_type_and_name(self._canvas._tenant_id, LLMType.IMAGE2TEXT, conf["parse_method"])
            else:
                vision_model_config = get_tenant_default_model_by_type(self._canvas._tenant_id, LLMType.IMAGE2TEXT)
            vision_model = LLMBundle(self._canvas._tenant_id, vision_model_config, lang=self._param.setups["pdf"].get("lang"))
            pdf_parser = VisionParser(vision_model=vision_model)
            lines, _ = pdf_parser(blob, callback=self.callback)
            bboxes = []
            for t, poss in lines:
                for pn, x0, x1, top, bott in RAGFlowPdfParser.extract_positions(poss):
                    bboxes.append(
                        {
                            "page_number": int(pn[0]) + 1,
                            "x0": float(x0),
                            "x1": float(x1),
                            "top": float(top),
                            "bottom": float(bott),
                            "text": t,
                            "layout_type": "text",
                        }
                    )

        # Persist outlines and optionally remove TOC before normalizing metadata.
        self.set_output("file", {**kwargs.get("file", {}), "outlines": pdf_parser.outlines})
        if conf.get("remove_toc"):
            if not pdf_parser.outlines:
                bboxes, _ = remove_toc(bboxes)
            elif pdf_parser.outlines[0][2] == 1:
                bboxes = remove_toc_pdf(bboxes, pdf_parser.outlines)
            else:
                first_outline_page = pdf_parser.outlines[0][2]
                split_at = len(bboxes)
                for i, item in enumerate(bboxes):
                    if item["page_number"] >= first_outline_page:
                        split_at = i
                        break
                toc_bboxes, _ = remove_toc(bboxes[:split_at])
                bboxes = toc_bboxes + bboxes[split_at:]

        # Normalize shared bbox fields for downstream consumers.
        layout_counters = {}
        for b in bboxes:
            raw_layout = str(b.get("layout_type") or "").strip()
            has_layout = bool(raw_layout)
            layout = re.sub(r"\s+", " ", raw_layout) if has_layout else "text"
            b["layout_type"] = layout

            if not b.get("layoutno"):
                seq = layout_counters.get(layout, 0)
                layout_counters[layout] = seq + 1
                b["layoutno"] = f"{layout}-{seq}"

            if flatten_media_to_text:
                b["doc_type_kwd"] = "text"
            elif layout == "table":
                b["doc_type_kwd"] = "table"
            elif layout == "figure":
                b["doc_type_kwd"] = "image"
            elif not has_layout and b.get("image") is not None:
                b["doc_type_kwd"] = "image"
            else:
                b["doc_type_kwd"] = "text"

        # Mark likely author blocks near the title when enabled.
        if author_enabled:
            def _begin(txt):
                if not isinstance(txt, str):
                    return False
                return re.match(
                    r"[0-9. 一、i]*(introduction|abstract|摘要|引言|keywords|key words|关键词|background|背景|目录|前言|contents)",
                    txt.lower().strip(),
                )

            i = 0
            while i < min(32, len(bboxes) - 1):
                b = bboxes[i]
                i += 1
                layout_type = b.get("layout_type", "")
                layoutno = b.get("layoutno", "")
                is_title = "title" in str(layout_type).lower() or "title" in str(layoutno).lower()
                if not is_title:
                    continue

                title_txt = b.get("text", "")
                if _begin(title_txt):
                    break

                for j in range(3):
                    next_idx = i + j
                    if next_idx >= len(bboxes):
                        break
                    candidate = bboxes[next_idx].get("text", "")
                    if _begin(candidate):
                        break
                    if isinstance(candidate, str) and "@" in candidate:
                        break
                    bboxes[next_idx]["author"] = True
                break

        # Mark the abstract block when enabled.
        if abstract_enabled:
            i = 0
            abstract_idx = None
            while i + 1 < min(32, len(bboxes)):
                b = bboxes[i]
                i += 1
                txt = b.get("text", "")
                if not isinstance(txt, str):
                    continue
                txt = txt.lower().strip()
                if re.match(r"(abstract|摘要)", txt):
                    if len(txt.split()) > 32 or len(txt) > 64:
                        abstract_idx = i - 1
                        break
                    next_txt = bboxes[i].get("text", "") if i < len(bboxes) else ""
                    if isinstance(next_txt, str):
                        next_txt = next_txt.lower().strip()
                        if len(next_txt.split()) > 32 or len(next_txt) > 64:
                            abstract_idx = i
                    i += 1
                    break
            if abstract_idx is not None:
                bboxes[abstract_idx]["abstract"] = True

        enhance_media_sections_with_vision(
            bboxes,
            self._canvas._tenant_id,
            conf.get("vlm"),
            callback=self.callback,
        )

        # Emit the requested final PDF output format.
        if conf.get("output_format") == "json":
            normalize_pdf_items_metadata(bboxes)
            self.set_output("json", bboxes)
        if conf.get("output_format") == "markdown":
            mkdn = ""
            for b in bboxes:
                if b.get("layout_type", "") == "title":
                    mkdn += "\n## "
                if b.get("layout_type", "") == "figure":
                    mkdn += "\n![Image]({})".format(VLM.image2base64(b["image"]))
                    continue
                mkdn += b.get("text", "") + "\n"
            self.set_output("markdown", mkdn)