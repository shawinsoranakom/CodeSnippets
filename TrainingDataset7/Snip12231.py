def has_results(self, using):
        q = self.exists()
        compiler = q.get_compiler(using=using)
        return compiler.has_results()