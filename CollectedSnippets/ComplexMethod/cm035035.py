def __call__(self, data):
        # load bbox and label info
        ocr_info = self._load_ocr_info(data)

        for idx in range(len(ocr_info)):
            if "bbox" not in ocr_info[idx]:
                ocr_info[idx]["bbox"] = self.trans_poly_to_bbox(ocr_info[idx]["points"])

        if self.order_method == "tb-yx":
            ocr_info = order_by_tbyx(ocr_info)

        # for re
        train_re = self.contains_re and not self.infer_mode
        if train_re:
            ocr_info = self.filter_empty_contents(ocr_info)

        height, width, _ = data["image"].shape

        words_list = []
        bbox_list = []
        input_ids_list = []
        token_type_ids_list = []
        segment_offset_id = []
        gt_label_list = []

        entities = []

        if train_re:
            relations = []
            id2label = {}
            entity_id_to_index_map = {}
            empty_entity = set()

        data["ocr_info"] = copy.deepcopy(ocr_info)

        for info in ocr_info:
            text = info["transcription"]
            if len(text) <= 0:
                continue
            if train_re:
                # for re
                if len(text) == 0:
                    empty_entity.add(info["id"])
                    continue
                id2label[info["id"]] = info["label"]
                relations.extend([tuple(sorted(l)) for l in info["linking"]])
            # smooth_box
            info["bbox"] = self.trans_poly_to_bbox(info["points"])

            encode_res = self.tokenizer.encode(
                text,
                pad_to_max_seq_len=False,
                return_attention_mask=True,
                return_token_type_ids=True,
            )

            if not self.add_special_ids:
                # TODO: use tok.all_special_ids to remove
                encode_res["input_ids"] = encode_res["input_ids"][1:-1]
                encode_res["token_type_ids"] = encode_res["token_type_ids"][1:-1]
                encode_res["attention_mask"] = encode_res["attention_mask"][1:-1]

            if self.use_textline_bbox_info:
                bbox = [info["bbox"]] * len(encode_res["input_ids"])
            else:
                bbox = self.split_bbox(
                    info["bbox"], info["transcription"], self.tokenizer
                )
            if len(bbox) <= 0:
                continue
            bbox = self._smooth_box(bbox, height, width)
            if self.add_special_ids:
                bbox.insert(0, [0, 0, 0, 0])
                bbox.append([0, 0, 0, 0])

            # parse label
            if not self.infer_mode:
                label = info["label"]
                gt_label = self._parse_label(label, encode_res)

            # construct entities for re
            if train_re:
                if gt_label[0] != self.label2id_map["O"]:
                    entity_id_to_index_map[info["id"]] = len(entities)
                    label = label.upper()
                    entities.append(
                        {
                            "start": len(input_ids_list),
                            "end": len(input_ids_list) + len(encode_res["input_ids"]),
                            "label": label.upper(),
                        }
                    )
            else:
                entities.append(
                    {
                        "start": len(input_ids_list),
                        "end": len(input_ids_list) + len(encode_res["input_ids"]),
                        "label": "O",
                    }
                )
            input_ids_list.extend(encode_res["input_ids"])
            token_type_ids_list.extend(encode_res["token_type_ids"])
            bbox_list.extend(bbox)
            words_list.append(text)
            segment_offset_id.append(len(input_ids_list))
            if not self.infer_mode:
                gt_label_list.extend(gt_label)

        data["input_ids"] = input_ids_list
        data["token_type_ids"] = token_type_ids_list
        data["bbox"] = bbox_list
        data["attention_mask"] = [1] * len(input_ids_list)
        data["labels"] = gt_label_list
        data["segment_offset_id"] = segment_offset_id
        data["tokenizer_params"] = dict(
            padding_side=self.tokenizer.padding_side,
            pad_token_type_id=self.tokenizer.pad_token_type_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        data["entities"] = entities

        if train_re:
            data["relations"] = relations
            data["id2label"] = id2label
            data["empty_entity"] = empty_entity
            data["entity_id_to_index_map"] = entity_id_to_index_map
        return data