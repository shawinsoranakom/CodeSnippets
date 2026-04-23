def _parse_json(self, response, **extra):
        if not hasattr(response, "_json"):
            if not JSON_CONTENT_TYPE_RE.match(response.get("Content-Type")):
                raise ValueError(
                    'Content-Type header is "%s", not "application/json"'
                    % response.get("Content-Type")
                )
            response._json = json.loads(response.text, **extra)
        return response._json