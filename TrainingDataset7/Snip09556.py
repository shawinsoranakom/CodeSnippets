def format_for_duration_arithmetic(self, sql):
        return "INTERVAL %s MICROSECOND" % sql