async def test_config_entry_title_from_home(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    auth: FakeAuth,
) -> None:
    """Test that the Google Home name is used for the config entry title."""

    auth.structures.append(
        {
            "name": f"enterprise/{PROJECT_ID}/structures/some-structure-id",
            "traits": {
                "sdm.structures.traits.Info": {
                    "customName": "Example Home",
                },
            },
        }
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_app_creds_flow(result)
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, {"code": "1234"})
    result = await oauth.async_complete_pubsub_flow(
        result, selected_topic=f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}"
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("context", {}).get("unique_id") == PROJECT_ID

    entry = oauth.get_config_entry()
    assert entry.title == "Example Home"
    assert "token" in entry.data
    assert entry.data.get("cloud_project_id") == CLOUD_PROJECT_ID
    assert (
        entry.data.get("subscription_name")
        == f"projects/{CLOUD_PROJECT_ID}/subscriptions/home-assistant-{RAND_SUFFIX}"
    )
    assert (
        entry.data.get("topic_name")
        == f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}"
    )