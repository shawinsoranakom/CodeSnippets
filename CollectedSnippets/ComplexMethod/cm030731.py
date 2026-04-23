def _rounding_values(self, use_float):
        "Build timestamps used to test rounding."

        units = [1, US_TO_NS, MS_TO_NS, SEC_TO_NS]
        if use_float:
            # picoseconds are only tested to pytime_converter accepting floats
            units.append(1e-3)

        values = (
            # small values
            1, 2, 5, 7, 123, 456, 1234,
            # 10^k - 1
            9,
            99,
            999,
            9999,
            99999,
            999999,
            # test half even rounding near 0.5, 1.5, 2.5, 3.5, 4.5
            499, 500, 501,
            1499, 1500, 1501,
            2500,
            3500,
            4500,
        )

        ns_timestamps = [0]
        for unit in units:
            for value in values:
                ns = value * unit
                ns_timestamps.extend((-ns, ns))
        for pow2 in (0, 5, 10, 15, 22, 23, 24, 30, 33):
            ns = (2 ** pow2) * SEC_TO_NS
            ns_timestamps.extend((
                -ns-1, -ns, -ns+1,
                ns-1, ns, ns+1
            ))
        for seconds in (_testcapi.INT_MIN, _testcapi.INT_MAX):
            ns_timestamps.append(seconds * SEC_TO_NS)
        if use_float:
            # numbers with an exact representation in IEEE 754 (base 2)
            for pow2 in (3, 7, 10, 15):
                ns = 2.0 ** (-pow2)
                ns_timestamps.extend((-ns, ns))

        # seconds close to _PyTime_t type limit
        ns = (2 ** 63 // SEC_TO_NS) * SEC_TO_NS
        ns_timestamps.extend((-ns, ns))

        return ns_timestamps