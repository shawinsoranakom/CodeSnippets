def get_json_dumps(encoder):
    if encoder is None:
        return json.dumps
    return partial(json.dumps, cls=encoder)