def _confirm_picklable(self, obj):
        """
        Confirm that obj can be pickled and unpickled as multiprocessing will
        need to pickle the exception in the child process and unpickle it in
        the parent process. Let the exception rise, if not.
        """
        pickle.loads(pickle.dumps(obj))