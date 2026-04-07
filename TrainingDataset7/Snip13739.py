def __getstate__(self):
        # Make this class picklable by removing the file-like buffer
        # attributes. This is possible since they aren't used after unpickling
        # after being sent to ParallelTestSuite.
        state = self.__dict__.copy()
        state.pop("_stdout_buffer", None)
        state.pop("_stderr_buffer", None)
        state.pop("_original_stdout", None)
        state.pop("_original_stderr", None)
        return state