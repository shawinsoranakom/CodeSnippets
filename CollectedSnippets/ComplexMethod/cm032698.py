def _extract_embedding(result: dict) -> list[float]:
        if not isinstance(result, dict):
            raise TypeError(f"Unexpected response type: {type(result)}")

        data = result.get("data")
        if data is None:
            raise KeyError("Missing 'data' in response")

        if isinstance(data, list):
            if not data:
                raise ValueError("Empty 'data' in response")
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            raise TypeError(f"Unexpected 'data' type: {type(data)}")

        if not isinstance(item, dict):
            raise TypeError("Unexpected item shape in 'data'")
        if "embedding" not in item:
            raise KeyError("Missing 'embedding' in response item")
        return item["embedding"]