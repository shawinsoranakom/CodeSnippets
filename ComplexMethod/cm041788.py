def wrapper(features: Sequence[dict[str, Any]]):
        labels_key = [k for k in features[0].keys() if k.endswith("labels")]
        input_ids_key = [k for k in features[0].keys() if k.endswith("input_ids")]
        for feature in features:
            if len(labels_key) == 0:  # pt
                feature["labels"] = deepcopy(feature["input_ids"])[1:]
            for k in labels_key:
                feature[k] = feature[k][1:]
            for k in input_ids_key:
                feature[k] = feature[k][:-1]
            for k in ["attention_mask", "position_ids"]:
                if k in feature:
                    feature[k] = feature[k][:-1]

        # for qwen vl series model
        tmp_features = data_collator(features)
        tmp_features.pop("rope_deltas", None)
        position_ids = tmp_features.get("position_ids", None)

        if position_ids is not None and position_ids.dim() == 3:
            if position_ids.shape[0] == 4:
                position_ids = position_ids[1:]
            tmp_features["position_ids"] = position_ids

        return tmp_features