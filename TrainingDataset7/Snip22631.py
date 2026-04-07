def as_uuid(self, dct):
                if "uuid" in dct:
                    dct["uuid"] = uuid.UUID(dct["uuid"])
                return dct