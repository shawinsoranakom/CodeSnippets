async def test_delete_metadata_duplicates_many(
    async_test_recorder: RecorderInstanceContextManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test removal of duplicated statistics."""
    module = "tests.components.recorder.db_schema_28"
    importlib.import_module(module)
    old_db_schema = sys.modules[module]

    external_energy_metadata_1 = {
        "has_mean": False,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import_tariff_1",
        "unit_of_measurement": "kWh",
    }
    external_energy_metadata_2 = {
        "has_mean": False,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import_tariff_2",
        "unit_of_measurement": "kWh",
    }
    external_co2_metadata = {
        "has_mean": True,
        "has_sum": False,
        "name": "Fossil percentage",
        "source": "test",
        "statistic_id": "test:fossil_percentage",
        "unit_of_measurement": "%",
    }

    def add_statistics_meta(hass: HomeAssistant) -> None:
        with session_scope(hass=hass) as session:
            session.add(
                recorder.db_schema.StatisticsMeta.from_meta(external_energy_metadata_1)
            )
            for _ in range(1100):
                session.add(
                    recorder.db_schema.StatisticsMeta.from_meta(
                        external_energy_metadata_1
                    )
                )
            session.add(
                recorder.db_schema.StatisticsMeta.from_meta(external_energy_metadata_2)
            )
            session.add(
                recorder.db_schema.StatisticsMeta.from_meta(external_energy_metadata_2)
            )
            session.add(
                recorder.db_schema.StatisticsMeta.from_meta(external_co2_metadata)
            )
            session.add(
                recorder.db_schema.StatisticsMeta.from_meta(external_co2_metadata)
            )

    def get_statistics_meta(hass: HomeAssistant) -> list:
        with session_scope(hass=hass, read_only=True) as session:
            return list(session.query(recorder.db_schema.StatisticsMeta).all())

    # Create some duplicated statistics with schema version 28
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
            "homeassistant.components.recorder.core.create_engine",
            new=_create_engine_28,
        ),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass),
        ):
            await async_wait_recording_done(hass)
            await async_wait_recording_done(hass)

            instance = recorder.get_instance(hass)
            await instance.async_add_executor_job(add_statistics_meta, hass)

            await hass.async_stop()

    # Test that the duplicates are removed during migration from schema 28
    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass),
    ):
        await hass.async_start()
        await async_wait_recording_done(hass)
        await async_wait_recording_done(hass)

        assert "Deleted 1102 duplicated statistics_meta rows" in caplog.text
        instance = recorder.get_instance(hass)
        tmp = await instance.async_add_executor_job(get_statistics_meta, hass)
        assert len(tmp) == 3
        assert tmp[0].id == 1101
        assert tmp[0].statistic_id == "test:total_energy_import_tariff_1"
        assert tmp[1].id == 1103
        assert tmp[1].statistic_id == "test:total_energy_import_tariff_2"
        assert tmp[2].id == 1105
        assert tmp[2].statistic_id == "test:fossil_percentage"

        await hass.async_stop()