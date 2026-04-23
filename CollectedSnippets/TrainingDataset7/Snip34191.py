def __call__(self):
                self.num_calls += 1
                return {"the_value": self.value}