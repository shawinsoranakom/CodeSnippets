def represent_decimal(self, data):
        return self.represent_scalar("tag:yaml.org,2002:str", str(data))