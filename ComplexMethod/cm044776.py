def __init__(
        self,
        dataset: Dataset,
        num_replicas: Optional[int] = None,
        rank: Optional[int] = None,
        shuffle: bool = True,
        seed: int = 0,
        drop_last: bool = False,
        batch_size: int = 32,
    ) -> None:
        if num_replicas is None:
            if not dist.is_available():
                raise RuntimeError("Requires distributed package to be available")
            num_replicas = dist.get_world_size() if torch.cuda.is_available() else 1
        if rank is None:
            if not dist.is_available():
                raise RuntimeError("Requires distributed package to be available")
            rank = dist.get_rank() if torch.cuda.is_available() else 0
            if torch.cuda.is_available():
                torch.cuda.set_device(rank)
        if rank >= num_replicas or rank < 0:
            raise ValueError("Invalid rank {}, rank should be in the interval [0, {}]".format(rank, num_replicas - 1))
        self.dataset = dataset
        self.num_replicas = num_replicas
        self.rank = rank
        self.epoch = 0
        self.drop_last = drop_last
        # If the dataset length is evenly divisible by # of replicas, then there
        # is no need to drop any data, since the dataset will be split equally.
        if self.drop_last and len(self.dataset) % self.num_replicas != 0:  # type: ignore[arg-type]
            # Split to nearest available length that is evenly divisible.
            # This is to ensure each rank receives the same amount of data when
            # using this Sampler.
            self.num_samples = math.ceil(
                (len(self.dataset) - self.num_replicas) / self.num_replicas,  # type: ignore[arg-type]
            )
        else:
            self.num_samples = math.ceil(
                len(self.dataset) / self.num_replicas,
            )  # type: ignore[arg-type]
        self.total_size = self.num_samples * self.num_replicas
        self.shuffle = shuffle
        self.seed = seed
        self.batch_size = batch_size
        self.id_with_length = self._get_sample_lengths()
        self.id_buckets = self.make_buckets(bucket_width=2.0)