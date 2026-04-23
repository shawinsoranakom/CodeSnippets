async def test_max_conversions_per_device(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test that each device has a maximum number of conversions (currently 2)."""
    max_conversions = 2
    device_ids = ["1234", "5678"]

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_paths = [
            os.path.join(temp_dir, f"{i}.wav") for i in range(max_conversions + 1)
        ]
        for wav_path in wav_paths:
            _write_silence(wav_path, 10)

        wav_urls = [pathname2url(p) for p in wav_paths]

        # Each device will have max + 1 conversions
        device_urls = {
            device_id: [
                async_create_proxy_url(
                    hass,
                    device_id,
                    wav_url,
                    media_format="wav",
                    rate=22050,
                    channels=2,
                    width=2,
                )
                for wav_url in wav_urls
            ]
            for device_id in device_ids
        }

        for urls in device_urls.values():
            # First URL should fail because it was overwritten by the others
            req = await client.get(urls[0])
            assert req.status == HTTPStatus.BAD_REQUEST

            # All other URLs should succeed
            for url in urls[1:]:
                req = await client.get(url)
                assert req.status == HTTPStatus.OK