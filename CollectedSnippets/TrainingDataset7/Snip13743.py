def check_picklable(self, test, err):
        # Ensure that sys.exc_info() tuples are picklable. This displays a
        # clear multiprocessing.pool.RemoteTraceback generated in the child
        # process instead of a multiprocessing.pool.MaybeEncodingError, making
        # the root cause easier to figure out for users who aren't familiar
        # with the multiprocessing module. Since we're in a forked process,
        # our best chance to communicate with them is to print to stdout.
        try:
            self._confirm_picklable(err)
        except Exception as exc:
            original_exc_txt = repr(err[1])
            original_exc_txt = textwrap.fill(
                original_exc_txt, 75, initial_indent="    ", subsequent_indent="    "
            )
            pickle_exc_txt = repr(exc)
            pickle_exc_txt = textwrap.fill(
                pickle_exc_txt, 75, initial_indent="    ", subsequent_indent="    "
            )
            if tblib is None:
                print("""

{} failed:

{}

Unfortunately, tracebacks cannot be pickled, making it impossible for the
parallel test runner to handle this exception cleanly.

In order to see the traceback, you should install tblib:

    python -m pip install tblib
""".format(test, original_exc_txt))
            else:
                print("""

{} failed:

{}

Unfortunately, the exception it raised cannot be pickled, making it impossible
for the parallel test runner to handle it cleanly.

Here's the error encountered while trying to pickle the exception:

{}

You should re-run this test with the --parallel=1 option to reproduce the
failure and get a correct traceback.
""".format(test, original_exc_txt, pickle_exc_txt))
            raise