def get_joint_angles(self, refresh: bool = False) -> np.ndarray:
        """
        The 'joint product' is a 4-vector holding the cross and dot
        product between tangent vectors at a joint
        """
        if not self.needs_new_joint_angles and not refresh:
            return self.data["joint_angle"][:, 0]

        if "joint_angle" in self.locked_data_keys:
            return self.data["joint_angle"][:, 0]

        self.needs_new_joint_angles = False
        self._data_has_changed = True

        # Rotate points such that positive z direction is the normal
        points = self.get_points() @ rotation_between_vectors(OUT, self.get_unit_normal())

        if len(points) < 3:
            return self.data["joint_angle"][:, 0]

        # Find all the unit tangent vectors at each joint
        a0, h, a1 = points[0:-1:2], points[1::2], points[2::2]
        a0_to_h = h - a0
        h_to_a1 = a1 - h

        # Tangent vectors into each vertex
        v_in = np.zeros(points.shape)
        # Tangent vectors out of each vertex
        v_out = np.zeros(points.shape)

        v_in[1::2] = a0_to_h
        v_in[2::2] = h_to_a1
        v_out[0:-1:2] = a0_to_h
        v_out[1::2] = h_to_a1

        # Joint up closed loops, or mark unclosed paths as such
        ends = self.get_subpath_end_indices()
        starts = [0, *(e + 2 for e in ends[:-1])]
        for start, end in zip(starts, ends):
            if start == end:
                continue
            if (points[start] == points[end]).all():
                v_in[start] = v_out[end - 1]
                v_out[end] = v_in[start + 1]
            else:
                v_in[start] = v_out[start]
                v_out[end] = v_in[end]

        # Find the angles between vectors into each vertex, and out of it
        angles_in = np.arctan2(v_in[:, 1], v_in[:, 0])
        angles_out = np.arctan2(v_out[:, 1], v_out[:, 0])
        angle_diffs = angles_out - angles_in
        angle_diffs[angle_diffs < -PI] += TAU
        angle_diffs[angle_diffs > PI] -= TAU
        self.data["joint_angle"][:, 0] = angle_diffs
        return self.data["joint_angle"][:, 0]