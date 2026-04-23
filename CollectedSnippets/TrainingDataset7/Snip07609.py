def dumps(self, obj):
        return [
            json.dumps(
                o,
                separators=(",", ":"),
                cls=MessageEncoder,
            )
            for o in obj
        ]