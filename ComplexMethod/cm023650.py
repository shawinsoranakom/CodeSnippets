async def test_statistic_during_period_partial_overlap(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
    frozen_time: datetime.datetime,
) -> None:
    """Test statistic_during_period."""
    client = await hass_ws_client()

    freezer.move_to(frozen_time)
    now = dt_util.utcnow()

    await async_recorder_block_till_done(hass)

    zero = now
    start = zero.replace(hour=0, minute=0, second=0, microsecond=0)

    # Sum shall be tracking a hypothetical sensor that is 0 at midnight, and grows by 1 per minute.
    # The test will have 4 hours of LTS-only data (0:00-3:59:59), followed by 2 hours of overlapping STS/LTS (4:00-5:59:59), followed by 30 minutes of STS only (6:00-6:29:59)
    # similar to how a real recorder might look after purging STS.

    # The datapoint at i=0 (start = 0:00) will be 60 as that is the growth during the hour starting at the start period
    imported_stats_hours = [
        {
            "start": (start + timedelta(hours=i)),
            "min": i * 60,
            "max": i * 60 + 60,
            "mean": i * 60 + 30,
            "sum": (i + 1) * 60,
        }
        for i in range(6)
    ]

    # The datapoint at i=0 (start = 4:00) would be the sensor's value at t=4:05, or 245
    imported_stats_5min = [
        {
            "start": (start + timedelta(hours=4, minutes=5 * i)),
            "min": 4 * 60 + i * 5,
            "max": 4 * 60 + i * 5 + 5,
            "mean": 4 * 60 + i * 5 + 2.5,
            "sum": 4 * 60 + (i + 1) * 5,
        }
        for i in range(30)
    ]

    assert imported_stats_hours[-1]["sum"] == 360
    assert imported_stats_hours[-1]["start"] == start.replace(
        hour=5, minute=0, second=0, microsecond=0
    )
    assert imported_stats_5min[-1]["sum"] == 390
    assert imported_stats_5min[-1]["start"] == start.replace(
        hour=6, minute=25, second=0, microsecond=0
    )

    statId = "sensor.test_overlapping"
    imported_metadata = {
        "has_sum": True,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "name": "Total imported energy overlapping",
        "source": "recorder",
        "statistic_id": statId,
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    recorder.get_instance(hass).async_import_statistics(
        imported_metadata,
        imported_stats_hours,
        Statistics,
    )
    recorder.get_instance(hass).async_import_statistics(
        imported_metadata,
        imported_stats_5min,
        StatisticsShortTerm,
    )
    await async_wait_recording_done(hass)

    metadata = get_metadata(hass, statistic_ids={statId})
    metadata_id = metadata[statId][0]
    run_cache = get_short_term_statistics_run_cache(hass)
    # Verify the import of the short term statistics
    # also updates the run cache
    assert run_cache.get_latest_ids({metadata_id}) is not None

    # Get all the stats, should consider all hours and 5mins
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": statId,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "change": 390,
        "max": 390,
        "min": 0,
        "mean": 195,
    }

    async def assert_stat_during_fixed(client, start_time, end_time, expect):
        json = {
            "type": "recorder/statistic_during_period",
            "types": list(expect.keys()),
            "statistic_id": statId,
            "fixed_period": {},
        }
        if start_time:
            json["fixed_period"]["start_time"] = start_time.isoformat()
        if end_time:
            json["fixed_period"]["end_time"] = end_time.isoformat()

        await client.send_json_auto_id(json)
        response = await client.receive_json()
        assert response["success"]
        assert response["result"] == expect

    # One hours worth of growth in LTS-only
    start_time = start.replace(hour=1)
    end_time = start.replace(hour=2)
    await assert_stat_during_fixed(
        client, start_time, end_time, {"change": 60, "min": 60, "max": 120, "mean": 90}
    )

    # Five minutes of growth in STS-only
    start_time = start.replace(hour=6, minute=15)
    end_time = start.replace(hour=6, minute=20)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 5,
            "min": 6 * 60 + 15,
            "max": 6 * 60 + 20,
            "mean": 6 * 60 + (15 + 20) / 2,
        },
    )

    # Six minutes of growth in STS-only
    start_time = start.replace(hour=6, minute=14)
    end_time = start.replace(hour=6, minute=20)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 5,
            "min": 6 * 60 + 15,
            "max": 6 * 60 + 20,
            "mean": 6 * 60 + (15 + 20) / 2,
        },
    )

    # Six minutes of growth in STS-only
    # 5-minute Change includes start times exactly on or before a statistics start, but end times are not counted unless they are greater than start.
    start_time = start.replace(hour=6, minute=15)
    end_time = start.replace(hour=6, minute=21)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 10,
            "min": 6 * 60 + 15,
            "max": 6 * 60 + 25,
            "mean": 6 * 60 + (15 + 25) / 2,
        },
    )

    # Five minutes of growth in overlapping LTS+STS
    start_time = start.replace(hour=5, minute=15)
    end_time = start.replace(hour=5, minute=20)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 5,
            "min": 5 * 60 + 15,
            "max": 5 * 60 + 20,
            "mean": 5 * 60 + (15 + 20) / 2,
        },
    )

    # Five minutes of growth in overlapping LTS+STS (start of hour)
    start_time = start.replace(hour=5, minute=0)
    end_time = start.replace(hour=5, minute=5)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 5, "min": 5 * 60, "max": 5 * 60 + 5, "mean": 5 * 60 + (5) / 2},
    )

    # Five minutes of growth in overlapping LTS+STS (end of hour)
    start_time = start.replace(hour=4, minute=55)
    end_time = start.replace(hour=5, minute=0)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 5,
            "min": 4 * 60 + 55,
            "max": 5 * 60,
            "mean": 4 * 60 + (55 + 60) / 2,
        },
    )

    # Five minutes of growth in STS-only, with a minute offset. Despite that this does not cover the full period, result is still 5
    start_time = start.replace(hour=6, minute=16)
    end_time = start.replace(hour=6, minute=21)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 5,
            "min": 6 * 60 + 20,
            "max": 6 * 60 + 25,
            "mean": 6 * 60 + (20 + 25) / 2,
        },
    )

    # 7 minutes of growth in STS-only, spanning two intervals
    start_time = start.replace(hour=6, minute=14)
    end_time = start.replace(hour=6, minute=21)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 10,
            "min": 6 * 60 + 15,
            "max": 6 * 60 + 25,
            "mean": 6 * 60 + (15 + 25) / 2,
        },
    )

    # One hours worth of growth in LTS-only, with arbitrary minute offsets
    # Since this does not fully cover the hour, result is None?
    start_time = start.replace(hour=1, minute=40)
    end_time = start.replace(hour=2, minute=12)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": None, "min": None, "max": None, "mean": None},
    )

    # One hours worth of growth in LTS-only, with arbitrary minute offsets, covering a whole 1-hour period
    start_time = start.replace(hour=1, minute=40)
    end_time = start.replace(hour=3, minute=12)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 60, "min": 120, "max": 180, "mean": 150},
    )

    # 90 minutes of growth in window overlapping LTS+STS/STS-only (4:41 - 6:11)
    start_time = start.replace(hour=4, minute=41)
    end_time = start_time + timedelta(minutes=90)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {
            "change": 90,
            "min": 4 * 60 + 45,
            "max": 4 * 60 + 45 + 90,
            "mean": 4 * 60 + 45 + 45,
        },
    )

    # 4 hours of growth in overlapping LTS-only/LTS+STS (2:01-6:01)
    start_time = start.replace(hour=2, minute=1)
    end_time = start_time + timedelta(minutes=240)
    # 60 from LTS (3:00-3:59), 125 from STS (25 intervals) (4:00-6:01)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 185, "min": 3 * 60, "max": 3 * 60 + 185, "mean": 3 * 60 + 185 / 2},
    )

    # 4 hours of growth in overlapping LTS-only/LTS+STS (1:31-5:31)
    start_time = start.replace(hour=1, minute=31)
    end_time = start_time + timedelta(minutes=240)
    # 120 from LTS (2:00-3:59), 95 from STS (19 intervals) 4:00-5:31
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 215, "min": 2 * 60, "max": 2 * 60 + 215, "mean": 2 * 60 + 215 / 2},
    )

    # 5 hours of growth, start time only (1:31-end)
    start_time = start.replace(hour=1, minute=31)
    end_time = None
    # will be actually 2:00 - end
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 4 * 60 + 30, "min": 120, "max": 390, "mean": (390 + 120) / 2},
    )

    # 5 hours of growth, end_time_only (0:00-5:00)
    start_time = None
    end_time = start.replace(hour=5)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 5 * 60, "min": 0, "max": 5 * 60, "mean": (5 * 60) / 2},
    )

    # 5 hours 1 minute of growth, end_time_only (0:00-5:01)
    start_time = None
    end_time = start.replace(hour=5, minute=1)
    # 4 hours LTS, 1 hour and 5 minutes STS (4:00-5:01)
    await assert_stat_during_fixed(
        client,
        start_time,
        end_time,
        {"change": 5 * 60 + 5, "min": 0, "max": 5 * 60 + 5, "mean": (5 * 60 + 5) / 2},
    )