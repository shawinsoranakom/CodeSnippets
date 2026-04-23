def _check_gather_pattern(
        self,
        buf_size: list,
        actual_strides: list,
        is_contiguous: bool,
        coefficients: OrderedSet,
    ) -> bool:
        """
        Check if access pattern requires gather (non-standard striding).
        """
        expected_strides = [1]  # 1D buffers have stride 1

        if len(buf_size) > 1:
            expected_stride = 1
            expected_strides = []
            for i in range(len(buf_size) - 1, -1, -1):
                expected_strides.insert(0, expected_stride)
                dim_size = self._safe_int(buf_size[i])
                if dim_size is not None:
                    expected_stride *= dim_size

        if is_contiguous:
            # Buffer is contiguous - check if access coefficients match expected strides
            expected_stride_set = OrderedSet(expected_strides)
            for coef in coefficients:
                if coef not in expected_stride_set:
                    return True
        else:
            # Buffer is NOT contiguous (strided input)
            # Check if coefficients match actual buffer strides
            actual_stride_set = OrderedSet(s for s in actual_strides if s is not None)
            for coef in coefficients:
                if coef not in actual_stride_set:
                    return True

        return False