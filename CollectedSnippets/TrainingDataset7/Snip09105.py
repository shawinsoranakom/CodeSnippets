def timestamp(self):
        return b62_encode(int(time.time()))