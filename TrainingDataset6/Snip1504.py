def known_hosts(path):
        with open(path, 'r') as fh:
            return fh.readlines()