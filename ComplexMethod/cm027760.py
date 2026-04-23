def looks_identical(self, mobject: Mobject) -> bool:
        fam1 = self.family_members_with_points()
        fam2 = mobject.family_members_with_points()
        if len(fam1) != len(fam2):
            return False
        for m1, m2 in zip(fam1, fam2):
            if m1.get_num_points() != m2.get_num_points():
                return False
            if not m1.data.dtype == m2.data.dtype:
                return False
            for key in m1.data.dtype.names:
                if not np.isclose(m1.data[key], m2.data[key]).all():
                    return False
            if set(m1.uniforms).difference(m2.uniforms):
                return False
            for key in m1.uniforms:
                value1 = m1.uniforms[key]
                value2 = m2.uniforms[key]
                if isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray) and not value1.size == value2.size:
                    return False
                if not np.isclose(value1, value2).all():
                    return False
        return True