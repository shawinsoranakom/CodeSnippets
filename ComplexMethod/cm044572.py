def _get_unique_labels(cls, numbers: np.ndarray) -> list[str]:
        """For a list of threshold values for displaying in the bin name, get the lowest number of
        decimal figures (down to int) required to have a unique set of folder names and return the
        formatted numbers.

        Parameters
        ----------
        numbers
            The list of floating point threshold numbers being used as boundary points

        Returns
        -------
        The string formatted numbers at the lowest precision possible to represent them
        uniquely
        """
        i = 0
        while True:
            rounded = [round(n, i) for n in numbers]
            if len(set(rounded)) == len(numbers):
                break
            i += 1

        if i == 0:
            retval = [str(int(n)) for n in rounded]
        else:
            pre, post = zip(*[str(r).split(".") for r in rounded])
            rpad = max(len(x) for x in post)
            retval = [f"{str(int(left))}.{str(int(right)).ljust(rpad, '0')}"
                      for left, right in zip(pre, post)]
        logger.debug("rounded values: %s, formatted labels: %s", rounded, retval)
        return retval