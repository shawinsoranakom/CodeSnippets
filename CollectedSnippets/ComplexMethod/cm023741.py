async def test_delete_duplicates_many(
    async_test_recorder: RecorderInstanceContextManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test removal of duplicated statistics.

    The test only works with SQLite.
    """
    importlib.import_module(SCHEMA_MODULE)
    old_db_schema = sys.modules[SCHEMA_MODULE]

    period1 = dt_util.as_utc(dt_util.parse_datetime("2021-09-01 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2021-09-30 23:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2021-10-01 00:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2021-10-31 23:00:00"))

    external_energy_statistics_1 = (
        {
            "start": period1,
            "last_reset": None,
            "state": 0,
            "sum": 2,
        },
        {
            "start": period2,
            "last_reset": None,
            "state": 1,
            "sum": 3,
        },
        {
            "start": period3,
            "last_reset": None,
            "state": 2,
            "sum": 4,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 5,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 5,
        },
    )
    external_energy_metadata_1 = {
        "has_mean": False,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import_tariff_1",
        "unit_of_measurement": "kWh",
    }
    external_energy_statistics_2 = (
        {
            "start": period1,
            "last_reset": None,
            "state": 0,
            "sum": 20,
        },
        {
            "start": period2,
            "last_reset": None,
            "state": 1,
            "sum": 30,
        },
        {
            "start": period3,
            "last_reset": None,
            "state": 2,
            "sum": 40,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 50,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 50,
        },
    )
    external_energy_metadata_2 = {
        "has_mean": False,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import_tariff_2",
        "unit_of_measurement": "kWh",
    }
    external_co2_statistics = (
        {
            "start": period1,
            "last_reset": None,
            "mean": 10,
        },
        {
            "start": period2,
            "last_reset": None,
            "mean": 30,
        },
        {
            "start": period3,
            "last_reset": None,
            "mean": 60,
        },
        {
            "start": period4,
            "last_reset": None,
            "mean": 90,
        },
    )
    external_co2_metadata = {
        "has_mean": True,
        "has_sum": False,
        "name": "Fossil percentage",
        "source": "test",
        "statistic_id": "test:fossil_percentage",
        "unit_of_measurement": "%",
    }

    # Create some duplicated statistics with schema version 23
    with (
        patch.object(recorder, "db_schema", old_db_schema),
        patch.object(
            recorder.migration, "SCHEMA_VERSION", old_db_schema.SCHEMA_VERSION
        ),
        patch.object(
            recorder.migration,
            "LIVE_MIGRATION_MIN_SCHEMA_VERSION",
            get_patched_live_version(old_db_schema),
        ),
        patch.object(
            recorder.migration, "non_live_data_migration_needed", return_value=False
        ),
        patch(
            CREATE_ENGINE_TARGET,
            new=partial(
                create_engine_test_for_schema_version_postfix,
                schema_version_postfix=SCHEMA_VERSION_POSTFIX,
            ),
        ),
    ):
        async with async_test_home_assistant() as hass, async_test_recorder(hass):
            get_instance(hass).recorder_and_worker_thread_ids.add(threading.get_ident())
            await async_wait_recording_done(hass)
            await async_wait_recording_done(hass)

            with session_scope(hass=hass) as session:
                session.add(
                    recorder.db_schema.StatisticsMeta.from_meta(
                        external_energy_metadata_1
                    )
                )
                session.add(
                    recorder.db_schema.StatisticsMeta.from_meta(
                        external_energy_metadata_2
                    )
                )
                session.add(
                    recorder.db_schema.StatisticsMeta.from_meta(external_co2_metadata)
                )
            with session_scope(hass=hass) as session:
                for stat in external_energy_statistics_1:
                    session.add(recorder.db_schema.Statistics.from_stats(1, stat))
                for _ in range(3000):
                    session.add(
                        recorder.db_schema.Statistics.from_stats(
                            1, external_energy_statistics_1[-1]
                        )
                    )
                for stat in external_energy_statistics_2:
                    session.add(recorder.db_schema.Statistics.from_stats(2, stat))
                for stat in external_co2_statistics:
                    session.add(recorder.db_schema.Statistics.from_stats(3, stat))

            await hass.async_stop()

    # Test that the duplicates are removed during migration from schema 23
    async with async_test_home_assistant() as hass, async_test_recorder(hass):
        await hass.async_start()
        await async_wait_recording_done(hass)
        await async_wait_recording_done(hass)
        await hass.async_stop()

    assert "Deleted 3002 duplicated statistics rows" in caplog.text
    assert "Found non identical" not in caplog.text
    assert "Found duplicated" not in caplog.text