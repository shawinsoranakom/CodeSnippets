def _traverse(_object: dict, array=None, parent_key=None) -> list:
            if isinstance(_object, dict):
                for key, values in _object.items():
                    # We update the parent key so that {"key1": {"key2": ""}} becomes "key1.key2"
                    _parent_key = f"{parent_key}.{key}" if parent_key else key

                    # we make sure that we are building only the relevant parts of the payload related to the pattern
                    # the payload could be very complex, and the pattern only applies to part of it
                    if _is_key_in_patterns(_parent_key):
                        array = _traverse(values, array, _parent_key)

            elif isinstance(_object, list):
                if not _object:
                    return array
                array = [i for value in _object for i in _traverse(value, array, parent_key)]
            else:
                array = [{**item, parent_key: _object} for item in array]
            return array