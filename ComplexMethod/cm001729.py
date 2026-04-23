def run_task_tests(self, task, dtype="float32"):
        """Run pipeline tests for a specific `task`

        Args:
            task (`str`):
                A task name. This should be a key in the mapping `pipeline_test_mapping`.
            dtype (`str`, `optional`, defaults to `'float32'`):
                The torch dtype to use for the model. Can be used for FP16/other precision inference.
        """
        if task not in self.pipeline_model_mapping:
            self.skipTest(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: `{task}` is not in "
                f"`self.pipeline_model_mapping` for `{self.__class__.__name__}`."
            )

        model_architectures = self.pipeline_model_mapping[task]
        if not isinstance(model_architectures, tuple):
            model_architectures = (model_architectures,)

        # We are going to run tests for multiple model architectures, some of them might be skipped
        # with this flag we are control if at least one model were tested or all were skipped
        at_least_one_model_is_tested = False

        for model_architecture in model_architectures:
            model_arch_name = model_architecture.__name__
            model_type = model_architecture.config_class.model_type

            if model_arch_name not in tiny_model_summary:
                continue

            tokenizer_names = tiny_model_summary[model_arch_name]["tokenizer_classes"]

            # Sort image processors and feature extractors from tiny-models json file
            image_processor_names = []
            feature_extractor_names = []

            processor_classes = tiny_model_summary[model_arch_name]["processor_classes"]
            for cls_name in processor_classes:
                if "ImageProcessor" in cls_name:
                    image_processor_names.append(cls_name)
                elif "FeatureExtractor" in cls_name:
                    feature_extractor_names.append(cls_name)

            # Processor classes are not in tiny models JSON file, so extract them from the mapping
            # processors are mapped to instance, e.g. "XxxProcessor"
            processor_names = PROCESSOR_MAPPING_NAMES.get(model_type, None)
            if not isinstance(processor_names, (list, tuple)):
                processor_names = [processor_names]

            commit = None
            if model_arch_name in tiny_model_summary and "sha" in tiny_model_summary[model_arch_name]:
                commit = tiny_model_summary[model_arch_name]["sha"]

            repo_name = f"tiny-random-{model_arch_name}"
            if TRANSFORMERS_TINY_MODEL_PATH != "hf-internal-testing":
                repo_name = model_arch_name

            self.run_model_pipeline_tests(
                task,
                repo_name,
                model_architecture,
                tokenizer_names=tokenizer_names,
                image_processor_names=image_processor_names,
                feature_extractor_names=feature_extractor_names,
                processor_names=processor_names,
                commit=commit,
                dtype=dtype,
            )
            at_least_one_model_is_tested = True

        if task in task_to_pipeline_and_spec_mapping:
            pipeline, hub_spec = task_to_pipeline_and_spec_mapping[task]
            compare_pipeline_args_to_hub_spec(pipeline, hub_spec)

        if not at_least_one_model_is_tested:
            self.skipTest(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: Could not find any "
                f"model architecture in the tiny models JSON file for `{task}`."
            )