async def make_request(
        self: Auth, method: HTTPMethod, url: str, **kwargs: Any
    ) -> JsonArrayType | JsonObjectType:
        """Return the JSON for a HTTP get of a given URL."""

        if method != HTTPMethod.GET:
            pytest.fail(f"Unmocked method: {method} {url}")

        await self._headers()

        # assume a valid GET, and return the JSON for that web API
        if url == "accountInfo":  # /v0/accountInfo
            return {}  # will throw a KeyError -> BadApiResponseError

        if url.startswith("locations/"):  # /v0/locations?userId={id}&allData=True
            return []  # user has no locations

        if url == "userAccount":  # /v2/userAccount
            return user_account_config_fixture(install)

        if url.startswith("location/"):
            if "installationInfo" in url:  # /v2/location/installationInfo?userId={id}
                return user_locations_config_fixture(install)
            if "status" in url:  # /v2/location/{id}/status
                return location_status_fixture(install)

        elif "schedule" in url:
            if url.startswith("domesticHotWater"):  # /v2/domesticHotWater/{id}/schedule
                return dhw_schedule_fixture(install, url[16:23])
            if url.startswith("temperatureZone"):  # /v2/temperatureZone/{id}/schedule
                return zone_schedule_fixture(install, url[16:23])

        pytest.fail(f"Unexpected request: {HTTPMethod.GET} {url}")