async def _async_method_inner(self, request):
        # Do not just use plain strings for the variables' values in the code
        # so that the tests don't return false positives when the function's
        # source is displayed in the exception report.
        cooked_eggs = "".join(["s", "c", "r", "a", "m", "b", "l", "e", "d"])  # NOQA
        sauce = "".join(  # NOQA
            ["w", "o", "r", "c", "e", "s", "t", "e", "r", "s", "h", "i", "r", "e"]
        )
        raise Exception