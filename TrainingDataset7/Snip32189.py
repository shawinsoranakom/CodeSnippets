def __call__(self, **kwargs):
                val = self.ctx_var.get()
                self.ctx_var.set(val + 1)
                self.values.append(self.ctx_var.get())
                return self.ctx_var.get()