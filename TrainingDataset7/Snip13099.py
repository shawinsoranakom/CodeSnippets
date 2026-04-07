def get_backend(self):
        from . import task_backends

        return task_backends[self.backend]