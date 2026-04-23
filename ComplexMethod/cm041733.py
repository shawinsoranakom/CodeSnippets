def preprocess_dataset(self, examples: dict[str, list[Any]]) -> dict[str, list[Any]]:
        # Creates mismatched pairs of prompts and completions for the KL dataset by adding a +1 offset to the order of completions.
        kl_response = [examples["_response"][-1]] + examples["_response"][:-1]
        model_inputs = defaultdict(list)
        for i in range(len(examples["_prompt"])):
            if len(examples["_prompt"][i]) % 2 != 1 or len(examples["_response"][i]) < 2:
                logger.warning_rank0(
                    "Dropped invalid example: {}".format(examples["_prompt"][i] + examples["_response"][i])
                )
                continue

            input_ids, labels, kl_input_ids, kl_labels, kto_tag = self._encode_data_example(
                prompt=examples["_prompt"][i],
                response=examples["_response"][i],
                kl_response=kl_response[i],
                system=examples["_system"][i],
                tools=examples["_tools"][i],
                images=examples["_images"][i] or [],
                videos=examples["_videos"][i] or [],
                audios=examples["_audios"][i] or [],
            )
            model_inputs["input_ids"].append(input_ids)
            model_inputs["attention_mask"].append([1] * len(input_ids))
            model_inputs["labels"].append(labels)
            model_inputs["kl_input_ids"].append(kl_input_ids)
            model_inputs["kl_attention_mask"].append([1] * len(kl_input_ids))
            model_inputs["kl_labels"].append(kl_labels)
            model_inputs["kto_tags"].append(kto_tag)
            model_inputs["images"].append(examples["_images"][i])
            model_inputs["videos"].append(examples["_videos"][i])
            model_inputs["audios"].append(examples["_audios"][i])

        desirable_num = sum([1 for tag in model_inputs["kto_tags"] if tag])
        undesirable_num = len(model_inputs["kto_tags"]) - desirable_num
        if desirable_num == 0 or undesirable_num == 0:
            logger.warning_rank0("Your dataset only has one preference type.")

        return model_inputs