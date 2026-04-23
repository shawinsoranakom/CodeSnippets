def _assert_mm_data_inputs(
    mm_data: MultiModalDataDict | None,
    data_count: MultiModalDataCounts,
    skipped_media_indices: dict[str, list] | None = None,  # modality -> list[int]
) -> None:
    assert mm_data is not None
    assert set(data_count.keys()) == (set(mm_data.keys()))

    for modality, n in data_count.items():
        modality_data = mm_data.get(modality)
        assert modality_data is not None
        assert isinstance(modality_data, list) and len(modality_data) == n

        if skipped_media_indices is not None:
            skipped_media_indices_for_modality = skipped_media_indices.get(modality)
            assert skipped_media_indices_for_modality is not None
            for i in skipped_media_indices_for_modality:
                assert modality_data[i] is None