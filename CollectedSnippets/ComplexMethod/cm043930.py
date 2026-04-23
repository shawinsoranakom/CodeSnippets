def _bulk_fetch_and_cache_codelists(self, agency_id: str, dataflow_id: str):
        """Fetch all codelists for a given agency and dataflow and caches them."""
        # pylint: disable=import-outside-toplevel
        import json

        from openbb_core.provider.utils.helpers import make_request
        from requests.exceptions import RequestException

        url = f"https://api.imf.org/external/sdmx/3.0/structure/codelist/{agency_id},{dataflow_id}/all?detail=full&references=none"
        headers = {"Accept": "application/json"}

        try:
            response = make_request(url, headers=headers)
            json_response: dict = response.json()
        except (json.JSONDecodeError, RequestException) as e:
            warnings.warn(
                f"Could not bulk fetch codelists for {agency_id}/{dataflow_id}: {e} -> {url}",
                OpenBBWarning,
            )
            return

        codelists_in_response = json_response.get("data", {}).get("codelists", [])

        with self._codelist_lock:
            for codelist_obj in codelists_in_response:
                codelist_id = codelist_obj.get("id")
                if not codelist_id:
                    continue

                current_codelist_map = {}
                current_descriptions_map = {}
                for code in codelist_obj.get("codes", []):
                    code_id = code.get("id")
                    code_name_obj = (
                        code.get("names", {}).get("en") or code.get("name") or code_id
                    )
                    code_description = (
                        code.get("descriptions", {}).get("en", "")
                        or code.get("description", "")
                        or ""
                    )
                    if not code_description and code_name_obj:
                        code_description = code_name_obj

                    if code_id:
                        current_codelist_map[code_id] = code_name_obj
                        current_descriptions_map[code_id] = code_description

                self._codelist_cache[codelist_id] = current_codelist_map
                self._codelist_descriptions[codelist_id] = current_descriptions_map