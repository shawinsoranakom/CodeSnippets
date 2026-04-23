def _parse_transfers(self):
        for transfer_spec in self.offloading_spec.get_flushed_transfers():
            src_spec, dst_spec = transfer_spec
            assert isinstance(src_spec, GPULoadStoreSpec)

            for block_id in src_spec.block_ids:
                self.flushed_gpu_block_indexes.add(
                    self.gpu_block_index[block_id.item()]
                )

        block_size_factor = self.offloaded_block_size // self.gpu_block_size

        for transfer_spec in self.offloading_spec.get_completed_transfers():
            src_spec, dst_spec = transfer_spec

            if isinstance(src_spec, GPULoadStoreSpec):
                store = True
                gpu_spec = src_spec
                offload_spec = dst_spec
            else:
                store = False
                gpu_spec = dst_spec
                offload_spec = src_spec

            assert isinstance(offload_spec, MockLoadStoreSpec)
            assert isinstance(gpu_spec, GPULoadStoreSpec)

            gpu_block_indices: list[int] = []
            for block_id in gpu_spec.block_ids:
                gpu_block_indices.append(self.gpu_block_index[block_id.item()])

            # list of (offload_key, sub_block_offset)
            offload_addresses: list[Any] = []
            for offload_key in offload_spec.offload_keys:
                for sub_block_idx in range(block_size_factor):
                    offload_addresses.append((offload_key, sub_block_idx))

            if store:
                assert len(gpu_block_indices) == len(offload_addresses)

                self.completed_stores.append(
                    TransferSummary(gpu_block_indices, offload_addresses)
                )
            else:
                remainder_sub_block_count = len(offload_addresses) - len(
                    gpu_block_indices
                )
                assert remainder_sub_block_count >= 0
                assert remainder_sub_block_count < block_size_factor
                offload_addresses = offload_addresses[remainder_sub_block_count:]

                self.completed_loads.append(
                    TransferSummary(gpu_block_indices, offload_addresses)
                )