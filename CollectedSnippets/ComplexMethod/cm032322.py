def reset(self, mem=False):
        super().reset()
        if not mem:
            self.history = []
            self.retrieval = []
            self.memory = []
        print(self.variables)
        for k in self.globals.keys():
            if k.startswith("sys."):
                if isinstance(self.globals[k], str):
                    self.globals[k] = ""
                elif isinstance(self.globals[k], int):
                    self.globals[k] = 0
                elif isinstance(self.globals[k], float):
                    self.globals[k] = 0
                elif isinstance(self.globals[k], list):
                    self.globals[k] = []
                elif isinstance(self.globals[k], dict):
                    self.globals[k] = {}
                else:
                    self.globals[k] = None
            if k.startswith("env."):
                key = k[4:]
                if key in self.variables:
                    variable = self.variables[key]
                    if variable["type"] == "string":
                        self.globals[k] = ""
                        variable["value"] = ""
                    elif variable["type"] == "number":
                        self.globals[k] = 0
                        variable["value"] = 0
                    elif variable["type"] == "boolean":
                        self.globals[k] = False
                        variable["value"] = False
                    elif variable["type"] == "object":
                        self.globals[k] = {}
                        variable["value"] = {}
                    elif variable["type"].startswith("array"):
                        self.globals[k] = []
                        variable["value"] = []
                    else:
                        self.globals[k] = ""
                else:
                    self.globals[k] = ""