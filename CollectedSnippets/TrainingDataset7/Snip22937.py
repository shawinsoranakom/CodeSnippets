def compress(self, data_list):
                if data_list:
                    return "%s.%s ext. %s (label: %s)" % tuple(data_list)
                return None