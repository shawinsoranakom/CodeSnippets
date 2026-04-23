def save_pretrained(self, save_directory, push_to_hub: bool = False, **kwargs):
        """
        Saves the attributes of this processor (feature extractor, tokenizer...) in the specified directory so that it
        can be reloaded using the [`~ProcessorMixin.from_pretrained`] method.

        <Tip>

        This class method is simply calling [`~feature_extraction_utils.FeatureExtractionMixin.save_pretrained`] and
        [`~tokenization_utils_base.PreTrainedTokenizerBase.save_pretrained`]. Please refer to the docstrings of the
        methods above for more information.

        </Tip>

        Args:
            save_directory (`str` or `os.PathLike`):
                Directory where the feature extractor JSON file and the tokenizer files will be saved (directory will
                be created if it does not exist).
            push_to_hub (`bool`, *optional*, defaults to `False`):
                Whether or not to push your model to the Hugging Face model hub after saving it. You can specify the
                repository you want to push to with `repo_id` (will default to the name of `save_directory` in your
                namespace).
            kwargs (`dict[str, Any]`, *optional*):
                Additional key word arguments passed along to the [`~utils.PushToHubMixin.push_to_hub`] method.
        """
        os.makedirs(save_directory, exist_ok=True)

        if push_to_hub:
            commit_message = kwargs.pop("commit_message", None)
            repo_id = kwargs.pop("repo_id", save_directory.split(os.path.sep)[-1])
            repo_id = create_repo(repo_id, exist_ok=True, **kwargs).repo_id
            files_timestamps = self._get_files_timestamps(save_directory)
        # If we have a custom config, we copy the file defining it in the folder and set the attributes so it can be
        # loaded from the Hub.
        if self._auto_class is not None:
            attrs = [getattr(self, attribute_name) for attribute_name in self.get_attributes()]
            configs = [(a.init_kwargs if isinstance(a, PreTrainedTokenizerBase) else a) for a in attrs]
            configs.append(self)
            custom_object_save(self, save_directory, config=configs)

        for attribute_name in self.get_attributes():
            attribute = getattr(self, attribute_name)

            modality = _get_modality_for_attribute(attribute_name)
            is_primary = attribute_name == modality
            if modality == "tokenizer":
                attribute._set_processor_class(self.__class__.__name__)
                # Save the tokenizer in its own vocab file. The other attributes are saved as part of `processor_config.json`
                if is_primary:
                    attribute.save_pretrained(save_directory)
                else:
                    # if a model has multiple tokenizers, save the additional tokenizers in their own folders.
                    attribute.save_pretrained(os.path.join(save_directory, attribute_name))
            elif attribute._auto_class is not None:
                custom_object_save(attribute, save_directory, config=attribute)

        if self._auto_class is not None:
            # We added an attribute to the init_kwargs of the tokenizers, which needs to be cleaned up.
            for attribute_name in self.get_attributes():
                attribute = getattr(self, attribute_name)
                if isinstance(attribute, PreTrainedTokenizerBase):
                    del attribute.init_kwargs["auto_map"]

        # If we save using the predefined names, we can load using `from_pretrained`
        # plus we save chat_template in its own file
        output_processor_file = os.path.join(save_directory, PROCESSOR_NAME)
        output_chat_template_file_jinja = os.path.join(save_directory, CHAT_TEMPLATE_FILE)
        chat_template_dir = os.path.join(save_directory, CHAT_TEMPLATE_DIR)

        # Save `chat_template` in its own file. We can't get it from `processor_dict` as we popped it in `to_dict`
        # to avoid serializing chat template in json config file. So let's get it from `self` directly
        if isinstance(self.chat_template, str):
            # New format for single templates is to save them as chat_template.jinja
            with open(output_chat_template_file_jinja, "w", encoding="utf-8") as f:
                f.write(self.chat_template)
            logger.info(f"chat template saved in {output_chat_template_file_jinja}")
        elif isinstance(self.chat_template, dict):
            # New format for multiple templates is to save the default as chat_template.jinja
            # and the other templates in the chat_templates/ directory
            for template_name, template in self.chat_template.items():
                if template_name == "default":
                    with open(output_chat_template_file_jinja, "w", encoding="utf-8") as f:
                        f.write(self.chat_template["default"])
                    logger.info(f"chat template saved in {output_chat_template_file_jinja}")
                else:
                    os.makedirs(chat_template_dir, exist_ok=True)
                    template_filepath = os.path.join(chat_template_dir, f"{template_name}.jinja")
                    with open(template_filepath, "w", encoding="utf-8") as f:
                        f.write(template)
                    logger.info(f"chat template saved in {template_filepath}")

        # Create a unified `preprocessor_config.json` and save all attributes as a composite config, except for tokenizers
        self.to_json_file(output_processor_file)
        logger.info(f"processor saved in {output_processor_file}")
        return_files = [output_processor_file]

        if push_to_hub:
            self._upload_modified_files(
                save_directory,
                repo_id,
                files_timestamps,
                commit_message=commit_message,
                token=kwargs.get("token"),
            )

        return return_files