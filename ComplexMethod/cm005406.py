def __init__(
        self,
        args: SquadDataTrainingArguments,
        tokenizer: PreTrainedTokenizer,
        limit_length: int | None = None,
        mode: str | Split = Split.train,
        is_language_sensitive: bool = False,
        cache_dir: str | None = None,
        dataset_format: str = "pt",
    ):
        self.args = args
        self.is_language_sensitive = is_language_sensitive
        self.processor = SquadV2Processor() if args.version_2_with_negative else SquadV1Processor()
        if isinstance(mode, str):
            try:
                mode = Split[mode]
            except KeyError:
                raise KeyError("mode is not a valid split name")
        self.mode = mode
        # Load data features from cache or dataset file
        version_tag = "v2" if args.version_2_with_negative else "v1"
        cached_features_file = os.path.join(
            cache_dir if cache_dir is not None else args.data_dir,
            f"cached_{mode.value}_{tokenizer.__class__.__name__}_{args.max_seq_length}_{version_tag}",
        )

        # Make sure only the first process in distributed training processes the dataset,
        # and the others will use the cache.
        lock_path = cached_features_file + ".lock"
        with FileLock(lock_path):
            if os.path.exists(cached_features_file) and not args.overwrite_cache:
                start = time.time()
                check_torch_load_is_safe()
                self.old_features = torch.load(cached_features_file, weights_only=True)

                # Legacy cache files have only features, while new cache files
                # will have dataset and examples also.
                self.features = self.old_features["features"]
                self.dataset = self.old_features.get("dataset", None)
                self.examples = self.old_features.get("examples", None)
                logger.info(
                    f"Loading features from cached file {cached_features_file} [took %.3f s]", time.time() - start
                )

                if self.dataset is None or self.examples is None:
                    logger.warning(
                        f"Deleting cached file {cached_features_file} will allow dataset and examples to be cached in"
                        " future run"
                    )
            else:
                if mode == Split.dev:
                    self.examples = self.processor.get_dev_examples(args.data_dir)
                else:
                    self.examples = self.processor.get_train_examples(args.data_dir)

                self.features, self.dataset = squad_convert_examples_to_features(
                    examples=self.examples,
                    tokenizer=tokenizer,
                    max_seq_length=args.max_seq_length,
                    doc_stride=args.doc_stride,
                    max_query_length=args.max_query_length,
                    is_training=mode == Split.train,
                    threads=args.threads,
                    return_dataset=dataset_format,
                )

                start = time.time()
                torch.save(
                    {"features": self.features, "dataset": self.dataset, "examples": self.examples},
                    cached_features_file,
                )
                # ^ This seems to take a lot of time so I want to investigate why and how we can improve.
                logger.info(
                    f"Saving features into cached file {cached_features_file} [took {time.time() - start:.3f} s]"
                )