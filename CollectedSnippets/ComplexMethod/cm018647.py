def mock_browse_by_idstring(
    search_type: str, idstring: str, start=0, max_items=100, full_album_art_uri=False
) -> list[MockMusicServiceItem]:
    """Mock the call to browse_by_id_string."""
    if search_type == "album_artists" and idstring == "A:ALBUMARTIST/Beatles":
        return [
            MockMusicServiceItem(
                "All",
                idstring + "/",
                idstring,
                "object.container.playlistContainer.sameArtist",
            ),
            MockMusicServiceItem(
                "A Hard Day's Night",
                "A:ALBUMARTIST/Beatles/A%20Hard%20Day's%20Night",
                idstring,
                "object.container.album.musicAlbum",
            ),
            MockMusicServiceItem(
                "Abbey Road",
                "A:ALBUMARTIST/Beatles/Abbey%20Road",
                idstring,
                "object.container.album.musicAlbum",
            ),
        ]
    # browse_by_id_string works with URL encoded or decoded strings
    if search_type == "genres" and idstring in (
        "A:GENRE/Classic%20Rock",
        "A:GENRE/Classic Rock",
    ):
        return [
            MockMusicServiceItem(
                "All",
                "A:GENRE/Classic%20Rock/",
                "A:GENRE/Classic%20Rock",
                "object.container.albumlist",
            ),
            MockMusicServiceItem(
                "Bruce Springsteen",
                "A:GENRE/Classic%20Rock/Bruce%20Springsteen",
                "A:GENRE/Classic%20Rock",
                "object.container.person.musicArtist",
            ),
            MockMusicServiceItem(
                "Cream",
                "A:GENRE/Classic%20Rock/Cream",
                "A:GENRE/Classic%20Rock",
                "object.container.person.musicArtist",
            ),
        ]
    if search_type == "composers" and idstring in (
        "A:COMPOSER/Carlos%20Santana",
        "A:COMPOSER/Carlos Santana",
    ):
        return [
            MockMusicServiceItem(
                "All",
                "A:COMPOSER/Carlos%20Santana/",
                "A:COMPOSER/Carlos%20Santana",
                "object.container.playlistContainer.sameArtist",
            ),
            MockMusicServiceItem(
                "Between Good And Evil",
                "A:COMPOSER/Carlos%20Santana/Between%20Good%20And%20Evil",
                "A:COMPOSER/Carlos%20Santana",
                "object.container.album.musicAlbum",
            ),
            MockMusicServiceItem(
                "Sacred Fire",
                "A:COMPOSER/Carlos%20Santana/Sacred%20Fire",
                "A:COMPOSER/Carlos%20Santana",
                "object.container.album.musicAlbum",
            ),
        ]
    if search_type == "tracks":
        return list_from_json_fixture("music_library_tracks.json")
    if search_type == "albums" and idstring == "A:ALBUM":
        return list_from_json_fixture("music_library_albums.json")
    if search_type == SONOS_SHARE and idstring == "S:":
        return [
            MockMusicServiceItem(
                None,
                "S://192.168.1.1/music",
                "S:",
                "object.container",
            )
        ]
    if search_type == SONOS_SHARE and idstring == "S://192.168.1.1/music":
        return [
            MockMusicServiceItem(
                None,
                "S://192.168.1.1/music/beatles",
                "S://192.168.1.1/music",
                "object.container",
            ),
            MockMusicServiceItem(
                None,
                "S://192.168.1.1/music/elton%20john",
                "S://192.168.1.1/music",
                "object.container",
            ),
        ]
    if search_type == SONOS_SHARE and idstring == "S://192.168.1.1/music/elton%20john":
        return [
            MockMusicServiceItem(
                None,
                "S://192.168.1.1/music/elton%20john/Greatest%20Hits",
                "S://192.168.1.1/music/elton%20john",
                "object.container",
            ),
            MockMusicServiceItem(
                None,
                "S://192.168.1.1/music/elton%20john/Good%20Bye%20Yellow%20Brick%20Road",
                "S://192.168.1.1/music/elton%20john",
                "object.container",
            ),
        ]
    return []