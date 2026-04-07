def dictvalue(*t):
        if t[1] is True:
            return t[0]
        else:
            return "%s=%s" % (t[0], t[1])