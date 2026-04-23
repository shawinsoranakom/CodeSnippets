def __call__(self, data):
        # prepare data
        entities = data.pop("entities")
        relations = data.pop("relations")
        encoded_inputs_all = []
        for index in range(0, len(data["input_ids"]), self.max_seq_len):
            item = {}
            for key in data:
                if key in [
                    "label",
                    "input_ids",
                    "labels",
                    "token_type_ids",
                    "bbox",
                    "attention_mask",
                ]:
                    if self.infer_mode and key == "labels":
                        item[key] = data[key]
                    else:
                        item[key] = data[key][index : index + self.max_seq_len]
                else:
                    item[key] = data[key]
            # select entity in current chunk
            entities_in_this_span = []
            global_to_local_map = {}  #
            for entity_id, entity in enumerate(entities):
                if (
                    index <= entity["start"] < index + self.max_seq_len
                    and index <= entity["end"] < index + self.max_seq_len
                ):
                    entity["start"] = entity["start"] - index
                    entity["end"] = entity["end"] - index
                    global_to_local_map[entity_id] = len(entities_in_this_span)
                    entities_in_this_span.append(entity)

            # select relations in current chunk
            relations_in_this_span = []
            for relation in relations:
                if (
                    index <= relation["start_index"] < index + self.max_seq_len
                    and index <= relation["end_index"] < index + self.max_seq_len
                ):
                    relations_in_this_span.append(
                        {
                            "head": global_to_local_map[relation["head"]],
                            "tail": global_to_local_map[relation["tail"]],
                            "start_index": relation["start_index"] - index,
                            "end_index": relation["end_index"] - index,
                        }
                    )
            item.update(
                {
                    "entities": self.reformat(entities_in_this_span),
                    "relations": self.reformat(relations_in_this_span),
                }
            )
            if len(item["entities"]) > 0:
                item["entities"]["label"] = [
                    self.entities_labels[x] for x in item["entities"]["label"]
                ]
                encoded_inputs_all.append(item)
        if len(encoded_inputs_all) == 0:
            return None
        return encoded_inputs_all[0]