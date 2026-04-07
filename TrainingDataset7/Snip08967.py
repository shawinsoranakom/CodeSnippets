def update(self, count):
        if not self.output:
            return
        perc = count * 100 // self.total_count
        done = perc * self.progress_width // 100
        if self.prev_done >= done:
            return
        self.prev_done = done
        cr = "" if self.total_count == 1 else "\r"
        self.output.write(
            cr + "[" + "." * done + " " * (self.progress_width - done) + "]"
        )
        if done == self.progress_width:
            self.output.write("\n")
        self.output.flush()