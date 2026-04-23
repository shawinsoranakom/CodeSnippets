def preprocess(
        self,
        input,
        padding="do_not_pad",
        doc_stride=None,
        max_seq_len=None,
        word_boxes: tuple[str, list[float]] | None = None,
        lang=None,
        tesseract_config="",
        timeout=None,
    ):
        # NOTE: This code mirrors the code in question answering and will be implemented in a follow up PR
        # to support documents with enough tokens that overflow the model's window
        if max_seq_len is None:
            max_seq_len = self.tokenizer.model_max_length

        if doc_stride is None:
            doc_stride = min(max_seq_len // 2, 256)

        image = None
        image_features = {}
        if input.get("image", None) is not None:
            image = load_image(input["image"], timeout=timeout)
            if self.image_processor is not None:
                image_inputs = self.image_processor(images=image, return_tensors="pt")
                image_inputs = image_inputs.to(self.dtype)
                image_features.update(image_inputs)
            elif self.feature_extractor is not None:
                image_features.update(self.feature_extractor(images=image, return_tensors="pt"))
            elif self.model_type == ModelType.VisionEncoderDecoder:
                raise ValueError("If you are using a VisionEncoderDecoderModel, you must provide a feature extractor")

        words, boxes = None, None
        if self.model_type != ModelType.VisionEncoderDecoder:
            if "word_boxes" in input:
                words = [x[0] for x in input["word_boxes"]]
                boxes = [x[1] for x in input["word_boxes"]]
            elif "words" in image_features and "boxes" in image_features:
                words = image_features.pop("words")[0]
                boxes = image_features.pop("boxes")[0]
            elif image is not None:
                if not TESSERACT_LOADED:
                    raise ValueError(
                        "If you provide an image without word_boxes, then the pipeline will run OCR using Tesseract,"
                        " but pytesseract is not available"
                    )
                if TESSERACT_LOADED:
                    words, boxes = apply_tesseract(image, lang=lang, tesseract_config=tesseract_config)
            else:
                raise ValueError(
                    "You must provide an image or word_boxes. If you provide an image, the pipeline will automatically"
                    " run OCR to derive words and boxes"
                )

        if self.tokenizer.padding_side != "right":
            raise ValueError(
                "Document question answering only supports tokenizers whose padding side is 'right', not"
                f" {self.tokenizer.padding_side}"
            )

        if self.model_type == ModelType.VisionEncoderDecoder:
            task_prompt = f"<s_docvqa><s_question>{input['question']}</s_question><s_answer>"
            # Adapted from https://huggingface.co/spaces/nielsr/donut-docvqa/blob/main/app.py
            encoding = {
                "inputs": image_features["pixel_values"],
                "decoder_input_ids": self.tokenizer(
                    task_prompt, add_special_tokens=False, return_tensors="pt"
                ).input_ids,
                "return_dict_in_generate": True,
            }
            yield {
                **encoding,
                "p_mask": None,
                "word_ids": None,
                "words": None,
                "output_attentions": True,
                "is_last": True,
            }
        else:
            tokenizer_kwargs = {}
            if self.model_type == ModelType.LayoutLM:
                tokenizer_kwargs["text"] = input["question"].split()
                tokenizer_kwargs["text_pair"] = words
                tokenizer_kwargs["is_split_into_words"] = True
            else:
                tokenizer_kwargs["text"] = [input["question"]]
                tokenizer_kwargs["text_pair"] = [words]
                tokenizer_kwargs["boxes"] = [boxes]

            encoding = self.tokenizer(
                padding=padding,
                max_length=max_seq_len,
                stride=doc_stride,
                return_token_type_ids=True,
                truncation="only_second",
                return_overflowing_tokens=True,
                **tokenizer_kwargs,
            )
            # TODO: check why slower `LayoutLMTokenizer` and `LayoutLMv2Tokenizer` don't have this key in outputs
            # FIXME: ydshieh and/or Narsil
            encoding.pop("overflow_to_sample_mapping", None)  # We do not use this

            num_spans = len(encoding["input_ids"])

            # p_mask: mask with 1 for token than cannot be in the answer (0 for token which can be in an answer)
            # We put 0 on the tokens from the context and 1 everywhere else (question and special tokens)
            # This logic mirrors the logic in the question_answering pipeline
            p_mask = [[tok != 1 for tok in encoding.sequence_ids(span_id)] for span_id in range(num_spans)]
            for span_idx in range(num_spans):
                span_encoding = {k: torch.tensor(v[span_idx : span_idx + 1]) for (k, v) in encoding.items()}
                if "pixel_values" in image_features:
                    span_encoding["image"] = image_features["pixel_values"]

                input_ids_span_idx = encoding["input_ids"][span_idx]
                # keep the cls_token unmasked (some models use it to indicate unanswerable questions)
                if self.tokenizer.cls_token_id is not None:
                    cls_indices = np.nonzero(np.array(input_ids_span_idx) == self.tokenizer.cls_token_id)[0]
                    for cls_index in cls_indices:
                        p_mask[span_idx][cls_index] = 0

                # For each span, place a bounding box [0,0,0,0] for question and CLS tokens, [1000,1000,1000,1000]
                # for SEP tokens, and the word's bounding box for words in the original document.
                if "boxes" not in tokenizer_kwargs:
                    bbox = []
                    for input_id, sequence_id, word_id in zip(
                        encoding.input_ids[span_idx],
                        encoding.sequence_ids(span_idx),
                        encoding.word_ids(span_idx),
                    ):
                        if sequence_id == 1:
                            bbox.append(boxes[word_id])
                        elif input_id == self.tokenizer.sep_token_id:
                            bbox.append([1000] * 4)
                        else:
                            bbox.append([0] * 4)

                    span_encoding["bbox"] = torch.tensor(bbox).unsqueeze(0)
                yield {
                    **span_encoding,
                    "p_mask": p_mask[span_idx],
                    "word_ids": encoding.word_ids(span_idx),
                    "words": words,
                    "is_last": span_idx == num_spans - 1,
                }