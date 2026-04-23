def save_chat_templates(
        self,
        save_directory: str | os.PathLike,
        tokenizer_config: dict,
        filename_prefix: str | None,
        save_jinja_files: bool,
    ):
        """
        Writes chat templates out to the save directory if we're using the new format, and removes them from
        the tokenizer config if present. If we're using the legacy format, it doesn't write any files, and instead
        writes the templates to the tokenizer config in the correct format.
        """
        chat_template_file = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + CHAT_TEMPLATE_FILE
        )
        chat_template_dir = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + CHAT_TEMPLATE_DIR
        )

        saved_raw_chat_template_files = []
        if save_jinja_files and isinstance(self.chat_template, str):
            # New format for single templates is to save them as chat_template.jinja
            with open(chat_template_file, "w", encoding="utf-8") as f:
                f.write(self.chat_template)
            logger.info(f"chat template saved in {chat_template_file}")
            saved_raw_chat_template_files.append(chat_template_file)
            if "chat_template" in tokenizer_config:
                tokenizer_config.pop("chat_template")  # To ensure it doesn't somehow end up in the config too
        elif save_jinja_files and isinstance(self.chat_template, dict):
            # New format for multiple templates is to save the default as chat_template.jinja
            # and the other templates in the chat_templates/ directory
            for template_name, template in self.chat_template.items():
                if template_name == "default":
                    with open(chat_template_file, "w", encoding="utf-8") as f:
                        f.write(self.chat_template["default"])
                    logger.info(f"chat template saved in {chat_template_file}")
                    saved_raw_chat_template_files.append(chat_template_file)
                else:
                    Path(chat_template_dir).mkdir(exist_ok=True)
                    template_filepath = os.path.join(chat_template_dir, f"{template_name}.jinja")
                    with open(template_filepath, "w", encoding="utf-8") as f:
                        f.write(template)
                    logger.info(f"chat template saved in {template_filepath}")
                    saved_raw_chat_template_files.append(template_filepath)
            if "chat_template" in tokenizer_config:
                tokenizer_config.pop("chat_template")  # To ensure it doesn't somehow end up in the config too
        elif isinstance(self.chat_template, dict):
            # Legacy format for multiple templates:
            # chat template dicts are saved to the config as lists of dicts with fixed key names.
            tokenizer_config["chat_template"] = [{"name": k, "template": v} for k, v in self.chat_template.items()]
        elif self.chat_template is not None:
            # Legacy format for single templates: Just make them a key in tokenizer_config.json
            tokenizer_config["chat_template"] = self.chat_template
        return tokenizer_config, saved_raw_chat_template_files