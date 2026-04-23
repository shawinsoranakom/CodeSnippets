def _convert_output_to_json(snapshot_content: dict, *args) -> dict:
            """Recurse through all elements in the snapshot and convert the json-string `output` to a dict"""
            for _, v in snapshot_content.items():
                if isinstance(v, dict):
                    if "output" in v:
                        try:
                            if isinstance(v["output"], str):
                                v["output"] = json.loads(v["output"])
                                return
                        except json.JSONDecodeError:
                            pass
                    v = _convert_output_to_json(v)
                elif isinstance(v, list):
                    v = [
                        _convert_output_to_json(item) if isinstance(item, dict) else item
                        for item in v
                    ]
            return snapshot_content