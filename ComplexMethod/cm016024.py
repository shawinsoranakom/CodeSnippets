def test_subnormal_warning(self):
        """Test that the subnormal is zero warning is not being raised."""
        ld_ma = _discovered_machar(np.longdouble)
        bytes = np.dtype(np.longdouble).itemsize
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            if (ld_ma.it, ld_ma.maxexp) == (63, 16384) and bytes in (12, 16):
                # 80-bit extended precision
                ld_ma.smallest_subnormal
                if len(w) != 0:
                    raise AssertionError(f"Expected no warnings, got {len(w)}")
            elif (ld_ma.it, ld_ma.maxexp) == (112, 16384) and bytes == 16:
                # IEE 754 128-bit
                ld_ma.smallest_subnormal
                if len(w) != 0:
                    raise AssertionError(f"Expected no warnings, got {len(w)}")
            else:
                # Double double
                ld_ma.smallest_subnormal
                # This test may fail on some platforms
                if len(w) != 0:
                    raise AssertionError(f"Expected no warnings, got {len(w)}")