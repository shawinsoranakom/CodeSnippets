def _resolve_variable(self, v: Variable) -> object:
        if v in self.context:
            return self.resolve(self.context[v])

        if self.parent is not None:
            return self.parent.resolve_variable(v)

        if all(c.upper() or c == "_" for c in v.name):
            s = os.environ.get(v.name)
            if s is not None:
                # using yaml.Loader instead of PathwayYamlLoader to prevent recursive
                # parsing of environment variables
                parsed_value = yaml.load(s, yaml.Loader)
                if (
                    isinstance(parsed_value, int)
                    or isinstance(parsed_value, float)
                    or isinstance(parsed_value, bool)
                ):
                    return parsed_value
                else:
                    return s

        raise KeyError(f"variable {v} is not defined")