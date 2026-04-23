def walk(v):
            if v is None:
                return
            if isinstance(v, str):
                v = v.strip()
                if v.startswith("data:image/"):
                    imgs.append(v)
                return
            if isinstance(v, (list, tuple, set)):
                for item in v:
                    walk(item)
                return
            if isinstance(v, dict):
                if "content" in v:
                    walk(v.get("content"))
                else:
                    for item in v.values():
                        walk(item)