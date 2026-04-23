async def test_service_get_queue_image_fallback(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_sonarr: MagicMock,
) -> None:
    """Test that get_queue uses url fallback when remoteUrl is not available."""
    # Mock queue response with images that only have 'url' (no 'remoteUrl')
    mock_sonarr.async_get_queue.return_value = SonarrQueue(
        {
            "page": 1,
            "pageSize": 10,
            "sortKey": "timeleft",
            "sortDirection": "ascending",
            "totalRecords": 1,
            "records": [
                {
                    "series": {
                        "title": "Test Series",
                        "sortTitle": "test series",
                        "seasonCount": 1,
                        "status": "continuing",
                        "overview": "A test series.",
                        "network": "Test Network",
                        "airTime": "20:00",
                        "images": [
                            {
                                "coverType": "fanart",
                                "url": "/MediaCover/1/fanart.jpg?lastWrite=123456",
                            },
                            {
                                "coverType": "poster",
                                "url": "/MediaCover/1/poster.jpg?lastWrite=123456",
                            },
                        ],
                        "seasons": [{"seasonNumber": 1, "monitored": True}],
                        "year": 2024,
                        "path": "/tv/Test Series",
                        "profileId": 1,
                        "seasonFolder": True,
                        "monitored": True,
                        "useSceneNumbering": False,
                        "runtime": 45,
                        "tvdbId": 12345,
                        "tvRageId": 0,
                        "tvMazeId": 0,
                        "firstAired": "2024-01-01T00:00:00Z",
                        "lastInfoSync": "2024-01-01T00:00:00Z",
                        "seriesType": "standard",
                        "cleanTitle": "testseries",
                        "imdbId": "tt1234567",
                        "titleSlug": "test-series",
                        "certification": "TV-14",
                        "genres": ["Drama"],
                        "tags": [],
                        "added": "2024-01-01T00:00:00Z",
                        "ratings": {"votes": 100, "value": 8.0},
                        "qualityProfileId": 1,
                        "id": 1,
                    },
                    "episode": {
                        "seriesId": 1,
                        "episodeFileId": 0,
                        "seasonNumber": 1,
                        "episodeNumber": 1,
                        "title": "Pilot",
                        "airDate": "2024-01-01",
                        "airDateUtc": "2024-01-01T00:00:00Z",
                        "overview": "The pilot episode.",
                        "hasFile": False,
                        "monitored": True,
                        "absoluteEpisodeNumber": 1,
                        "unverifiedSceneNumbering": False,
                        "id": 1,
                    },
                    "quality": {
                        "quality": {"id": 3, "name": "WEBDL-1080p"},
                        "revision": {"version": 1, "real": 0},
                    },
                    "size": 1000000000,
                    "title": "Test.Series.S01E01.1080p.WEB-DL",
                    "sizeleft": 500000000,
                    "timeleft": "00:10:00",
                    "estimatedCompletionTime": "2024-01-01T01:00:00Z",
                    "status": "Downloading",
                    "trackedDownloadStatus": "Ok",
                    "statusMessages": [],
                    "downloadId": "test123",
                    "protocol": "torrent",
                    "id": 1,
                }
            ],
        }
    )

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_QUEUE,
        {ATTR_ENTRY_ID: init_integration.entry_id},
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert ATTR_SHOWS in response
    shows = response[ATTR_SHOWS]
    assert len(shows) == 1

    queue_item = shows["Test.Series.S01E01.1080p.WEB-DL"]
    assert "images" in queue_item

    # Since remoteUrl is not available, the fallback should use base_url + url
    # The base_url from mock_config_entry is http://192.168.1.189:8989
    assert "fanart" in queue_item["images"]
    assert "poster" in queue_item["images"]
    # Check that the fallback constructed the URL with base_url prefix
    assert queue_item["images"]["fanart"] == (
        "http://192.168.1.189:8989/MediaCover/1/fanart.jpg?lastWrite=123456"
    )
    assert queue_item["images"]["poster"] == (
        "http://192.168.1.189:8989/MediaCover/1/poster.jpg?lastWrite=123456"
    )