def flatten(obj, parent_key=""):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    if isinstance(v, (dict, list)) and v:
                        items.extend(flatten(v, new_key))
                    else:
                        items.append({"name": new_key, "value": v})
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    new_key = f"{parent_key}[{i}]"
                    if isinstance(v, (dict, list)) and v:
                        items.extend(flatten(v, new_key))
                    else:
                        items.append({"name": new_key, "value": v})
            return items