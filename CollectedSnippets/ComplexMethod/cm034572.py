def parse_json_maybe(s: str):
                if not s:
                    return None
                try:
                    return json.loads(s)
                except Exception:
                    pass
                m = None
                if "{" in s and "}" in s:
                    m = re.search(r"\{[\s\S]*\}", s)
                if m is None and "[" in s and "]" in s:
                    m = re.search(r"\[[\s\S]*\]", s)
                if not m:
                    return None
                try:
                    return json.loads(m.group(0))
                except Exception:
                    return None