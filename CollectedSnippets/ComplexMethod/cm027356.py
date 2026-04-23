async def get_media_info(media_library, search_id, search_type):
    """Fetch media/album."""
    thumbnail = None
    title = None
    media = None

    properties = ["thumbnail", "art"]
    if search_type == MediaType.ALBUM:
        if search_id:
            album = await media_library.get_album_details(
                album_id=int(search_id), properties=properties
            )
            thumbnail = media_library.thumbnail_url(
                album["albumdetails"]["art"].get(
                    "poster", album["albumdetails"].get("thumbnail")
                )
            )
            title = album["albumdetails"]["label"]
            media = await media_library.get_songs(
                album_id=int(search_id),
                properties=[
                    "albumid",
                    "artist",
                    "duration",
                    "album",
                    "thumbnail",
                    "track",
                    "art",
                ],
            )
            media = media.get("songs")
        else:
            media = await media_library.get_albums(properties=properties)
            media = media.get("albums")
            title = "Albums"

    elif search_type == MediaType.ARTIST:
        if search_id:
            media = await media_library.get_albums(
                artist_id=int(search_id), properties=properties
            )
            media = media.get("albums")
            artist = await media_library.get_artist_details(
                artist_id=int(search_id), properties=properties
            )
            thumbnail = media_library.thumbnail_url(
                artist["artistdetails"]["art"].get(
                    "poster", artist["artistdetails"].get("thumbnail")
                )
            )
            title = artist["artistdetails"]["label"]
        else:
            media = await media_library.get_artists(properties)
            media = media.get("artists")
            title = "Artists"

    elif search_type == "library_music":
        library = {MediaType.ALBUM: "Albums", MediaType.ARTIST: "Artists"}
        media = [{"label": name, "type": type_} for type_, name in library.items()]
        title = "Music Library"

    elif search_type == MediaType.MOVIE:
        if search_id:
            movie = await media_library.get_movie_details(
                movie_id=int(search_id), properties=properties
            )
            thumbnail = media_library.thumbnail_url(
                movie["moviedetails"]["art"].get(
                    "poster", movie["moviedetails"].get("thumbnail")
                )
            )
        else:
            media = await media_library.get_movies(properties)
            media = media.get("movies")
            title = "Movies"

    elif search_type == MediaType.TVSHOW:
        if search_id:
            media = await media_library.get_seasons(
                tv_show_id=int(search_id),
                properties=["thumbnail", "season", "tvshowid", "art"],
            )
            media = media.get("seasons")
            tvshow = await media_library.get_tv_show_details(
                tv_show_id=int(search_id), properties=properties
            )
            thumbnail = media_library.thumbnail_url(
                tvshow["tvshowdetails"]["art"].get(
                    "poster", tvshow["tvshowdetails"].get("thumbnail")
                )
            )
            title = tvshow["tvshowdetails"]["label"]
        else:
            media = await media_library.get_tv_shows(properties)
            media = media.get("tvshows")
            title = "TV Shows"

    elif search_type == MediaType.SEASON:
        tv_show_id, season_id = search_id.split("/", 1)
        media = await media_library.get_episodes(
            tv_show_id=int(tv_show_id),
            season_id=int(season_id),
            properties=["thumbnail", "tvshowid", "seasonid", "art"],
        )
        media = media.get("episodes")
        if media:
            season = await media_library.get_season_details(
                season_id=int(media[0]["seasonid"]), properties=properties
            )
            thumbnail = media_library.thumbnail_url(
                season["seasondetails"]["art"].get(
                    "poster", season["seasondetails"].get("thumbnail")
                )
            )
            title = season["seasondetails"]["label"]

    elif search_type == MediaType.CHANNEL:
        media = await media_library.get_channels(
            channel_group_id="alltv",
            properties=["thumbnail", "channeltype", "channel", "broadcastnow"],
        )
        media = media.get("channels")

        title = "Channels"

    return thumbnail, title, media