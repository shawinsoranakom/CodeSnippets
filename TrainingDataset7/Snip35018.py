def test_pickle_errors_detection(self):
        picklable_error = RuntimeError("This is fine")
        not_unpicklable_error = ExceptionThatFailsUnpickling("arg")

        result = RemoteTestResult()
        result._confirm_picklable(picklable_error)

        # The exception can be pickled but not unpickled.
        pickle.dumps(not_unpicklable_error)
        msg = "__init__() missing 1 required positional argument"
        with self.assertRaisesMessage(TypeError, msg):
            result._confirm_picklable(not_unpicklable_error)