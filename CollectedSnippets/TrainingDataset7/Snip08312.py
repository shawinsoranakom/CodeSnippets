def loads(self, data):
        try:
            return int(data)
        except ValueError:
            return pickle.loads(data)