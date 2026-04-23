def _load_file(self, fobj):
        # Retrieve all the data as it exists in the zoneinfo file
        trans_idx, trans_utc, utcoff, isdst, abbr, tz_str = _common.load_data(
            fobj
        )

        # Infer the DST offsets (needed for .dst()) from the data
        dstoff = self._utcoff_to_dstoff(trans_idx, utcoff, isdst)

        # Convert all the transition times (UTC) into "seconds since 1970-01-01 local time"
        trans_local = self._ts_to_local(trans_idx, trans_utc, utcoff)

        # Construct `_ttinfo` objects for each transition in the file
        _ttinfo_list = [
            _ttinfo(
                _load_timedelta(utcoffset), _load_timedelta(dstoffset), tzname
            )
            for utcoffset, dstoffset, tzname in zip(utcoff, dstoff, abbr)
        ]

        self._trans_utc = trans_utc
        self._trans_local = trans_local
        self._ttinfos = [_ttinfo_list[idx] for idx in trans_idx]

        # Find the first non-DST transition
        for i in range(len(isdst)):
            if not isdst[i]:
                self._tti_before = _ttinfo_list[i]
                break
        else:
            if self._ttinfos:
                self._tti_before = self._ttinfos[0]
            else:
                self._tti_before = None

        # Set the "fallback" time zone
        if tz_str is not None and tz_str != b"":
            self._tz_after = _parse_tz_str(tz_str.decode())
        else:
            if not self._ttinfos and not _ttinfo_list:
                raise ValueError("No time zone information found.")

            if self._ttinfos:
                self._tz_after = self._ttinfos[-1]
            else:
                self._tz_after = _ttinfo_list[-1]

        # Determine if this is a "fixed offset" zone, meaning that the output
        # of the utcoffset, dst and tzname functions does not depend on the
        # specific datetime passed.
        #
        # We make three simplifying assumptions here:
        #
        # 1. If _tz_after is not a _ttinfo, it has transitions that might
        #    actually occur (it is possible to construct TZ strings that
        #    specify STD and DST but no transitions ever occur, such as
        #    AAA0BBB,0/0,J365/25).
        # 2. If _ttinfo_list contains more than one _ttinfo object, the objects
        #    represent different offsets.
        # 3. _ttinfo_list contains no unused _ttinfos (in which case an
        #    otherwise fixed-offset zone with extra _ttinfos defined may
        #    appear to *not* be a fixed offset zone).
        #
        # Violations to these assumptions would be fairly exotic, and exotic
        # zones should almost certainly not be used with datetime.time (the
        # only thing that would be affected by this).
        if len(_ttinfo_list) > 1 or not isinstance(self._tz_after, _ttinfo):
            self._fixed_offset = False
        elif not _ttinfo_list:
            self._fixed_offset = True
        else:
            self._fixed_offset = _ttinfo_list[0] == self._tz_after