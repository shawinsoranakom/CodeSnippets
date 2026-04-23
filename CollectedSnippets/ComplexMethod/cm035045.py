def resample_sidelines(self, sideline1, sideline2, resample_step):
        """Resample two sidelines to be of the same points number according to
        step size.

        Args:
            sideline1 (ndarray): The points composing a sideline of a text
                polygon.
            sideline2 (ndarray): The points composing another sideline of a
                text polygon.
            resample_step (float): The resampled step size.

        Returns:
            resampled_line1 (ndarray): The resampled line 1.
            resampled_line2 (ndarray): The resampled line 2.
        """

        assert sideline1.ndim == sideline2.ndim == 2
        assert sideline1.shape[1] == sideline2.shape[1] == 2
        assert sideline1.shape[0] >= 2
        assert sideline2.shape[0] >= 2
        assert isinstance(resample_step, float)

        length1 = sum(
            [norm(sideline1[i + 1] - sideline1[i]) for i in range(len(sideline1) - 1)]
        )
        length2 = sum(
            [norm(sideline2[i + 1] - sideline2[i]) for i in range(len(sideline2) - 1)]
        )

        total_length = (length1 + length2) / 2
        resample_point_num = max(int(float(total_length) / resample_step), 1)

        resampled_line1 = self.resample_line(sideline1, resample_point_num)
        resampled_line2 = self.resample_line(sideline2, resample_point_num)

        return resampled_line1, resampled_line2