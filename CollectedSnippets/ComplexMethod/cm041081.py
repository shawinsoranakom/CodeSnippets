def _normalize_transform(obj):
            transforms = []

            if isinstance(obj, str):
                transforms.append({"Name": obj, "Parameters": {}})

            if isinstance(obj, dict):
                transforms.append(obj)

            if isinstance(obj, list):
                for v in obj:
                    if isinstance(v, str):
                        transforms.append({"Name": v, "Parameters": {}})

                    if isinstance(v, dict):
                        if not v.get("Parameters"):
                            v["Parameters"] = {}
                        transforms.append(v)

            return transforms