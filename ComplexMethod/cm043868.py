async def get_one(url):
            """Response callback function."""
            res = await amake_request(url, response_callback=response_callback)
            data = res.get("response", {}).get("data", [])  # type: ignore
            if not data:
                series_id = res.get("request", {}).get("params", {}).get("facets", {}).get("seriesId", [])  # type: ignore
                masked_url = url.replace(api_key, "API_KEY")
                messages.append(f"No data returned for {series_id or masked_url}")
            if data:
                results.extend(data)
            response_total = int(res.get("response", {}).get("total", 0))  # type: ignore
            n_results = len(data)
            # After conservatively chunking the request, we may still need to paginate.
            # This is mostly out of an abundance of caution.
            if response_total > 5000 and n_results == 5000:
                offset = 5000
                url = url.replace("&offset=0", f"&offset={offset}")
                while n_results < response_total:
                    additional_response = await amake_request(url)
                    additional_data = additional_response.get("response", {}).get("data", [])  # type: ignore
                    if not additional_data:
                        series_id = (
                            res.get("request", {}).get("params", {}).get("facets", {}).get("seriesId", [])  # type: ignore
                        )
                        masked_url = url.replace(api_key, "API_KEY")
                        messages.append(
                            f"No additional data returned for {series_id or masked_url}"
                        )
                    if additional_data:
                        results.extend(additional_data)
                    n_results += len(additional_data)
                    url = url.replace(f"&offset={offset}", f"&offset={offset + 5000}")
                    offset += 5000