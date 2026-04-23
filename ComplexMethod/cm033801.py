def _validate_semantic_markup_collect(self, destination, sub_key, data, all_paths):
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            keys = {key}
            if is_iterable(value.get('aliases')):
                keys.update(value['aliases'])
            new_paths = [path + [key] for path in all_paths for key in keys]
            destination.update([tuple(path) for path in new_paths])
            self._validate_semantic_markup_collect(destination, sub_key, value.get(sub_key), new_paths)