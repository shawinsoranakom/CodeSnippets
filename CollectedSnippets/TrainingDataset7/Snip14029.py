def print_results(self):
        for name, end_times in self.records.items():
            for record_time in end_times:
                record = "%s took %.3fs" % (name, record_time)
                sys.stderr.write(record + os.linesep)