async def parse_m3u(hass, url):
    """Very simple m3u parser.

    Based on https://github.com/dvndrsn/M3uParser/blob/master/m3uparser.py
    """
    # From Mozilla gecko source: https://github.com/mozilla/gecko-dev/blob/c4c1adbae87bf2d128c39832d72498550ee1b4b8/dom/media/DecoderTraits.cpp#L47-L52
    hls_content_types = (
        # https://tools.ietf.org/html/draft-pantos-http-live-streaming-19#section-10
        "application/vnd.apple.mpegurl",
        # Additional informal types used by Mozilla gecko not included as they
        # don't reliably indicate HLS streams
    )
    m3u_data = await _fetch_playlist(hass, url, hls_content_types)
    m3u_lines = m3u_data.splitlines()

    playlist = []

    length = None
    title = None

    for line in m3u_lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # Get length and title from #EXTINF line
            info = line.split("#EXTINF:")[1].split(",", 1)
            if len(info) != 2:
                _LOGGER.warning("Ignoring invalid extinf %s in playlist %s", line, url)
                continue
            length = info[0].split(" ", 1)
            title = info[1].strip()
        elif line.startswith(("#EXT-X-VERSION:", "#EXT-X-STREAM-INF:")):
            # HLS stream, supported by cast devices
            raise PlaylistSupported("HLS")
        elif line.startswith("#"):
            # Ignore other extensions
            continue
        elif len(line) != 0:
            # Get song path from all other, non-blank lines
            if not _is_url(line):
                raise PlaylistError(f"Invalid item {line} in playlist {url}")
            playlist.append(PlaylistItem(length=length, title=title, url=line))
            # reset the song variables so it doesn't use the same EXTINF more than once
            length = None
            title = None

    return playlist