def add(key, template):
        value = db.get(key, None)
        # Don't add the parameter if it is not in django's settings
        if value:
            params.append(template % value)