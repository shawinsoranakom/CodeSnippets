def test_get_data() -> None:
        """ Test get_data function works """
        session_id = 1

        cache = _Cache()
        assert cache.get_data(session_id, "loss") is None
        assert cache.get_data(session_id, "timestamps") is None

        labels = ['label1', 'label2']
        data = {1: EventData(3., [5., 6.]), 2: EventData(4., [7., 8.])}
        expected_timestamps = np.array([3., 4.])
        expected_loss = np.array([[5., 6.], [7., 8.]])

        cache.cache_data(session_id, data, labels, is_live=False)
        get_timestamps = cache.get_data(session_id, "timestamps")
        get_loss = cache.get_data(session_id, "loss")

        assert isinstance(get_timestamps, dict)
        assert len(get_timestamps) == 1
        assert list(get_timestamps) == [session_id]
        result = get_timestamps[session_id]
        assert list(result) == ["timestamps"]
        np.testing.assert_array_equal(result["timestamps"], expected_timestamps)

        assert isinstance(get_loss, dict)
        assert len(get_loss) == 1
        assert list(get_loss) == [session_id]
        result = get_loss[session_id]
        assert list(result) == ["loss", "labels"]
        np.testing.assert_array_equal(result["loss"], expected_loss)