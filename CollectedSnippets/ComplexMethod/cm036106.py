def test_multimodal_kwargs():
    e1 = MultiModalFieldElem(
        torch.zeros(1000, dtype=torch.bfloat16),
        MultiModalBatchedField(),
    )
    e2 = MultiModalFieldElem(
        [torch.zeros(1000, dtype=torch.int8) for _ in range(4)],
        MultiModalFlatField(
            slices=[[slice(1, 2, 3), slice(4, 5, 6)], [slice(None, 2)]],
            dim=0,
        ),
    )
    e3 = MultiModalFieldElem(
        torch.zeros(1000, dtype=torch.int32),
        MultiModalSharedField(batch_size=4),
    )
    e4 = MultiModalFieldElem(
        torch.zeros(1000, dtype=torch.int32),
        MultiModalFlatField(slices=[slice(1, 2, 3), slice(4, 5, 6)], dim=2),
    )
    mm = MultiModalKwargsItems(
        {
            "audio": [MultiModalKwargsItem({"a0": e1})],
            "video": [MultiModalKwargsItem({"v0": e2})],
            "image": [MultiModalKwargsItem({"i0": e3, "i1": e4})],
        }
    )

    # pack mm kwargs into a mock request so that it can be decoded properly
    req = MyRequest([mm])

    encoder = MsgpackEncoder()
    decoder = MsgpackDecoder(MyRequest)

    encoded = encoder.encode(req)

    assert len(encoded) == 8

    total_len = sum(memoryview(x).cast("B").nbytes for x in encoded)

    # expected total encoding length, should be 14319, +-20 for minor changes
    assert 14300 <= total_len <= 14340
    decoded = decoder.decode(encoded).mm[0]
    assert isinstance(decoded, MultiModalKwargsItems)

    # check all modalities were recovered and do some basic sanity checks
    assert len(decoded) == 3
    images = decoded["image"]
    assert len(images) == 1
    assert len(images[0].items()) == 2
    assert list(images[0].keys()) == ["i0", "i1"]

    # check the tensor contents and layout in the main dict
    mm_data = mm.get_data()
    decoded_data = decoded.get_data()
    assert all(nested_equal(mm_data[k], decoded_data[k]) for k in mm_data)