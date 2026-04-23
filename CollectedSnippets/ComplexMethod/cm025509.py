def _update_data(self) -> dict[str, OndiloIcoPoolData]:
        """Fetch pools data from API endpoint."""
        res = {}
        pools = self.api.get_pools()
        _LOGGER.debug("Pools: %s", pools)
        error: OndiloError | None = None
        for pool in pools:
            pool_id = pool["id"]
            if (data := self.data) and pool_id in data:
                pool_data = res[pool_id] = data[pool_id]
                pool_data.pool = pool
                # Skip requesting new ICO data for known pools
                # to avoid unnecessary API calls.
                continue
            try:
                ico = self.api.get_ICO_details(pool_id)
            except OndiloError as err:
                error = err
                _LOGGER.debug("Error communicating with API for %s: %s", pool_id, err)
                continue

            if not ico:
                _LOGGER.debug("The pool id %s does not have any ICO attached", pool_id)
                continue

            res[pool_id] = OndiloIcoPoolData(ico=ico, pool=pool)
        if not res:
            if error:
                raise UpdateFailed(f"Error communicating with API: {error}") from error
        return res