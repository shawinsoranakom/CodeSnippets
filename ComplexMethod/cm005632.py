def save_pretrained(self, save_directory: str | os.PathLike, **kwargs: Any):
        """
        Save the pipeline's model and tokenizer.

        Args:
            save_directory (`str` or `os.PathLike`):
                A path to the directory where to saved. It will be created if it doesn't exist.
            kwargs (`dict[str, Any]`, *optional*):
                Additional key word arguments passed along to the [`~utils.PushToHubMixin.push_to_hub`] method.
        """
        if os.path.isfile(save_directory):
            logger.error(f"Provided path ({save_directory}) should be a directory, not a file")
            return
        os.makedirs(save_directory, exist_ok=True)

        if hasattr(self, "_registered_impl"):
            # Add info to the config
            pipeline_info = self._registered_impl.copy()
            custom_pipelines = {}
            for task, info in pipeline_info.items():
                if info["impl"] != self.__class__:
                    continue

                info = info.copy()
                module_name = info["impl"].__module__
                last_module = module_name.split(".")[-1]
                # Change classes into their names/full names
                info["impl"] = f"{last_module}.{info['impl'].__name__}"
                info["pt"] = tuple(c.__name__ for c in info["pt"])

                custom_pipelines[task] = info
            self.model.config.custom_pipelines = custom_pipelines
            # Save the pipeline custom code
            custom_object_save(self, save_directory)

        self.model.save_pretrained(save_directory, **kwargs)

        if self.tokenizer is not None:
            self.tokenizer.save_pretrained(save_directory, **kwargs)

        if self.feature_extractor is not None:
            self.feature_extractor.save_pretrained(save_directory, **kwargs)

        if self.image_processor is not None:
            self.image_processor.save_pretrained(save_directory, **kwargs)