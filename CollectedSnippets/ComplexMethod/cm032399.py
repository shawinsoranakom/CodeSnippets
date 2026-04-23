def _recursive_convert_obj_to_dict(obj):
            ret_dict = {}
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, dict) or (v and type(v).__name__ not in dir(builtins)):
                        ret_dict[k] = _recursive_convert_obj_to_dict(v)
                    else:
                        ret_dict[k] = v
                return ret_dict

            for attr_name in list(obj.__dict__):
                if attr_name in [_FEEDED_DEPRECATED_PARAMS, _DEPRECATED_PARAMS, _USER_FEEDED_PARAMS, _IS_RAW_CONF]:
                    continue
                # get attr
                attr = getattr(obj, attr_name)
                if isinstance(attr, pd.DataFrame):
                    ret_dict[attr_name] = attr.to_dict()
                    continue
                if isinstance(attr, dict) or (attr and type(attr).__name__ not in dir(builtins)):
                    ret_dict[attr_name] = _recursive_convert_obj_to_dict(attr)
                else:
                    ret_dict[attr_name] = attr

            return ret_dict