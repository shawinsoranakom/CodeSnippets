def test_constants_get_warp(size: int, batch_size: int, mocker: pytest_mock.MockerFixture) -> None:
    """ Test ConstantsAugmentation._get_warp works as expected """
    warp_lm_mock = mocker.patch(
        f"{MODULE_PREFIX}.ConstantsAugmentation._get_warp_to_landmarks",
        return_value=((np.random.random((batch_size, 8, 2)) * 100).astype("int32"),
                      (np.random.random((2, size, size))).astype("float32")))
    warp_pad = int(1.25 * size)

    warps = ConstantsAugmentation._get_warp(size, batch_size)

    warp_lm_mock.assert_called_once_with(size, batch_size)

    assert isinstance(warps, ConstantsWarp)

    assert isinstance(warps.maps, np.ndarray)
    assert warps.maps.dtype == "float32"
    assert warps.maps.shape == (batch_size, 2, 5, 5)
    assert warps.maps.min() == 0.
    assert warps.maps.mean() == size / 2.
    assert warps.maps.max() == size

    assert isinstance(warps.pad, tuple)
    assert len(warps.pad) == 2
    assert all(isinstance(x, int) for x in warps.pad)
    assert all(x == warp_pad for x in warps.pad)

    assert isinstance(warps.slices, slice)
    assert warps.slices.step is None
    assert warps.slices.start == warp_pad // 10
    assert warps.slices.stop == -warp_pad // 10

    assert isinstance(warps.scale, float)
    assert warps.scale == 5 / 256 * size

    assert isinstance(warps.lm_edge_anchors, np.ndarray)
    assert warps.lm_edge_anchors.dtype == warp_lm_mock.return_value[0].dtype
    assert warps.lm_edge_anchors.shape == warp_lm_mock.return_value[0].shape
    assert np.all(warps.lm_edge_anchors == warp_lm_mock.return_value[0])

    assert isinstance(warps.lm_grids, np.ndarray)
    assert warps.lm_grids.dtype == warp_lm_mock.return_value[1].dtype
    assert warps.lm_grids.shape == warp_lm_mock.return_value[1].shape
    assert np.all(warps.lm_grids == warp_lm_mock.return_value[1])

    assert isinstance(warps.lm_scale, float)
    assert warps.lm_scale == 2 / 256 * size