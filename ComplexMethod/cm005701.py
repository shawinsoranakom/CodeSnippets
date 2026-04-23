def visualize_attention_mask(self, input_sentence: str, suffix=""):
        model = self.model
        kwargs = {}
        image_seq_length = None
        if self.config.model_type in PROCESSOR_MAPPING_NAMES:
            img = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg?download=true"
            img = Image.open(io.BytesIO(httpx.get(img, follow_redirects=True).content))
            image_seq_length = 5
            processor = AutoProcessor.from_pretrained(self.repo_id, image_seq_length=image_seq_length)
            if hasattr(processor, "image_token"):
                image_token = processor.image_token
            else:
                image_token = processor.tokenizer.convert_ids_to_tokens([processor.image_token_id])[0]

            if image_token:
                input_sentence = input_sentence.replace("<img>", image_token)

            inputs = processor(images=img, text=input_sentence, suffix=suffix, return_tensors="pt")

            self.image_token = processor.tokenizer.convert_ids_to_tokens([processor.image_token_id])[0]

            attention_mask = inputs["attention_mask"]
            if "token_type_ids" in inputs:  # TODO inspect signature of update causal mask
                kwargs["token_type_ids"] = inputs["token_type_ids"]
            tokens = processor.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        else:
            tokenizer = AutoTokenizer.from_pretrained(self.repo_id)
            if tokenizer is None:
                raise ValueError(f"Could not load tokenizer for {self.repo_id}")
            tokens = tokenizer.tokenize(input_sentence)
            attention_mask = tokenizer(input_sentence, return_tensors="pt")["attention_mask"]
            if attention_mask is None:
                raise ValueError(f"Model type {self.config.model_type} does not support attention visualization")

        model.config._attn_implementation = "eager"
        model.train()

        batch_size, seq_length = attention_mask.shape
        inputs_embeds = torch.zeros((batch_size, seq_length, model.config.hidden_size), dtype=self.model.dtype)

        causal_mask = create_causal_mask(
            config=model.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=None,
        )

        if causal_mask is None:
            # attention_mask must be a tensor here
            attention_mask = attention_mask.unsqueeze(1).unsqueeze(1).expand(batch_size, 1, seq_length, seq_length)
        elif isinstance(causal_mask, torch.Tensor):
            attention_mask = ~causal_mask.to(dtype=torch.bool)
        else:
            attention_mask = ~causal_mask

        top_bottom_border = "##" * (
            len(f"Attention visualization for {self.config.model_type} | {self.mapped_cls}") + 4
        )  # Box width adjusted to text length
        side_border = "##"
        print(f"\n{top_bottom_border}")
        print(
            "##"
            + f"  Attention visualization for \033[1m{self.config.model_type}:{self.repo_id}\033[0m {self.mapped_cls.__name__}".center(
                len(top_bottom_border)
            )
            + "    "
            + side_border,
        )
        print(f"{top_bottom_border}")
        f_string = generate_attention_matrix_from_mask(
            tokens,
            attention_mask,
            img_token=self.image_token,
            sliding_window=getattr(self.config, "sliding_window", None),
            token_type_ids=kwargs.get("token_type_ids"),
            image_seq_length=image_seq_length,
        )
        print(f_string)
        print(f"{top_bottom_border}")