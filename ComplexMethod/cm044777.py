def __iter__(self) -> Iterator[T_co]:
        if self.shuffle:
            # deterministically shuffle based on epoch and seed
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch)
            random.seed(self.epoch + self.seed)
            shuffled_bucket = []
            for buc in self.id_buckets:
                buc_copy = buc.copy()
                shuffle(buc_copy)
                shuffled_bucket.append(buc_copy)
            grouped_batch_size = self.batch_size * self.num_replicas
            shuffled_bucket = list(itertools.chain(*shuffled_bucket))
            n_batch = int(math.ceil(len(shuffled_bucket) / grouped_batch_size))
            batches = [shuffled_bucket[b * grouped_batch_size : (b + 1) * grouped_batch_size] for b in range(n_batch)]
            shuffle(batches)
            indices = list(itertools.chain(*batches))
        else:
            # type: ignore[arg-type]
            indices = list(range(len(self.dataset)))

        if not self.drop_last:
            # add extra samples to make it evenly divisible
            padding_size = self.total_size - len(indices)
            if padding_size <= len(indices):
                indices += indices[:padding_size]
            else:
                indices += (indices * math.ceil(padding_size / len(indices)))[:padding_size]
        else:
            # remove tail of data to make it evenly divisible.
            indices = indices[: self.total_size]
        assert len(indices) == self.total_size

        # subsample
        indices = indices[self.rank : self.total_size : self.num_replicas]
        assert len(indices) == self.num_samples

        return iter(indices)