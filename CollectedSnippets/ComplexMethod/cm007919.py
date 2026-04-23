def sanitize(key, value):
        if isinstance(value, str) and len(value) > 100 and key != 'thumbnail':
            return f'md5:{md5(value)}'
        elif isinstance(value, list) and len(value) > 10:
            return f'count:{len(value)}'
        elif key.endswith('_count') and isinstance(value, int):
            return int
        return value