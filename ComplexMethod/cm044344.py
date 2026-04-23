def test_constants_get_warp_to_landmarks(size: int, batch_size: int) -> None:
    """ Test ConstantsAugmentation._get_warp_to_landmarks works as expected """
    anchors, grids = ConstantsAugmentation._get_warp_to_landmarks(size, batch_size)
    assert isinstance(anchors, np.ndarray)
    assert isinstance(grids, np.ndarray)

    assert anchors.dtype == np.int32
    assert anchors.shape == (batch_size, 8, 2)
    assert anchors.min() == 0
    assert anchors.max() == size - 1

    assert grids.dtype == np.float32
    assert grids.shape == (2, size, size)
    assert grids.min() == 0.
    assert grids.max() == size - 1