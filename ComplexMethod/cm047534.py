def convert_to_cache(self, value, record, validate=True):
        # cache format: str ("model,id") or None
        if isinstance(value, BaseModel):
            if not validate or (value._name in self.get_values(record.env) and len(value) <= 1):
                return "%s,%s" % (value._name, value.id) if value else None
        elif isinstance(value, str):
            res_model, res_id = value.split(',')
            if not validate or res_model in self.get_values(record.env):
                if record.env[res_model].browse(int(res_id)).exists():
                    return value
                else:
                    return None
        elif not value:
            return None
        raise ValueError("Wrong value for %s: %r" % (self, value))