async def test_ll_hls_stream(
    hass: HomeAssistant, hls_stream, stream_worker_sync
) -> None:
    """Test hls stream.

    Purposefully not mocking anything here to test full
    integration with the stream component.
    """
    await async_setup_component(
        hass,
        "stream",
        {
            "stream": {
                CONF_LL_HLS: True,
                CONF_SEGMENT_DURATION: SEGMENT_DURATION,
                # Use a slight mismatch in PART_DURATION to mimic
                # misalignments with source DTSs
                CONF_PART_DURATION: TEST_PART_DURATION - 0.01,
            }
        },
    )

    stream_worker_sync.pause()

    num_playlist_segments = 3
    # Setup demo HLS track
    source = generate_h264_video(duration=num_playlist_segments * SEGMENT_DURATION + 2)
    stream = create_stream(hass, source, {}, dynamic_stream_settings())

    # Request stream
    stream.add_provider(HLS_PROVIDER)
    await stream.start()

    hls_client = await hls_stream(stream)

    # Fetch playlist
    master_playlist_response = await hls_client.get()
    assert master_playlist_response.status == HTTPStatus.OK

    # Fetch init
    master_playlist = await master_playlist_response.text()
    init_response = await hls_client.get("/init.mp4")
    assert init_response.status == HTTPStatus.OK

    # Fetch playlist
    playlist_url = "/" + master_playlist.splitlines()[-1]
    playlist_response = await hls_client.get(
        playlist_url + f"?_HLS_msn={num_playlist_segments - 1}"
    )
    assert playlist_response.status == HTTPStatus.OK

    # Fetch segments
    playlist = await playlist_response.text()
    segment_re = re.compile(r"^(?P<segment_url>./segment/\d+\.m4s)")
    for line in playlist.splitlines():
        match = segment_re.match(line)
        if match:
            segment_url = "/" + match.group("segment_url")
            segment_response = await hls_client.get(segment_url)
            assert segment_response.status == HTTPStatus.OK

    def check_part_is_moof_mdat(data: bytes):
        if len(data) < 8 or data[4:8] != b"moof":
            return False
        moof_length = int.from_bytes(data[0:4], byteorder="big")
        if (
            len(data) < moof_length + 8
            or data[moof_length + 4 : moof_length + 8] != b"mdat"
        ):
            return False
        mdat_length = int.from_bytes(
            data[moof_length : moof_length + 4], byteorder="big"
        )
        if mdat_length + moof_length != len(data):
            return False
        return True

    # Parse playlist
    part_re = re.compile(
        r'#EXT-X-PART:DURATION=(?P<part_duration>[0-9]{1,}.[0-9]{3,}),URI="(?P<part_url>.+?)"(,INDEPENDENT=YES)?'
    )
    datetime_re = re.compile(r"#EXT-X-PROGRAM-DATE-TIME:(?P<datetime>.+)")
    inf_re = re.compile(r"#EXTINF:(?P<segment_duration>[0-9]{1,}.[0-9]{3,}),")
    # keep track of which tests were done (indexed by re)
    tested = dict.fromkeys((part_re, datetime_re, inf_re), False)
    # keep track of times and durations along playlist for checking consistency
    part_durations = []
    segment_duration = 0
    datetimes = deque()
    for line in playlist.splitlines():
        match = part_re.match(line)
        if match:
            # Fetch all completed part segments
            part_durations.append(float(match.group("part_duration")))
            part_segment_url = "/" + match.group("part_url")
            part_segment_response = await hls_client.get(
                part_segment_url,
            )
            assert part_segment_response.status == HTTPStatus.OK
            assert check_part_is_moof_mdat(await part_segment_response.read())
            tested[part_re] = True
            continue
        match = datetime_re.match(line)
        if match:
            datetimes.append(parser.parse(match.group("datetime")))
            # Check that segment durations are consistent with PROGRAM-DATE-TIME
            if len(datetimes) > 1:
                datetime_duration = (
                    datetimes[-1] - datetimes.popleft()
                ).total_seconds()
                if segment_duration:
                    assert math.isclose(
                        datetime_duration, segment_duration, rel_tol=1e-3
                    )
                    tested[datetime_re] = True
            continue
        match = inf_re.match(line)
        if match:
            segment_duration = float(match.group("segment_duration"))
            # Check that segment durations are consistent with part durations
            if len(part_durations) > 1:
                assert math.isclose(sum(part_durations), segment_duration, rel_tol=1e-3)
                tested[inf_re] = True
                part_durations.clear()
    # make sure all playlist tests were performed
    assert all(tested.values())

    stream_worker_sync.resume()

    # Stop stream, if it hasn't quit already
    await stream.stop()

    # Ensure playlist not accessible after stream ends
    fail_response = await hls_client.get()
    assert fail_response.status == HTTPStatus.NOT_FOUND