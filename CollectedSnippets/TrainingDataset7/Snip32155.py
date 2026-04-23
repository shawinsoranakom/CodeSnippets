async def test_asend_robust_correct_contextvars_sharing_sync_receivers(self):
        handler1 = self.CtxSyncHandler(self.ctx_var)
        handler2 = self.CtxSyncHandler(self.ctx_var)
        signal = dispatch.Signal()
        signal.connect(handler1)
        signal.connect(handler2)

        # set custom value outer signal
        self.ctx_var.set(1)

        await signal.asend_robust(self.__class__)

        self.assertEqual(len(handler1.values), 1)
        self.assertEqual(len(handler2.values), 1)
        self.assertEqual(sorted([*handler1.values, *handler2.values]), [2, 3])
        self.assertEqual(self.ctx_var.get(), 3)