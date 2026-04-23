def align_points(self, vmobject: VMobject) -> Self:
        if self.get_num_points() == len(vmobject.get_points()):
            for mob in [self, vmobject]:
                mob.get_joint_angles()
            return self

        for mob in self, vmobject:
            # If there are no points, add one to
            # where the "center" is
            if not mob.has_points():
                mob.start_new_path(mob.get_center())

        # Figure out what the subpaths are, and align
        subpaths1 = self.get_subpaths()
        subpaths2 = vmobject.get_subpaths()
        for subpaths in [subpaths1, subpaths2]:
            subpaths.sort(key=lambda sp: -sum(
                get_norm(p2 - p1)
                for p1, p2 in zip(sp, sp[1:])
            ))
        n_subpaths = max(len(subpaths1), len(subpaths2))

        # Start building new ones
        new_subpaths1 = []
        new_subpaths2 = []

        def get_nth_subpath(path_list, n):
            if n >= len(path_list):
                return np.vstack([path_list[0][:-1], path_list[0][::-1]])
            return path_list[n]

        for n in range(n_subpaths):
            sp1 = get_nth_subpath(subpaths1, n)
            sp2 = get_nth_subpath(subpaths2, n)
            diff1 = max(0, (len(sp2) - len(sp1)) // 2)
            diff2 = max(0, (len(sp1) - len(sp2)) // 2)
            sp1 = self.insert_n_curves_to_point_list(diff1, sp1)
            sp2 = self.insert_n_curves_to_point_list(diff2, sp2)
            if n > 0:
                # Add intermediate anchor to mark path end
                new_subpaths1.append(new_subpaths1[-1][-1])
                new_subpaths2.append(new_subpaths2[-1][-1])
            new_subpaths1.append(sp1)
            new_subpaths2.append(sp2)

        for mob, paths in [(self, new_subpaths1), (vmobject, new_subpaths2)]:
            new_points = np.vstack(paths)
            mob.resize_points(len(new_points), resize_func=resize_preserving_order)
            mob.set_points(new_points)
            mob.get_joint_angles()
        return self