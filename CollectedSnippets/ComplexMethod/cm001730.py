def run_model_pipeline_tests(
        self,
        task,
        repo_name,
        model_architecture,
        tokenizer_names,
        image_processor_names,
        feature_extractor_names,
        processor_names,
        commit,
        dtype="float32",
    ):
        """Run pipeline tests for a specific `task` with the give model class and tokenizer/processor class names

        Args:
            task (`str`):
                A task name. This should be a key in the mapping `pipeline_test_mapping`.
            repo_name (`str`):
                A model repository id on the Hub.
            model_architecture (`type`):
                A subclass of `PretrainedModel` or `PretrainedModel`.
            tokenizer_names (`list[str]`):
                A list of names of a subclasses of `PreTrainedTokenizerFast` or `PreTrainedTokenizer`.
            image_processor_names (`list[str]`):
                A list of names of subclasses of `BaseImageProcessor`.
            feature_extractor_names (`list[str]`):
                A list of names of subclasses of `FeatureExtractionMixin`.
            processor_names (`list[str]`):
                A list of names of subclasses of `ProcessorMixin`.
            commit (`str`):
                The commit hash of the model repository on the Hub.
            dtype (`str`, `optional`, defaults to `'float32'`):
                The torch dtype to use for the model. Can be used for FP16/other precision inference.
        """
        # Get an instance of the corresponding class `XXXPipelineTests` in order to use `get_test_pipeline` and
        # `run_pipeline_test`.
        pipeline_test_class_name = pipeline_test_mapping[task]["test"].__name__

        # If no image processor or feature extractor is found, we still need to test the pipeline with None
        # otherwise for any empty list we might skip all the tests
        tokenizer_names = tokenizer_names or [None]
        image_processor_names = image_processor_names or [None]
        feature_extractor_names = feature_extractor_names or [None]
        processor_names = processor_names or [None]

        test_cases = [
            {
                "tokenizer_name": tokenizer_name,
                "image_processor_name": image_processor_name,
                "feature_extractor_name": feature_extractor_name,
                "processor_name": processor_name,
            }
            for tokenizer_name in tokenizer_names
            for image_processor_name in image_processor_names
            for feature_extractor_name in feature_extractor_names
            for processor_name in processor_names
        ]

        for test_case in test_cases:
            tokenizer_name = test_case["tokenizer_name"]
            image_processor_name = test_case["image_processor_name"]
            feature_extractor_name = test_case["feature_extractor_name"]
            processor_name = test_case["processor_name"]

            do_skip_test_case = self.is_pipeline_test_to_skip(
                pipeline_test_class_name,
                model_architecture.config_class,
                model_architecture,
                tokenizer_name,
                image_processor_name,
                feature_extractor_name,
                processor_name,
            )

            if do_skip_test_case:
                logger.warning(
                    f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: test is "
                    f"currently known to fail for: model `{model_architecture.__name__}` | tokenizer "
                    f"`{tokenizer_name}` | image processor `{image_processor_name}` | feature extractor {feature_extractor_name}."
                )
                continue

            self.run_pipeline_test(
                task,
                repo_name,
                model_architecture,
                tokenizer_name=tokenizer_name,
                image_processor_name=image_processor_name,
                feature_extractor_name=feature_extractor_name,
                processor_name=processor_name,
                commit=commit,
                dtype=dtype,
            )