def iter_model_names(self, args):
        # for model_name in list_models(pretrained=True, exclude_filters=["*in21k"]):
        model_names = sorted(TIMM_MODELS.keys())
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