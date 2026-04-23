def __classify_visual_blocks(self):
        if not self.page_blocks:
            return

        ordered_blocks = sorted(self.page_blocks, key=lambda x: x["index"])
        original_type_by_index = {
            block["index"]: block["type"] for block in ordered_blocks
        }
        position_by_index = {
            block["index"]: pos for pos, block in enumerate(ordered_blocks)
        }
        main_blocks = [
            block
            for block in ordered_blocks
            if original_type_by_index[block["index"]] in self.VISUAL_MAIN_TYPES
        ]
        child_blocks = [
            block
            for block in ordered_blocks
            if original_type_by_index[block["index"]] in self.VISUAL_CHILD_TYPES
        ]

        child_parent_map = {}
        grouped_children = {
            main_block["index"]: {"captions": [], "footnotes": []}
            for main_block in main_blocks
        }

        for child_block in child_blocks:
            parent_block = self.__find_best_visual_parent(
                child_block,
                main_blocks,
                ordered_blocks,
                original_type_by_index,
                position_by_index,
            )
            child_parent_map[child_block["index"]] = (
                None if parent_block is None else parent_block["index"]
            )

        for child_block in child_blocks:
            original_child_type = original_type_by_index[child_block["index"]]
            parent_index = child_parent_map[child_block["index"]]

            if parent_index is None:
                child_block["type"] = BlockType.TEXT
                self.__sync_layout_det_type(child_block["index"], BlockType.TEXT)
                continue

            parent_type = original_type_by_index[parent_index]
            child_kind = self.__child_kind(original_child_type)
            mapped_type = self.VISUAL_TYPE_MAPPING[parent_type][child_kind]
            child_block["type"] = mapped_type
            self.__sync_layout_det_type(child_block["index"], mapped_type)
            grouped_children[parent_index][f"{child_kind}s"].append(child_block)

        self.image_groups = []
        self.table_groups = []
        self.chart_groups = []

        rebuilt_page_blocks = []
        for block in ordered_blocks:
            original_block_type = original_type_by_index[block["index"]]

            if original_block_type in self.VISUAL_CHILD_TYPES:
                if child_parent_map[block["index"]] is None:
                    rebuilt_page_blocks.append(block)
                continue

            if original_block_type not in self.VISUAL_MAIN_TYPES:
                rebuilt_page_blocks.append(block)
                continue

            mapping = self.VISUAL_TYPE_MAPPING[original_block_type]
            body_block = self.__make_child_block(block, mapping["body"])
            captions = sorted(
                [
                    self.__make_child_block(caption, mapping["caption"])
                    for caption in grouped_children[block["index"]]["captions"]
                ],
                key=lambda x: x["index"],
            )
            footnotes = sorted(
                [
                    self.__make_child_block(footnote, mapping["footnote"])
                    for footnote in grouped_children[block["index"]]["footnotes"]
                ],
                key=lambda x: x["index"],
            )

            self.__sync_layout_det_type(block["index"], mapping["body"])

            group_info = {
                f"{original_block_type}_body": body_block,
                f"{original_block_type}_caption_list": captions,
                f"{original_block_type}_footnote_list": footnotes,
            }
            if original_block_type == BlockType.IMAGE:
                self.image_groups.append(group_info)
            elif original_block_type == BlockType.TABLE:
                self.table_groups.append(group_info)
            else:
                self.chart_groups.append(group_info)

            two_layer_block = {
                "type": original_block_type,
                "bbox": block["bbox"],
                "blocks": [body_block, *captions, *footnotes],
                "index": block["index"],
                "score": block.get("score"),
            }
            # 对blocks按index排序
            two_layer_block["blocks"].sort(key=lambda x: x["index"])
            rebuilt_page_blocks.append(two_layer_block)

        self.page_blocks = rebuilt_page_blocks