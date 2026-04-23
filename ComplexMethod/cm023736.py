async def test_stats_migrate_times(
    async_test_recorder: RecorderInstanceContextManager,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we can migrate times in the statistics tables."""
    importlib.import_module(SCHEMA_MODULE_32)
    old_db_schema = sys.modules[SCHEMA_MODULE_32]
    now = dt_util.utcnow()
    now_timestamp = now.timestamp()

    statistics_kwargs = {
        "created": now,
        "mean": 0,
        "metadata_id": 1,
        "min": 0,
        "max": 0,
        "last_reset": now,
        "start": now,
        "state": 0,
        "sum": 0,
    }
    mock_metadata = old_db_schema.StatisticMetaData(
        has_mean=False,
        has_sum=False,
        name="Test",
        source="sensor",
        statistic_id="sensor.test",
        unit_of_measurement="cats",
    )
    number_of_migrations = 5

    def _get_index_names(table):
        with session_scope(hass=hass) as session:
            return inspect(session.connection()).get_indexes(table)

    with (
        patch.object(recorder, "db_schema", old_db_schema),
        patch.object(migration, "SCHEMA_VERSION", old_db_schema.SCHEMA_VERSION),
        patch.object(
            migration,
            "LIVE_MIGRATION_MIN_SCHEMA_VERSION",
            get_patched_live_version(old_db_schema),
        ),
        patch.object(migration, "non_live_data_migration_needed", return_value=False),
        patch(CREATE_ENGINE_TARGET, new=_create_engine_test),
    ):
        async with (
            async_test_home_assistant() as hass,
            async_test_recorder(hass) as instance,
        ):
            await hass.async_block_till_done()
            await async_wait_recording_done(hass)
            await async_wait_recording_done(hass)

            def _add_data():
                with session_scope(hass=hass) as session:
                    session.add(old_db_schema.StatisticsMeta.from_meta(mock_metadata))
                with session_scope(hass=hass) as session:
                    session.add(old_db_schema.Statistics(**statistics_kwargs))
                    session.add(old_db_schema.StatisticsShortTerm(**statistics_kwargs))

            await instance.async_add_executor_job(_add_data)
            await hass.async_block_till_done()
            await instance.async_block_till_done()

            statistics_indexes = await instance.async_add_executor_job(
                _get_index_names, "statistics"
            )
            statistics_short_term_indexes = await instance.async_add_executor_job(
                _get_index_names, "statistics_short_term"
            )
            statistics_index_names = {index["name"] for index in statistics_indexes}
            statistics_short_term_index_names = {
                index["name"] for index in statistics_short_term_indexes
            }

            await hass.async_stop()
            await hass.async_block_till_done()

    assert "ix_statistics_statistic_id_start" in statistics_index_names
    assert (
        "ix_statistics_short_term_statistic_id_start"
        in statistics_short_term_index_names
    )

    # Test that the times are migrated during migration from schema 32
    async with (
        async_test_home_assistant() as hass,
        async_test_recorder(hass) as instance,
    ):
        await hass.async_block_till_done()

        # We need to wait for all the migration tasks to complete
        # before we can check the database.
        for _ in range(number_of_migrations):
            await instance.async_block_till_done()
            await async_wait_recording_done(hass)

        def _get_test_data_from_db():
            with session_scope(hass=hass) as session:
                statistics_result = list(
                    session.query(recorder.db_schema.Statistics)
                    .join(
                        recorder.db_schema.StatisticsMeta,
                        recorder.db_schema.Statistics.metadata_id
                        == recorder.db_schema.StatisticsMeta.id,
                    )
                    .where(
                        recorder.db_schema.StatisticsMeta.statistic_id == "sensor.test"
                    )
                )
                statistics_short_term_result = list(
                    session.query(recorder.db_schema.StatisticsShortTerm)
                    .join(
                        recorder.db_schema.StatisticsMeta,
                        recorder.db_schema.StatisticsShortTerm.metadata_id
                        == recorder.db_schema.StatisticsMeta.id,
                    )
                    .where(
                        recorder.db_schema.StatisticsMeta.statistic_id == "sensor.test"
                    )
                )
                session.expunge_all()
                return statistics_result, statistics_short_term_result

        (
            statistics_result,
            statistics_short_term_result,
        ) = await instance.async_add_executor_job(_get_test_data_from_db)

        for results in (statistics_result, statistics_short_term_result):
            assert len(results) == 1
            assert results[0].created is None
            assert results[0].created_ts == now_timestamp
            assert results[0].last_reset is None
            assert results[0].last_reset_ts == now_timestamp
            assert results[0].start is None
            assert results[0].start_ts == now_timestamp

        statistics_indexes = await instance.async_add_executor_job(
            _get_index_names, "statistics"
        )
        statistics_short_term_indexes = await instance.async_add_executor_job(
            _get_index_names, "statistics_short_term"
        )
        statistics_index_names = {index["name"] for index in statistics_indexes}
        statistics_short_term_index_names = {
            index["name"] for index in statistics_short_term_indexes
        }

        assert "ix_statistics_statistic_id_start" not in statistics_index_names
        assert (
            "ix_statistics_short_term_statistic_id_start"
            not in statistics_short_term_index_names
        )

        await hass.async_stop()