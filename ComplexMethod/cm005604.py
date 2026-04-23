def postprocess(self, all_outputs, aggregation_strategy=AggregationStrategy.NONE, ignore_labels=None):
        if ignore_labels is None:
            ignore_labels = ["O"]
        all_entities = []

        # Get map from the first output, it's the same for all chunks
        word_to_chars_map = all_outputs[0].get("word_to_chars_map")

        for model_outputs in all_outputs:
            if model_outputs["logits"][0].dtype in (torch.bfloat16, torch.float16):
                logits = model_outputs["logits"][0].to(torch.float32).numpy()
            else:
                logits = model_outputs["logits"][0].numpy()

            sentence = all_outputs[0]["sentence"]
            input_ids = model_outputs["input_ids"][0]
            offset_mapping = (
                model_outputs["offset_mapping"][0] if model_outputs["offset_mapping"] is not None else None
            )
            special_tokens_mask = model_outputs["special_tokens_mask"][0].numpy()
            word_ids = model_outputs.get("word_ids")

            maxes = np.max(logits, axis=-1, keepdims=True)
            shifted_exp = np.exp(logits - maxes)
            scores = shifted_exp / shifted_exp.sum(axis=-1, keepdims=True)

            pre_entities = self.gather_pre_entities(
                sentence,
                input_ids,
                scores,
                offset_mapping,
                special_tokens_mask,
                aggregation_strategy,
                word_ids=word_ids,
                word_to_chars_map=word_to_chars_map,
            )
            grouped_entities = self.aggregate(pre_entities, aggregation_strategy)
            # Filter anything that is in self.ignore_labels
            entities = [
                entity
                for entity in grouped_entities
                if entity.get("entity", None) not in ignore_labels
                and entity.get("entity_group", None) not in ignore_labels
            ]
            all_entities.extend(entities)
        num_chunks = len(all_outputs)
        if num_chunks > 1:
            all_entities = self.aggregate_overlapping_entities(all_entities)
        return all_entities