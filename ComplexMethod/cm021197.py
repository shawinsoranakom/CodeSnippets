def default_settings_data(*args):
            # the get_setting_values method can be called with different argument types and numbers
            match args:
                case (str() as module_id, str() as data_id):
                    request = {module_id: [data_id]}
                case (str() as module_id, Iterable() as data_ids):
                    request = {module_id: data_ids}
                case ({},):
                    request = args[0]
                case _:
                    raise NotImplementedError

            result = {}
            for module_id, data_ids in request.items():
                if (values := mock_get_setting_values.get(module_id)) is not None:
                    result[module_id] = {}
                    for data_id in data_ids:
                        if data_id in values:
                            result[module_id][data_id] = values[data_id]
                        else:
                            raise ValueError(
                                f"Missing data_id {data_id} in module {module_id}"
                            )
                else:
                    raise ValueError(f"Missing module_id {module_id}")

            return result