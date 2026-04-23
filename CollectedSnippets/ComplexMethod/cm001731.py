def run_pipeline_test(
        self,
        task,
        repo_name,
        model_architecture,
        tokenizer_name,
        image_processor_name,
        feature_extractor_name,
        processor_name,
        commit,
        dtype="float32",
    ):
        """Run pipeline tests for a specific `task` with the give model class and tokenizer/processor class name

        The model will be loaded from a model repository on the Hub.

        Args:
            task (`str`):
                A task name. This should be a key in the mapping `pipeline_test_mapping`.
            repo_name (`str`):
                A model repository id on the Hub.
            model_architecture (`type`):
                A subclass of `PretrainedModel` or `PretrainedModel`.
            tokenizer_name (`str`):
                The name of a subclass of `PreTrainedTokenizerFast` or `PreTrainedTokenizer`.
            image_processor_name (`str`):
                The name of a subclass of `BaseImageProcessor`.
            feature_extractor_name (`str`):
                The name of a subclass of `FeatureExtractionMixin`.
            processor_name (`str`):
                The name of a subclass of `ProcessorMixin`.
            commit (`str`):
                The commit hash of the model repository on the Hub.
            dtype (`str`, `optional`, defaults to `'float32'`):
                The torch dtype to use for the model. Can be used for FP16/other precision inference.
        """
        repo_id = f"{TRANSFORMERS_TINY_MODEL_PATH}/{repo_name}"
        model_type = model_architecture.config_class.model_type

        if TRANSFORMERS_TINY_MODEL_PATH != "hf-internal-testing":
            repo_id = os.path.join(TRANSFORMERS_TINY_MODEL_PATH, model_type, repo_name)

        # -------------------- Load model --------------------

        # TODO: We should check if a model file is on the Hub repo. instead.
        try:
            model = model_architecture.from_pretrained(repo_id, revision=commit, use_safetensors=True)
        except Exception:
            logger.warning(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: Could not find or load "
                f"the model from `{repo_id}` with `{model_architecture}`."
            )
            self.skipTest(f"Could not find or load the model from {repo_id} with {model_architecture}.")

        # -------------------- Load tokenizer --------------------

        tokenizer = None
        if tokenizer_name is not None:
            tokenizer_class = getattr(transformers_module, tokenizer_name)
            tokenizer = tokenizer_class.from_pretrained(repo_id, revision=commit)

        # -------------------- Load processors --------------------

        processors = {}
        for key, name in zip(
            ["image_processor", "feature_extractor", "processor"],
            [image_processor_name, feature_extractor_name, processor_name],
        ):
            if name is not None:
                try:
                    # Can fail if some extra dependencies are not installed
                    processor_class = getattr(transformers_module, name)
                    processor = processor_class.from_pretrained(repo_id, revision=commit)
                    processors[key] = processor
                except Exception:
                    logger.warning(
                        f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: "
                        f"Could not load the {key} from `{repo_id}` with `{name}`."
                    )
                    self.skipTest(f"Could not load the {key} from {repo_id} with {name}.")

        # ---------------------------------------------------------

        # TODO: Maybe not upload such problematic tiny models to Hub.
        if tokenizer is None and "image_processor" not in processors and "feature_extractor" not in processors:
            logger.warning(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: Could not find or load "
                f"any tokenizer / image processor / feature extractor from `{repo_id}`."
            )
            self.skipTest(f"Could not find or load any tokenizer / processor from {repo_id}.")

        pipeline_test_class_name = pipeline_test_mapping[task]["test"].__name__
        if self.is_pipeline_test_to_skip_more(pipeline_test_class_name, model.config, model, tokenizer, **processors):
            logger.warning(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: test is "
                f"currently known to fail for: model `{model_architecture.__name__}` | tokenizer "
                f"`{tokenizer_name}` | image processor `{image_processor_name}` | feature extractor `{feature_extractor_name}`."
            )
            self.skipTest(
                f"Test is known to fail for: model `{model_architecture.__name__}` | tokenizer `{tokenizer_name}` "
                f"| image processor `{image_processor_name}` | feature extractor `{feature_extractor_name}`."
            )

        # validate
        validate_test_components(model, tokenizer)

        if hasattr(model, "eval"):
            model = model.eval()

        # Get an instance of the corresponding class `XXXPipelineTests` in order to use `get_test_pipeline` and
        # `run_pipeline_test`.
        task_test = pipeline_test_mapping[task]["test"]()

        pipeline, examples = task_test.get_test_pipeline(model, tokenizer, **processors, dtype=dtype)
        if pipeline is None:
            # The test can disable itself, but it should be very marginal
            # Concerns: Wav2Vec2ForCTC without tokenizer test (FastTokenizer don't exist)
            logger.warning(
                f"{self.__class__.__name__}::test_pipeline_{task.replace('-', '_')}_{dtype} is skipped: Could not get the "
                "pipeline for testing."
            )
            self.skipTest(reason="Could not get the pipeline for testing.")

        task_test.run_pipeline_test(pipeline, examples)

        def run_batch_test(pipeline, examples):
            # Need to copy because `Conversation` are stateful
            if pipeline.tokenizer is not None and pipeline.tokenizer.pad_token_id is None:
                return  # No batching for this and it's OK

            # 10 examples with batch size 4 means there needs to be a unfinished batch
            # which is important for the unbatcher
            def data(n):
                for _ in range(n):
                    # Need to copy because Conversation object is mutated
                    yield copy.deepcopy(random.choice(examples))

            out = []
            for item in pipeline(data(10), batch_size=4):
                out.append(item)
            self.assertEqual(len(out), 10)

        run_batch_test(pipeline, examples)