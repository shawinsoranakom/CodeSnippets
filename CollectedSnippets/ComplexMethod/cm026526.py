async def parse_pls(hass, url):
    """Very simple pls parser.

    Based on https://github.com/mariob/plsparser/blob/master/src/plsparser.py
    """
    pls_data = await _fetch_playlist(hass, url, ())

    pls_parser = configparser.ConfigParser()
    try:
        pls_parser.read_string(pls_data, url)
    except configparser.Error as err:
        raise PlaylistError(f"Can't parse playlist {url}") from err

    if (
        _PLS_SECTION_PLAYLIST not in pls_parser
        or pls_parser[_PLS_SECTION_PLAYLIST].getint("Version") != 2
    ):
        raise PlaylistError(f"Invalid playlist {url}")

    try:
        num_entries = pls_parser.getint(_PLS_SECTION_PLAYLIST, "NumberOfEntries")
    except (configparser.NoOptionError, ValueError) as err:
        raise PlaylistError(f"Invalid NumberOfEntries in playlist {url}") from err

    playlist_section = pls_parser[_PLS_SECTION_PLAYLIST]

    playlist = []
    for entry in range(1, num_entries + 1):
        file_option = f"File{entry}"
        if file_option not in playlist_section:
            _LOGGER.warning("Missing %s in pls from %s", file_option, url)
            continue
        item_url = playlist_section[file_option]
        if not _is_url(item_url):
            raise PlaylistError(f"Invalid item {item_url} in playlist {url}")
        playlist.append(
            PlaylistItem(
                length=playlist_section.get(f"Length{entry}"),
                title=playlist_section.get(f"Title{entry}"),
                url=item_url,
            )
        )
    return playlist