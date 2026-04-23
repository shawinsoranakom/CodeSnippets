def __init__(self, loader: DataLoader) -> None:
        self._dataset = loader.dataset
        self._shared_seed = None
        self._pg = None
        if isinstance(self._dataset, IterDataPipe):
            if dist.is_available() and dist.is_initialized():
                self._pg = dist.new_group(backend="gloo")
            self._shared_seed = _share_dist_seed(loader.generator, self._pg)
            shared_rng = torch.Generator()
            shared_rng.manual_seed(self._shared_seed)
            self._dataset = torch.utils.data.graph_settings.apply_random_seed(
                self._dataset, shared_rng
            )
        self._dataset_kind = loader._dataset_kind
        self._IterableDataset_len_called = loader._IterableDataset_len_called
        self._auto_collation = loader._auto_collation
        self._drop_last = loader.drop_last
        self._index_sampler = loader._index_sampler
        self._num_workers = loader.num_workers
        ws, rank = _get_distributed_settings()
        self._world_size = ws
        self._rank = rank

        if loader.pin_memory and loader.pin_memory_device:
            warnings.warn(
                "pin_memory_device is deprecated, the current accelerator will be used as the device,"
                f"ignore pin_memory_device='{loader.pin_memory_device}'.",
                stacklevel=2,
            )
        if loader.pin_memory and not torch.accelerator.is_available():
            warn_msg = (
                "'pin_memory' argument is set as true but no accelerator is found, "
                "then device pinned memory won't be used."
            )
            warnings.warn(warn_msg, stacklevel=2)

        # Enabling pin_memory in _BaseDataLoaderIter to support identical
        # behavior in forked implementations using _BaseDataLoaderIter.
        self._pin_memory = loader.pin_memory and torch.accelerator.is_available()

        # Set pin memory device based on the current accelerator.
        self._pin_memory_device = (
            acc.type
            if self._pin_memory
            and (acc := torch.accelerator.current_accelerator()) is not None
            else None
        )

        # Currently, pin_memory would raise error on the MPS backend (see
        # https://github.com/pytorch/pytorch/issues/86060), so forcibly
        # disable pin_memory on MPS. Remove this restriction once pinned
        # memory allocation for MPS is fixed.
        if self._pin_memory_device == "mps":
            self._pin_memory = False
            warn_msg = (
                "'pin_memory' argument is set as true but not supported on MPS now, "
                "device pinned memory won't be used."
            )
            warnings.warn(warn_msg, stacklevel=2)

        self._timeout = loader.timeout
        self._collate_fn = loader.collate_fn
        self._sampler_iter = iter(self._index_sampler)
        self._base_seed = (
            torch.empty((), dtype=torch.int64)
            .random_(generator=loader.generator)
            .item()
        )
        self._persistent_workers = loader.persistent_workers
        self._num_yielded = 0
        self._profile_name = f"enumerate(DataLoader)#{self.__class__.__name__}.__next__"