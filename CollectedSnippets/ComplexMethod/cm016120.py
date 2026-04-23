def load_model(
        self,
        device,
        model_name,
        batch_size=None,
        part=None,
        extra_args=None,
    ):
        if self.args.enable_activation_checkpointing:
            raise NotImplementedError(
                "Activation checkpointing not implemented for Torchbench models"
            )
        is_training = self.args.training
        use_eval_mode = self.args.use_eval_mode

        candidates = [
            f"torchbenchmark.models.{model_name}",
            f"torchbenchmark.canary_models.{model_name}",
        ]
        if self._fb_models_available:
            candidates.append(f"torchbenchmark.models.fb.{model_name}")

        for c in candidates:
            try:
                module = importlib.import_module(c)
                break
            except ModuleNotFoundError as e:
                if e.name != c:
                    raise
        else:
            raise ImportError(f"could not import any of {candidates}")
        benchmark_cls = getattr(module, "Model", None)
        if benchmark_cls is None:
            raise NotImplementedError(f"{model_name}.Model is None")

        if not hasattr(benchmark_cls, "name"):
            benchmark_cls.name = model_name

        cant_change_batch_size = (
            not getattr(benchmark_cls, "ALLOW_CUSTOMIZE_BSIZE", True)
            or model_name in self._config["dont_change_batch_size"]
        )
        if cant_change_batch_size:
            batch_size = None
        if (
            batch_size is None
            and is_training
            and model_name in self._batch_size["training"]
        ):
            batch_size = self._batch_size["training"][model_name]
        elif (
            batch_size is None
            and not is_training
            and model_name in self._batch_size["inference"]
        ):
            batch_size = self._batch_size["inference"][model_name]

        # Control the memory footprint for few models
        if self.args.accuracy and model_name in self._accuracy["max_batch_size"]:
            batch_size = min(batch_size, self._accuracy["max_batch_size"][model_name])

        # workaround "RuntimeError: not allowed to set torch.backends.cudnn flags"
        torch.backends.__allow_nonbracketed_mutation_flag = True
        if extra_args is None:
            extra_args = []
        if part:
            extra_args += ["--part", part]

        # sam_fast only runs with amp
        if model_name == "sam_fast":
            self.args.amp = True
            self.setup_amp()

        if model_name == "vision_maskrcnn" and is_training:
            # Output of vision_maskrcnn model is a list of bounding boxes,
            # sorted on the basis of their scores. This makes accuracy
            # comparison hard with torch.compile. torch.compile can cause minor
            # divergences in the output because of how fusion works for amp in
            # TorchInductor compared to eager.  Therefore, instead of looking at
            # all the bounding boxes, we compare only top 4.
            model_kwargs = {"box_detections_per_img": 4}
            benchmark = benchmark_cls(
                test="train",
                device=device,
                batch_size=batch_size,
                extra_args=extra_args,
                model_kwargs=model_kwargs,
            )
            use_eval_mode = True
        elif is_training:
            benchmark = benchmark_cls(
                test="train",
                device=device,
                batch_size=batch_size,
                extra_args=extra_args,
            )
        else:
            benchmark = benchmark_cls(
                test="eval",
                device=device,
                batch_size=batch_size,
                extra_args=extra_args,
            )
        model, example_inputs = benchmark.get_module()
        if model_name in [
            "basic_gnn_edgecnn",
            "basic_gnn_gcn",
            "basic_gnn_sage",
            "basic_gnn_gin",
        ]:
            _reassign_parameters(model)

        # Models that must be in train mode while training
        if is_training and (
            not use_eval_mode or model_name in self._config["only_training"]
        ):
            model.train()
        else:
            model.eval()
        gc.collect()
        batch_size = benchmark.batch_size
        if model_name == "torchrec_dlrm":
            batch_namedtuple = namedtuple(
                "Batch", "dense_features sparse_features labels"
            )
            example_inputs = tuple(
                batch_namedtuple(
                    dense_features=batch.dense_features,
                    sparse_features=batch.sparse_features,
                    labels=batch.labels,
                )
                for batch in example_inputs
            )
        # Torchbench has quite different setup for yolov3, so directly passing
        # the right example_inputs
        if model_name == "yolov3":
            example_inputs = (torch.rand(batch_size, 3, 384, 512).to(device),)
        # See https://github.com/pytorch/benchmark/issues/1561
        if model_name == "maml_omniglot":
            batch_size = 5
            if example_inputs[0].shape[0] != batch_size:
                raise AssertionError(
                    f"Expected batch size {batch_size}, but got {example_inputs[0].shape[0]}"
                )
        if model_name == "vision_maskrcnn":
            batch_size = 1
        # global current_name, current_device
        # current_device = device
        # current_name = benchmark.name

        if self.args.trace_on_xla:
            # work around for: https://github.com/pytorch/xla/issues/4174
            import torch_xla  # noqa: F401

        # Turning off kv cache for torchbench models. This is not the right
        # thing to do, but the torchbench models are way outdated, and since we
        # are using torchbench pt2 dashboard to track regressions (rather than
        # improving performance), we are just setting the kv cache to false.
        # Real transformers benchmarks will be added soon using a different
        # infra.
        if (
            model_name.startswith("hf")
            and hasattr(model, "config")
            and hasattr(model.config, "use_cache")
        ):
            model.config.use_cache = False

        self.validate_model(benchmark.name, model, example_inputs)
        return device, benchmark.name, model, example_inputs, batch_size