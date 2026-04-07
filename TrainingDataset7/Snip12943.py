def encode(k, v):
                return "%s=%s" % ((quote(k, safe), quote(v, safe)))