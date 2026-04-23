def test_airbyte_global_state():
    destination = _PathwayAirbyteDestination(print, print)
    assert destination._state == {}
    assert destination._shared_state is None
    destination._write(
        "_airbyte_states",
        [
            {
                "_airbyte_raw_id": "4450e616-fb46-458e-aa78-16c1f631dbfb",
                "_airbyte_job_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_slice_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_extracted_at": None,
                "_airbyte_loaded_at": "2024-03-15T16:01:13.809156",
                "_airbyte_data": '{"type": "GLOBAL", "global": {"stream_states": [{"stream_descriptor": {"name": "commits"}, "stream_state": {"pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}}}]}}',  # noqa
            }
        ],
    )
    assert destination._state == {
        "commits": {
            "pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}
        },
    }
    assert destination._shared_state is None
    destination._write(
        "_airbyte_states",
        [
            {
                "_airbyte_raw_id": "4450e616-fb46-458e-aa78-16c1f631dbfb",
                "_airbyte_job_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_slice_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_extracted_at": None,
                "_airbyte_loaded_at": "2024-03-15T16:01:13.809156",
                "_airbyte_data": '{"type": "GLOBAL", "global": {"shared_state": "shared_test", "stream_states": [{"stream_descriptor": {"name": "commits"}, "stream_state": {"pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}}}]}}',  # noqa
            }
        ],
    )
    assert destination._state == {
        "commits": {
            "pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}
        },
    }
    assert destination._shared_state == "shared_test"
    destination._write(
        "_airbyte_states",
        [
            {
                "_airbyte_raw_id": "4450e616-fb46-458e-aa78-16c1f631dbfb",
                "_airbyte_job_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_slice_started_at": "2024-03-15T16:01:07.374909",
                "_airbyte_extracted_at": None,
                "_airbyte_loaded_at": "2024-03-15T16:01:13.809156",
                "_airbyte_data": '{"type": "GLOBAL", "global": {"stream_states": [{"stream_descriptor": {"name": "commits"}, "stream_state": {"pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}}}]}}',  # noqa
            }
        ],
    )
    assert destination._state == {
        "commits": {
            "pathwaycom/pathway": {"main": {"created_at": "2024-08-29T22:00:10Z"}}
        },
    }
    assert destination._shared_state is None