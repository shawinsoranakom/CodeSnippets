def dumps(self, obj):
        return json.dumps(obj, separators=(",", ":")).encode("latin-1")