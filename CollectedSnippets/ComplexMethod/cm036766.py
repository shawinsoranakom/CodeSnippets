def _assert_mm_uuids(
    mm_uuids: MultiModalUUIDDict | None,
    media_count: int,
    expected_uuids: list[str | None],
    modality: str = "image",
) -> None:
    if len(expected_uuids) > 0:
        assert mm_uuids is not None
        assert modality in mm_uuids

        image_uuids = mm_uuids.get(modality)
        assert image_uuids is not None

        assert isinstance(image_uuids, list) and len(image_uuids) == media_count

        assert image_uuids == expected_uuids
    else:
        assert mm_uuids is None