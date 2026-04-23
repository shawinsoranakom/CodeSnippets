def __init__(
        self,
        dataset: Dataset[_T_co],
        batch_size: int | None = 1,
        shuffle: bool | None = None,
        sampler: Sampler | Iterable | None = None,
        batch_sampler: Sampler[list] | Iterable[list] | None = None,
        num_workers: int = 0,
        collate_fn: _collate_fn_t | None = None,
        pin_memory: bool = False,
        drop_last: bool = False,
        timeout: float = 0,
        worker_init_fn: _worker_init_fn_t | None = None,
        multiprocessing_context=None,
        generator=None,
        *,
        prefetch_factor: int | None = None,
        persistent_workers: bool = False,
        pin_memory_device: str = "",
        in_order: bool = True,
    ) -> None:
        torch._C._log_api_usage_once("python.data_loader")

        if num_workers < 0:
            raise ValueError(
                "num_workers option should be non-negative; "
                "use num_workers=0 to disable multiprocessing."
            )

        if timeout < 0:
            raise ValueError("timeout option should be non-negative")

        if num_workers == 0 and prefetch_factor is not None:
            raise ValueError(
                "prefetch_factor option could only be specified in multiprocessing."
                "let num_workers > 0 to enable multiprocessing, otherwise set prefetch_factor to None."
            )
        elif num_workers > 0 and prefetch_factor is None:
            prefetch_factor = 2
        elif prefetch_factor is not None and prefetch_factor < 0:
            raise ValueError("prefetch_factor option should be non-negative")

        if persistent_workers and num_workers == 0:
            raise ValueError("persistent_workers option needs num_workers > 0")

        self.dataset = dataset
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.pin_memory = pin_memory
        self.pin_memory_device = pin_memory_device
        self.timeout = timeout
        self.worker_init_fn = worker_init_fn
        self.multiprocessing_context = multiprocessing_context
        self.in_order = in_order

        # Adds forward compatibilities so classic DataLoader can work with DataPipes:
        #   _DataPipeSerializationWrapper container makes it easier to serialize without redefining pickler
        if isinstance(self.dataset, IterDataPipe):
            self.dataset = _IterDataPipeSerializationWrapper(self.dataset)
        elif isinstance(self.dataset, MapDataPipe):
            self.dataset = _MapDataPipeSerializationWrapper(self.dataset)

        # Arg-check dataset related before checking samplers because we want to
        # tell users that iterable-style datasets are incompatible with custom
        # samplers first, so that they don't learn that this combo doesn't work
        # after spending time fixing the custom sampler errors.
        if isinstance(dataset, IterableDataset):
            self._dataset_kind = _DatasetKind.Iterable
            # NOTE [ Custom Samplers and IterableDataset ]
            #
            # `IterableDataset` does not support custom `batch_sampler` or
            # `sampler` since the key is irrelevant (unless we support
            # generator-style dataset one day...).
            #
            # For `sampler`, we always create a dummy sampler. This is an
            # infinite sampler even when the dataset may have an implemented
            # finite `__len__` because in multi-process data loading, naive
            # settings will return duplicated data (which may be desired), and
            # thus using a sampler with length matching that of dataset will
            # cause data lost (you may have duplicates of the first couple
            # batches, but never see anything afterwards). Therefore,
            # `Iterabledataset` always uses an infinite sampler, an instance of
            # `_InfiniteConstantSampler` defined above.
            #
            # A custom `batch_sampler` essentially only controls the batch size.
            # However, it is unclear how useful it would be since an iterable-style
            # dataset can handle that within itself. Moreover, it is pointless
            # in multi-process data loading as the assignment order of batches
            # to workers is an implementation detail so users can not control
            # how to batchify each worker's iterable. Thus, we disable this
            # option. If this turns out to be useful in future, we can re-enable
            # this, and support custom samplers that specify the assignments to
            # specific workers.
            if isinstance(dataset, IterDataPipe):
                if shuffle is not None:
                    dataset = torch.utils.data.graph_settings.apply_shuffle_settings(
                        dataset, shuffle=shuffle
                    )
            # We cannot check `shuffle is not None` here, since previously `shuffle=False` was the default.
            elif shuffle not in {False, None}:
                raise ValueError(
                    f"DataLoader with IterableDataset: expected unspecified shuffle option, but got shuffle={shuffle}"
                )

            if sampler is not None:
                # See NOTE [ Custom Samplers and IterableDataset ]
                raise ValueError(
                    f"DataLoader with IterableDataset: expected unspecified sampler option, but got sampler={sampler}"
                )
            elif batch_sampler is not None:
                # See NOTE [ Custom Samplers and IterableDataset ]
                raise ValueError(
                    "DataLoader with IterableDataset: expected unspecified "
                    f"batch_sampler option, but got batch_sampler={batch_sampler}"
                )
        else:
            shuffle = bool(shuffle)
            self._dataset_kind = _DatasetKind.Map

        if sampler is not None and shuffle:
            raise ValueError("sampler option is mutually exclusive with shuffle")

        if batch_sampler is not None:
            # auto_collation with custom batch_sampler
            if batch_size != 1 or shuffle or sampler is not None or drop_last:
                raise ValueError(
                    "batch_sampler option is mutually exclusive "
                    "with batch_size, shuffle, sampler, and "
                    "drop_last"
                )
            batch_size = None
            drop_last = False
        elif batch_size is None:
            # no auto_collation
            if drop_last:
                raise ValueError(
                    "batch_size=None option disables auto-batching "
                    "and is mutually exclusive with drop_last"
                )

        if sampler is None:  # give default samplers
            if self._dataset_kind == _DatasetKind.Iterable:
                # See NOTE [ Custom Samplers and IterableDataset ]
                sampler = _InfiniteConstantSampler()
            else:  # map-style
                if shuffle:
                    sampler = RandomSampler(dataset, generator=generator)  # type: ignore[arg-type]
                else:
                    sampler = SequentialSampler(dataset)  # type: ignore[arg-type]

        if batch_size is not None and batch_sampler is None:
            # auto_collation without custom batch_sampler
            batch_sampler = BatchSampler(sampler, batch_size, drop_last)

        self.batch_size = batch_size
        self.drop_last = drop_last
        self.sampler = sampler
        self.batch_sampler = batch_sampler
        self.generator = generator

        if collate_fn is None:
            if self._auto_collation:
                collate_fn = _utils.collate.default_collate
            else:
                collate_fn = _utils.collate.default_convert

        self.collate_fn = collate_fn
        self.persistent_workers = persistent_workers

        self.__initialized = True
        self._IterableDataset_len_called = (
            None  # See NOTE [ IterableDataset and __len__ ]
        )

        self._iterator = None

        self.check_worker_number_rationality()