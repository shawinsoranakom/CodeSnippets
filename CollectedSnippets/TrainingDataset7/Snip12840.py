def value_omitted_from_data(self, data, files, name):
        return not any(
            ("{}_{}".format(name, interval) in data)
            for interval in ("year", "month", "day")
        )