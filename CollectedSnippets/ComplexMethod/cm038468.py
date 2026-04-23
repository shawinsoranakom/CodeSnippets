def post_process_device_kv_on_receive(
        self,
        block_size_ratio: int,
        block_ids_list: list[list[int]],
    ):
        """
        Post process device kv cache after receiving from remote.

        3 types of post processing supported:
            * kv_cache_postprocess_layout => convert from HND to NHD
            * kv_cache_postprocess_blksize => convert from small block size
              to large block size
            * kv_cache_postprocess_blksize_and_layout => convert from small
              block size to large block size and convert from HND to NHD

        """
        if len(self.device_kv_caches) == 0:
            return
        assert block_size_ratio >= 1, "Only nP < nD supported currently."
        assert self.transfer_topo is not None
        if self.enable_permute_local_kv and block_size_ratio > 1:
            logger.debug(
                "Post-processing device kv cache on receive by converting "
                "block_size with %sx bigger and permuting layout from HND"
                " to NHD.",
                block_size_ratio,
            )
        elif self.enable_permute_local_kv:
            logger.debug(
                "Post-processing device kv cache on receive by permuting layout"
                "from HND to NHD."
            )
        else:
            logger.debug(
                "Post-processing device kv cache on receive by converting "
                "block_size with %sx bigger.",
                block_size_ratio,
            )

        split_k_and_v = self.transfer_topo.split_k_and_v

        for block_ids in block_ids_list:
            indices = torch.tensor(block_ids, device=self.device_type, dtype=torch.long)

            for _, cache_or_caches in self.device_kv_caches.items():
                cache_list = cache_or_caches if split_k_and_v else [cache_or_caches]
                for cache in cache_list:
                    if self.enable_permute_local_kv and block_size_ratio > 1:
                        kv_postprocess_blksize_and_layout_on_receive(
                            cache, indices, block_size_ratio
                        )
                    elif self.enable_permute_local_kv:
                        kv_postprocess_layout_on_receive(cache, indices)
                    else:
                        kv_postprocess_blksize_on_receive(
                            cache, indices, block_size_ratio
                        )