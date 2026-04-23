def _configure_async_dispatch(self, callbacks):
        # Determine whether callbacks can be dispatched asynchronously.
        if not backend.IS_THREAD_SAFE:
            return
        async_train = True
        async_test = True
        async_predict = True
        if callbacks:
            if isinstance(callbacks, (list, tuple)):
                for cbk in callbacks:
                    if getattr(cbk, "async_safe", False):
                        # Callbacks that expose self.async_safe == True
                        # will be assumed safe for async dispatch.
                        continue
                    if not utils.is_default(cbk.on_batch_end):
                        async_train = False
                    if not utils.is_default(cbk.on_train_batch_end):
                        async_train = False
                    if not utils.is_default(cbk.on_test_batch_end):
                        async_test = False
                    if not utils.is_default(cbk.on_predict_batch_end):
                        async_predict = False

        self._async_train = async_train
        self._async_test = async_test
        self._async_predict = async_predict