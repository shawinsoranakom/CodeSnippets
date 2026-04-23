def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, datetime.timedelta):
            return str(obj)
        elif issubclass(type(obj), Enum) or issubclass(type(obj), IntEnum):
            return obj.value
        elif isinstance(obj, set):
            return list(obj)
        elif issubclass(type(obj), BaseType):
            if not self._with_type:
                return obj.to_dict()
            else:
                return obj.to_dict_with_type()
        elif isinstance(obj, type):
            return obj.__name__
        else:
            return json.JSONEncoder.default(self, obj)