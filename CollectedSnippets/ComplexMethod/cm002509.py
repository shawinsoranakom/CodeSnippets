def create_model_card(
        self,
        language: str | None = None,
        license: str | None = None,
        tags: str | list[str] | None = None,
        model_name: str | None = None,
        finetuned_from: str | None = None,
        tasks: str | list[str] | None = None,
        dataset_tags: str | list[str] | None = None,
        dataset: str | list[str] | None = None,
        dataset_args: str | list[str] | None = None,
    ) -> None:
        """
        Creates a draft of a model card using the information available to the `Trainer`.

        Args:
            language (`str`, *optional*):
                The language of the model (if applicable)
            license (`str`, *optional*):
                The license of the model. Will default to the license of the pretrained model used, if the original
                model given to the `Trainer` comes from a repo on the Hub.
            tags (`str` or `list[str]`, *optional*):
                Some tags to be included in the metadata of the model card.
            model_name (`str`, *optional*):
                The name of the model.
            finetuned_from (`str`, *optional*):
                The name of the model used to fine-tune this one (if applicable). Will default to the name of the repo
                of the original model given to the `Trainer` (if it comes from the Hub).
            tasks (`str` or `list[str]`, *optional*):
                One or several task identifiers, to be included in the metadata of the model card.
            dataset_tags (`str` or `list[str]`, *optional*):
                One or several dataset tags, to be included in the metadata of the model card.
            dataset (`str` or `list[str]`, *optional*):
                One or several dataset identifiers, to be included in the metadata of the model card.
            dataset_args (`str` or `list[str]`, *optional*):
               One or several dataset arguments, to be included in the metadata of the model card.
        """
        if not self.is_world_process_zero():
            return

        model_card_filepath = os.path.join(self.args.output_dir, "README.md")
        is_peft_library = False
        if os.path.exists(model_card_filepath):
            library_name = ModelCard.load(model_card_filepath).data.get("library_name")
            is_peft_library = library_name == "peft"

            # Append existing tags in `tags`
            existing_tags = ModelCard.load(model_card_filepath).data.tags
            if tags is not None and existing_tags is not None:
                if isinstance(tags, str):
                    tags = [tags]
                for tag in existing_tags:
                    if tag not in tags:
                        tags.append(tag)

        training_summary = TrainingSummary.from_trainer(
            self,
            language=language,
            license=license,
            tags=tags,
            model_name=model_name,
            finetuned_from=finetuned_from,
            tasks=tasks,
            dataset_tags=dataset_tags,
            dataset=dataset,
            dataset_args=dataset_args,
        )
        model_card = training_summary.to_model_card()
        with open(model_card_filepath, "w") as f:
            f.write(model_card)

        if is_peft_library:
            self.accelerator.unwrap_model(self.model).create_or_update_model_card(self.args.output_dir)