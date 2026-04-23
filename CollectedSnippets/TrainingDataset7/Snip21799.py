def random_upload_to(self, filename):
        # This returns a different result each time,
        # to make sure it only gets called once.
        return "%s/%s" % (random.randint(100, 999), filename)