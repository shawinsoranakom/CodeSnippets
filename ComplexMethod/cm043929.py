def _fetch_single_codelist(self, agency_id: str, codelist_id: str) -> bool:
        """
        Fetch a single codelist from the API and cache it.

        Parameters
        ----------
        agency_id : str
            The agency ID (e.g., "ISORA", "IMF.STA")
        codelist_id : str
            The codelist ID (e.g., "CL_RAFIT_LABELS")

        Returns
        -------
        bool
            True if successfully fetched and cached, False otherwise.
        """
        # pylint: disable=import-outside-toplevel
        import json

        from openbb_core.provider.utils.helpers import make_request
        from requests.exceptions import RequestException

        if codelist_id in self._codelist_cache and self._codelist_cache.get(
            codelist_id
        ):
            return True

        url = f"https://api.imf.org/external/sdmx/3.0/structure/codelist/{agency_id}/{codelist_id}?detail=full&references=none"
        headers = {"Accept": "application/json"}

        try:
            response = make_request(url, headers=headers, timeout=5)
            if response.status_code != 200:
                # Mark as failed to avoid repeated attempts
                # self._codelist_cache[codelist_id] = {}
                return False
            json_response: dict = response.json()
        except (json.JSONDecodeError, RequestException):
            # Mark as failed to avoid repeated attempts
            # self._codelist_cache[codelist_id] = {}
            return False

        codelists_in_response = json_response.get("data", {}).get("codelists", [])

        if not codelists_in_response:
            return False

        with self._codelist_lock:
            for codelist_obj in codelists_in_response:
                cl_id = codelist_obj.get("id")
                if not cl_id:
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

                self._codelist_cache[cl_id] = current_codelist_map
                self._codelist_descriptions[cl_id] = current_descriptions_map

        return codelist_id in self._codelist_cache