def default(self, o):
        import yaml  # leave import here, to avoid breaking our Lambda tests!

        if isinstance(o, HostAndPort):
            return str(o)
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        if isinstance(o, (datetime, date)):
            return timestamp_millis(o)
        if isinstance(o, yaml.ScalarNode):
            if o.tag == "tag:yaml.org,2002:int":
                return int(o.value)
            if o.tag == "tag:yaml.org,2002:float":
                return float(o.value)
            if o.tag == "tag:yaml.org,2002:bool":
                return bool(o.value)
            return str(o.value)
        try:
            if isinstance(o, bytes):
                return to_str(o)
            return super().default(o)
        except Exception:
            return None