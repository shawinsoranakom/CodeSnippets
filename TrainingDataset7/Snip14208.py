def dictitem(s):
        t = s.split("=", 1)
        if len(t) > 1:
            return (t[0].lower(), t[1])
        else:
            return (t[0].lower(), True)