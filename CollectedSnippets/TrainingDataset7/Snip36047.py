def increment_mtime(self, fp, by=1):
        current_time = time.time()
        self.set_mtime(fp, current_time + by)