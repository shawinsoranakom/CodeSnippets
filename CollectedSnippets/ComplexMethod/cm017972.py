def get_shape_content(shape, **kwargs):
                nonlocal md_content

                # Pictures
                if self._is_picture(shape):
                    # Get image data
                    image_stream = io.BytesIO(shape.image.blob)

                    # Try LLM description first if available
                    llm_description = ""
                    if llm_client and kwargs.get("llm_model"):
                        try:
                            from ._llm_caption import llm_caption

                            image_filename = shape.image.filename
                            image_extension = None
                            if image_filename:
                                import os

                                image_extension = os.path.splitext(image_filename)[1]

                            image_stream_info = StreamInfo(
                                mimetype=shape.image.content_type,
                                extension=image_extension,
                                filename=image_filename,
                            )

                            llm_description = llm_caption(
                                image_stream,
                                image_stream_info,
                                client=llm_client,
                                model=kwargs.get("llm_model"),
                                prompt=kwargs.get("llm_prompt"),
                            )
                        except Exception:
                            pass

                    # Try OCR if LLM failed or not available
                    ocr_text = ""
                    if not llm_description and ocr_service:
                        try:
                            image_stream.seek(0)
                            ocr_result = ocr_service.extract_text(image_stream)
                            if ocr_result.text.strip():
                                ocr_text = ocr_result.text.strip()
                        except Exception:
                            pass

                    # Format extracted content using unified OCR block format
                    content = (llm_description or ocr_text or "").strip()
                    if content:
                        md_content += f"\n*[Image OCR]\n{content}\n[End OCR]*\n"

                # Tables
                if self._is_table(shape):
                    md_content += self._convert_table_to_markdown(shape.table, **kwargs)

                # Charts
                if shape.has_chart:
                    md_content += self._convert_chart_to_markdown(shape.chart)

                # Text areas
                elif shape.has_text_frame:
                    if shape == title:
                        md_content += "# " + shape.text.lstrip() + "\\n"
                    else:
                        md_content += shape.text + "\\n"

                # Group Shapes
                if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.GROUP:
                    sorted_shapes = sorted(
                        shape.shapes,
                        key=lambda x: (
                            float("-inf") if not x.top else x.top,
                            float("-inf") if not x.left else x.left,
                        ),
                    )
                    for subshape in sorted_shapes:
                        get_shape_content(subshape, **kwargs)