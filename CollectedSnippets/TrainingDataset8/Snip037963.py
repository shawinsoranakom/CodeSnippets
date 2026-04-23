def to_str(v):
            try:
                return "Object of type %s: %s" % (type_util.get_fqn_type(v), str(v))
            except Exception:
                return "<Unable to convert item to string>"