def __init__(
        self,
        args: GlueDataTrainingArguments,
        tokenizer: PreTrainedTokenizerBase,
        limit_length: int | None = None,
        mode: str | Split = Split.train,
        cache_dir: str | None = None,
    ):
        warnings.warn(
            "This dataset will be removed from the library soon, preprocessing should be handled with the Hugging Face Datasets "
            "library. You can have a look at this example script for pointers: "
            "https://github.com/huggingface/transformers/blob/main/examples/pytorch/text-classification/run_glue.py",
            FutureWarning,
        )
        self.args = args
        self.processor = glue_processors[args.task_name]()
        self.output_mode = glue_output_modes[args.task_name]
        if isinstance(mode, str):
            try:
                mode = Split[mode]
            except KeyError:
                raise KeyError("mode is not a valid split name")
        # Load data features from cache or dataset file
        cached_features_file = os.path.join(
            cache_dir if cache_dir is not None else args.data_dir,
            f"cached_{mode.value}_{tokenizer.__class__.__name__}_{args.max_seq_length}_{args.task_name}",
        )
        label_list = self.processor.get_labels()
        if args.task_name in ["mnli", "mnli-mm"] and tokenizer.__class__.__name__ in (
            "RobertaTokenizer",
            "XLMRobertaTokenizer",
            "BartTokenizer",
            "BartTokenizerFast",
        ):
            # HACK(label indices are swapped in RoBERTa pretrained model)
            label_list[1], label_list[2] = label_list[2], label_list[1]
        self.label_list = label_list

        # Make sure only the first process in distributed training processes the dataset,
        # and the others will use the cache.
        lock_path = cached_features_file + ".lock"
        with FileLock(lock_path):
            if os.path.exists(cached_features_file) and not args.overwrite_cache:
                start = time.time()
                check_torch_load_is_safe()
                self.features = torch.load(cached_features_file, weights_only=True)
                logger.info(
                    f"Loading features from cached file {cached_features_file} [took %.3f s]", time.time() - start
                )
            else:
                logger.info(f"Creating features from dataset file at {args.data_dir}")

                if mode == Split.dev:
                    examples = self.processor.get_dev_examples(args.data_dir)
                elif mode == Split.test:
                    examples = self.processor.get_test_examples(args.data_dir)
                else:
                    examples = self.processor.get_train_examples(args.data_dir)
                if limit_length is not None:
                    examples = examples[:limit_length]
                self.features = glue_convert_examples_to_features(
                    examples,
                    tokenizer,
                    max_length=args.max_seq_length,
                    label_list=label_list,
                    output_mode=self.output_mode,
                )
                start = time.time()
                torch.save(self.features, cached_features_file)
                # ^ This seems to take a lot of time so I want to investigate why and how we can improve.
                logger.info(
                    f"Saving features into cached file {cached_features_file} [took {time.time() - start:.3f} s]"
                )