def get_prep_value(self, value):
                if value is True:
                    return {"value": True}
                return value