def _get_cache_missing_items(
        self,
        cache: BaseMultiModalProcessorCache,
        mm_data_items: MultiModalDataItems,
        mm_hashes: MultiModalHashes,
    ) -> tuple[MultiModalIsCached, MultiModalDataItems]:
        mm_is_cached = {
            modality: cache.is_cached(hashes) for modality, hashes in mm_hashes.items()
        }

        mm_missing_idxs = {
            modality: [
                idx
                for idx, item_is_cached in enumerate(items_is_cached)
                if not item_is_cached
            ]
            for modality, items_is_cached in mm_is_cached.items()
        }

        mm_missing_data = {}
        for modality, idxs in mm_missing_idxs.items():
            missing_modality_data = []
            for idx in idxs:
                data = mm_data_items[modality][idx]
                if data is None:
                    raise ValueError(
                        f"Cache miss for {modality} at index {idx} "
                        f"but data is not provided."
                    )
                else:
                    missing_modality_data.append(data)
            mm_missing_data[modality] = missing_modality_data

        mm_missing_items = self.info.parse_mm_data(mm_missing_data, validate=False)

        return mm_is_cached, mm_missing_items