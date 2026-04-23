async def get_one(url):
            """Get data for one URL."""
            result = await amake_request(
                url, response_callback=response_callback, **kwargs
            )
            processed_list: list = []

            for entry in result:
                new_entry = {
                    keys_to_rename.get(k, k): v
                    for k, v in entry.items()
                    if k not in keys_to_remove
                }
                new_entry["chamber"] = "Senate" if "senate-trades" in url else "House"
                processed_list.append(new_entry)

            if not processed_list or len(processed_list) == 0:
                warn(f"No data found for {url.replace(api_key, 'API_KEY')}")

            if processed_list:
                results.extend(processed_list)