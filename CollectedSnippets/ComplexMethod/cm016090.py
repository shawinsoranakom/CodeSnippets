def iter_model_names(self, args):
        model_names = list(BATCH_SIZE_KNOWN_MODELS.keys()) + list(EXTRA_MODELS.keys())
        model_names = set(model_names)
        model_names = sorted(model_names)

        start, end = self.get_benchmark_indices(len(model_names))
        for index, model_name in enumerate(model_names):
            if index < start or index >= end:
                continue
            if (
                not re.search("|".join(args.filter), model_name, re.IGNORECASE)
                or re.search("|".join(args.exclude), model_name, re.IGNORECASE)
                or model_name in args.exclude_exact
                or model_name in self.skip_models
            ):
                continue
            yield model_name