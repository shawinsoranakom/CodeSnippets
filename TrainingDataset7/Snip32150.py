def setUp(self):
        self.ctx_var = contextvars.ContextVar("test_var", default=0)

        class CtxSyncHandler:
            def __init__(self, ctx_var):
                self.ctx_var = ctx_var
                self.values = []

            def __call__(self, **kwargs):
                val = self.ctx_var.get()
                self.ctx_var.set(val + 1)
                self.values.append(self.ctx_var.get())
                return self.ctx_var.get()

        class CtxAsyncHandler:
            def __init__(self, ctx_var):
                self.ctx_var = ctx_var
                self.values = []
                markcoroutinefunction(self)

            async def __call__(self, **kwargs):
                val = self.ctx_var.get()
                self.ctx_var.set(val + 1)
                self.values.append(self.ctx_var.get())
                return self.ctx_var.get()

        self.CtxSyncHandler = CtxSyncHandler
        self.CtxAsyncHandler = CtxAsyncHandler