def run(
        self,
        decoded_tokens: list[int],
        complete_transfers: bool = True,
        expected_stored_gpu_block_indexes: tuple[int, ...] = (),
        expected_loaded_gpu_block_indexes: tuple[int, ...] = (),
        expected_flushed_gpu_block_indexes: tuple[int, ...] = (),
    ):
        """
        Runs multiple engine (scheduler + worker) steps.
        Assumes a single request is running.

        Args:
            decoded_tokens: the tokens to yield at each step.
            complete_transfers: complete transfers immediately
            expected_stored_gpu_block_indexes: GPU block indexes
                that are expected to be written during the run.
            expected_loaded_gpu_block_indexes: GPU block indexes
                that are expected to be loaded during the run.
            expected_flushed_gpu_block_indexes: GPU block indexes
                that are expected to be flushed during the run.
        """

        self.manager.reset_mock()
        self._run(decoded_tokens, complete_transfers)

        loaded_gpu_block_indexes: set[int] = set()
        for transfer in self.completed_loads:
            for gpu_block_idx, offloaded_address in zip(
                transfer.gpu_block_indices, transfer.offload_addresses
            ):
                loaded_gpu_block_indexes.add(gpu_block_idx)
                assert gpu_block_idx == self.offloaded[offloaded_address]

        assert set(expected_loaded_gpu_block_indexes) == loaded_gpu_block_indexes
        self.completed_loads.clear()

        stored_gpu_block_indexes: set[int] = set()
        for transfer in self.completed_stores:
            for gpu_block_idx, offloaded_address in zip(
                transfer.gpu_block_indices, transfer.offload_addresses
            ):
                stored_gpu_block_indexes.add(gpu_block_idx)
                self.offloaded[offloaded_address] = gpu_block_idx

        assert set(expected_stored_gpu_block_indexes) == stored_gpu_block_indexes
        self.completed_stores.clear()

        assert set(expected_flushed_gpu_block_indexes) == self.flushed_gpu_block_indexes
        self.flushed_gpu_block_indexes.clear()