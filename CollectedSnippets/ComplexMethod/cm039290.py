def test_config_context():
    assert get_config() == {
        "assume_finite": False,
        "working_memory": 1024,
        "print_changed_only": True,
        "display": "diagram",
        "array_api_dispatch": False,
        "pairwise_dist_chunk_size": 256,
        "enable_cython_pairwise_dist": True,
        "transform_output": "default",
        "enable_metadata_routing": False,
        "skip_parameter_validation": False,
        "sparse_interface": "spmatrix",
    }

    # Not using as a context manager affects nothing
    config_context(assume_finite=True)
    assert get_config()["assume_finite"] is False

    with config_context(assume_finite=True):
        assert get_config() == {
            "assume_finite": True,
            "working_memory": 1024,
            "print_changed_only": True,
            "display": "diagram",
            "array_api_dispatch": False,
            "pairwise_dist_chunk_size": 256,
            "enable_cython_pairwise_dist": True,
            "transform_output": "default",
            "enable_metadata_routing": False,
            "skip_parameter_validation": False,
            "sparse_interface": "spmatrix",
        }
    assert get_config()["assume_finite"] is False

    with config_context(assume_finite=True):
        with config_context(assume_finite=None):
            assert get_config()["assume_finite"] is True

        assert get_config()["assume_finite"] is True

        with config_context(assume_finite=False):
            assert get_config()["assume_finite"] is False

            with config_context(assume_finite=None):
                assert get_config()["assume_finite"] is False

                # global setting will not be retained outside of context that
                # did not modify this setting
                set_config(assume_finite=True)
                assert get_config()["assume_finite"] is True

            assert get_config()["assume_finite"] is False

        assert get_config()["assume_finite"] is True

    assert get_config() == {
        "assume_finite": False,
        "working_memory": 1024,
        "print_changed_only": True,
        "display": "diagram",
        "array_api_dispatch": False,
        "pairwise_dist_chunk_size": 256,
        "enable_cython_pairwise_dist": True,
        "transform_output": "default",
        "enable_metadata_routing": False,
        "skip_parameter_validation": False,
        "sparse_interface": "spmatrix",
    }

    # No positional arguments
    with pytest.raises(TypeError):
        config_context(True)

    # No unknown arguments
    with pytest.raises(TypeError):
        config_context(do_something_else=True).__enter__()