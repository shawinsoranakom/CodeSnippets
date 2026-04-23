def getslice(self, start=0, end=None):
        res = []
        for pagenum in itertools.count(start // self._pagesize):
            firstid = pagenum * self._pagesize
            nextfirstid = pagenum * self._pagesize + self._pagesize
            if start >= nextfirstid:
                continue

            page_results = None
            if self._use_cache:
                page_results = self._cache.get(pagenum)
            if page_results is None:
                page_results = list(self._pagefunc(pagenum))
            if self._use_cache:
                self._cache[pagenum] = page_results

            startv = (
                start % self._pagesize
                if firstid <= start < nextfirstid
                else 0)

            endv = (
                ((end - 1) % self._pagesize) + 1
                if (end is not None and firstid <= end <= nextfirstid)
                else None)

            if startv != 0 or endv is not None:
                page_results = page_results[startv:endv]
            res.extend(page_results)

            # A little optimization - if current page is not "full", ie. does
            # not contain page_size videos then we can assume that this page
            # is the last one - there are no more ids on further pages -
            # i.e. no need to query again.
            if len(page_results) + startv < self._pagesize:
                break

            # If we got the whole page, but the next page is not interesting,
            # break out early as well
            if end == nextfirstid:
                break
        return res