def __init__(self, data=None, auto_id=False, field_list=[]):
                Form.__init__(self, data, auto_id=auto_id)

                for field in field_list:
                    self.fields[field[0]] = field[1]