def get_data_adapter(
    x,
    y=None,
    sample_weight=None,
    batch_size=None,
    steps_per_epoch=None,
    shuffle=False,
    class_weight=None,
):
    # Allow passing a custom data adapter.
    if isinstance(x, data_adapter.DataAdapter):
        return x

    # Check for multi-process/worker distribution.
    distribution = distribution_lib.distribution()
    if (
        distribution is not None
        and getattr(distribution, "_is_multi_process", False)
        and getattr(distribution, "auto_shard_dataset", False)
        and not is_tf_dataset(x)
    ):
        raise ValueError(
            "When using a multi-worker distribution with auto-sharding enabled, "
            "the data must be provided as a `tf.data.Dataset` instance. "
            f"Received: type(x)={type(x)}. "
            "If the dataset is already sharded across workers, then set "
            "`distribution.auto_shard_dataset = False`."
        )

    if array_data_adapter.can_convert_arrays((x, y, sample_weight)):
        return ArrayDataAdapter(
            x,
            y,
            sample_weight=sample_weight,
            class_weight=class_weight,
            shuffle=shuffle,
            batch_size=batch_size,
            steps=steps_per_epoch,
        )
    elif is_tf_dataset(x):
        # Unsupported args: y, sample_weight, shuffle
        if y is not None:
            raise_unsupported_arg("y", "the targets", "tf.data.Dataset")
        if sample_weight is not None:
            raise_unsupported_arg(
                "sample_weights", "the sample weights", "tf.data.Dataset"
            )
        return TFDatasetAdapter(
            x, class_weight=class_weight, distribution=distribution
        )
        # TODO: should we warn or not?
        # warnings.warn(
        #     "`shuffle=True` was passed, but will be ignored since the "
        #     "data `x` was provided as a tf.data.Dataset. The Dataset is "
        #     "expected to already be shuffled "
        #     "(via `.shuffle(tf.data.AUTOTUNE)`)"
        # )
    elif isinstance(x, py_dataset_adapter.PyDataset):
        if y is not None:
            raise_unsupported_arg("y", "the targets", "PyDataset")
        if sample_weight is not None:
            raise_unsupported_arg(
                "sample_weights", "the sample weights", "PyDataset"
            )
        return PyDatasetAdapter(x, class_weight=class_weight, shuffle=shuffle)
        # TODO: should we warn or not?
        # if x.num_batches is None and shuffle:
        #     warnings.warn(
        #         "`shuffle=True` was passed, but will be ignored since the "
        #         "data `x` was provided as a infinite PyDataset. The "
        #         "PyDataset is expected to already be shuffled."
        # )
    elif is_torch_dataloader(x):
        if y is not None:
            raise_unsupported_arg("y", "the targets", "torch DataLoader")
        if sample_weight is not None:
            raise_unsupported_arg(
                "sample_weights", "the sample weights", "torch DataLoader"
            )
        if class_weight is not None:
            raise ValueError(
                "Argument `class_weight` is not supported for torch "
                f"DataLoader inputs. You can modify your `__getitem__ ` method"
                " to return input tensor, label and class_weight. "
                "Alternatively, use a custom training loop. See the User Guide "
                "https://keras.io/guides/custom_train_step_in_torch/"
                "#supporting-sampleweight-amp-classweight for more details. "
                f"Received: class_weight={class_weight}"
            )
        return TorchDataLoaderAdapter(x)
        # TODO: should we warn or not?
        # warnings.warn(
        #     "`shuffle=True` was passed, but will be ignored since the "
        #     "data `x` was provided as a torch DataLoader. The DataLoader "
        #     "is expected to already be shuffled."
        # )
    elif is_grain_dataset(x):
        if y is not None:
            raise_unsupported_arg(
                "y", "the targets", "grain.Dataset and grain.DataLoader"
            )
        if sample_weight is not None:
            raise_unsupported_arg(
                "sample_weights",
                "the sample weights",
                "grain.Dataset and grain.DataLoader",
            )
        if class_weight is not None:
            raise ValueError(
                "Argument `class_weight` is not supported for grain.Dataset "
                f"and grain.DataLoader inputs. You can modify your "
                "`__getitem__ ` method to return input tensor, label and "
                "class_weight. "
                f"Received: class_weight={class_weight}"
            )
        return GrainDatasetAdapter(x)
        # TODO: should we warn or not?
        # warnings.warn(
        #     "`shuffle=True` was passed, but will be ignored since the "
        #     "data `x` was provided as a grain dataset. The grain dataset "
        #     "is expected to already be shuffled."
        # )
    elif isinstance(x, types.GeneratorType):
        if y is not None:
            raise_unsupported_arg("y", "the targets", "PyDataset")
        if sample_weight is not None:
            raise_unsupported_arg(
                "sample_weights", "the sample weights", "PyDataset"
            )
        if class_weight is not None:
            raise ValueError(
                "Argument `class_weight` is not supported for Python "
                f"generator inputs. Received: class_weight={class_weight}"
            )
        return GeneratorDataAdapter(x)
        # TODO: should we warn or not?
        # warnings.warn(
        #     "`shuffle=True` was passed, but will be ignored since the "
        #     "data `x` was provided as a generator. The generator "
        #     "is expected to yield already-shuffled data."
        # )
    else:
        raise ValueError(f"Unrecognized data type: x={x} (of type {type(x)})")