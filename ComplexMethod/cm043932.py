def get_available_constraints(
        self,
        dataflow_id: str,
        key: str,
        component_id: str | None = None,
        mode: str | None = None,
        references: str | None = None,
        **kwargs,
    ) -> dict:
        """Fetch available constraints for a given dataflow and parameters."""
        # pylint: disable=import-outside-toplevel
        import json

        from openbb_core.provider.utils.helpers import make_request
        from requests.exceptions import RequestException

        if dataflow_id not in self.dataflows:
            raise ValueError(f"Dataflow '{dataflow_id}' not found.")

        kwargs_sorted = sorted(kwargs.items())
        kwargs_tuple = tuple(kwargs_sorted)

        cache_key = (
            f"{dataflow_id}:{key}:{component_id}:{mode}:{references}:{kwargs_tuple}"
        )

        with self._constraints_lock:
            if cached_constraints := self._constraints_cache.get(cache_key):
                return cached_constraints

        df = self.dataflows[dataflow_id]
        agency_id = df.get("agencyID")

        if not agency_id:
            raise ValueError(f"Agency ID not found for dataflow '{dataflow_id}'.")

        # Note: URL length is now primarily managed by table_builder.py which limits
        # constraint keys to depth 0-1 codes when there are many indicators.
        # This fallback is kept as a safety net for edge cases.
        processed_key = key

        base_url = (
            f"https://api.imf.org/external/sdmx/3.0/availability/dataflow/"
            f"{agency_id}/{dataflow_id}/%2B/{processed_key}/{component_id or 'all'}"
        )
        query_params = {
            "mode": mode,
            "references": references,
        }
        c_params = {f"c[{k}]": v for k, v in kwargs.items() if v}
        query_params.update(c_params)

        query_params = {k: v for k, v in query_params.items() if v is not None}
        url = (
            base_url + "?" + "&".join(f"{k}={v}" for k, v in query_params.items())
            if query_params
            else base_url
        )
        json_response: dict = {}
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": "Open Data Platform - IMF Metadata Utility",
            }
            response = make_request(url, headers=headers)
            response.raise_for_status()
            json_response = response.json()
        except json.JSONDecodeError as e:
            raise OpenBBError(
                f"Unexpected response format when fetching constraints {dataflow_id}: {e}"
                + f" -> {url}"
            ) from None
        except RequestException as e:
            raise OpenBBError(
                f"An error occurred while fetching constraints {dataflow_id}: {e} -> {url}"
            ) from None

        extracted_values: dict = {}
        json_data = json_response.get("data", {})
        data_constraints = json_data.get("dataConstraints", [])

        for constraint in data_constraints:
            for region in constraint.get("cubeRegions", []):
                for kv in region.get("keyValues", []):
                    dim_id = kv.get("id")
                    if dim_id:
                        if dim_id not in extracted_values:
                            extracted_values[dim_id] = []
                        for val in kv.get("values", []):
                            if isinstance(val, dict):
                                extracted_values[dim_id].append(val.get("value"))
                            else:
                                extracted_values[dim_id].append(val)
                for comp in region.get("components", []):
                    dim_id = comp.get("id")
                    if dim_id:
                        if dim_id not in extracted_values:
                            extracted_values[dim_id] = []
                        for val in comp.get("values", []):
                            if isinstance(val, dict):
                                extracted_values[dim_id].append(val.get("value"))
                            else:
                                extracted_values[dim_id].append(val)

        for dim_id, values in list(extracted_values.items()):
            # Remove falsy values, deduplicate.
            unique_values = {v for v in values if v}
            extracted_values[dim_id] = list(unique_values)

        key_values = [{"id": k, "values": v} for k, v in extracted_values.items()]

        result = {"key_values": key_values, "full_response": json_response}

        with self._constraints_lock:
            self._constraints_cache[cache_key] = result

        return result