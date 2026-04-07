def compress(self, data_list):
        if data_list:
            return "%s,%s,%s" % (data_list[0], "".join(data_list[1]), data_list[2])
        return None