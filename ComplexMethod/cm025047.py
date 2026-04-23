async def test_async_validate(hass: HomeAssistant, tmpdir: py.path.local) -> None:
    """Test the async_validate helper."""
    validator_calls: dict[str, list[int]] = {}

    def _mock_validator_schema(real_func, *args):
        calls = validator_calls.setdefault(real_func.__name__, [])
        calls.append(threading.get_ident())
        return real_func(*args)

    CV_PREFIX = "homeassistant.helpers.config_validation"
    with (
        patch(f"{CV_PREFIX}.isdir", wraps=partial(_mock_validator_schema, cv.isdir)),
        patch(f"{CV_PREFIX}.string", wraps=partial(_mock_validator_schema, cv.string)),
    ):
        # Assert validation in event loop when not decorated with not_async_friendly
        await cv.async_validate(hass, cv.string, "abcd")
        assert validator_calls == {"string": [hass.loop_thread_id]}
        validator_calls = {}

        # Assert validation in executor when decorated with not_async_friendly
        await cv.async_validate(hass, cv.isdir, tmpdir)
        assert validator_calls == {"isdir": [hass.loop_thread_id, ANY]}
        assert validator_calls["isdir"][1] != hass.loop_thread_id
        validator_calls = {}

        # Assert validation in executor when decorated with not_async_friendly
        await cv.async_validate(hass, vol.All(cv.isdir, cv.string), tmpdir)
        assert validator_calls == {"isdir": [hass.loop_thread_id, ANY], "string": [ANY]}
        assert validator_calls["isdir"][1] != hass.loop_thread_id
        assert validator_calls["string"][0] != hass.loop_thread_id
        validator_calls = {}

        # Assert validation in executor when decorated with not_async_friendly
        await cv.async_validate(hass, vol.All(cv.string, cv.isdir), tmpdir)
        assert validator_calls == {
            "isdir": [hass.loop_thread_id, ANY],
            "string": [hass.loop_thread_id, ANY],
        }
        assert validator_calls["isdir"][1] != hass.loop_thread_id
        assert validator_calls["string"][1] != hass.loop_thread_id
        validator_calls = {}

        # Assert validation in event loop when not using cv.async_validate
        cv.isdir(tmpdir)
        assert validator_calls == {"isdir": [hass.loop_thread_id]}
        validator_calls = {}

        # Assert validation in event loop when not using cv.async_validate
        vol.All(cv.isdir, cv.string)(tmpdir)
        assert validator_calls == {
            "isdir": [hass.loop_thread_id],
            "string": [hass.loop_thread_id],
        }
        validator_calls = {}

        # Assert validation in event loop when not using cv.async_validate
        vol.All(cv.string, cv.isdir)(tmpdir)
        assert validator_calls == {
            "isdir": [hass.loop_thread_id],
            "string": [hass.loop_thread_id],
        }
        validator_calls = {}