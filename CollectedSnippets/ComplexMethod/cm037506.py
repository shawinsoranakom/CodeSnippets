def _validate_mm_uuids(
        self,
        mm_data: MultiModalDataDict,
        mm_data_items: MultiModalDataItems,
        mm_uuid_items: MultiModalUUIDItems,
    ) -> None:
        # NOTE: Keys corresponding to `None` in `mm_data` don't appear in
        # `mm_data_items`
        modalities = mm_data.keys() | mm_uuid_items.keys()

        for modality in modalities:
            data_items = mm_data_items.get(modality)
            uuid_items = mm_uuid_items.get(modality)

            if data_items is None:
                if uuid_items is None:
                    raise ValueError(
                        f"multi_modal_data[{modality!r}] is empty but "
                        f"multi_modal_uuids[{modality!r}] is missing."
                    )

            elif uuid_items is not None:
                if len(data_items) != len(uuid_items):
                    raise ValueError(
                        f"If given, multi_modal_uuids[{modality!r}] must have "
                        f"same length as multi_modal_data[{modality!r}], but "
                        f"got {len(uuid_items)} vs {len(data_items)}."
                    )

                for i, item in enumerate(data_items):
                    if item is None and uuid_items[i] is None:
                        raise ValueError(
                            f"multi_modal_data[{modality!r}][{i}] is empty but "
                            f"multi_modal_uuids[{modality!r}][{i}] is missing."
                        )