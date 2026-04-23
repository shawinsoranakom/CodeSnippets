def lock_matching_data(self, mobject1: Mobject, mobject2: Mobject) -> Self:
        tuples = zip(
            self.get_family(),
            mobject1.get_family(),
            mobject2.get_family(),
        )
        for sm, sm1, sm2 in tuples:
            if not sm.data.dtype == sm1.data.dtype == sm2.data.dtype:
                continue
            sm.lock_data(
                key for key in sm.data.dtype.names
                if arrays_match(sm1.data[key], sm2.data[key])
            )
            sm.lock_uniforms(
                key for key in self.uniforms
                if all(listify(mobject1.uniforms.get(key, 0) == mobject2.uniforms.get(key, 0)))
            )
            sm.const_data_keys = set(
                key for key in sm.data.dtype.names
                if key not in sm.locked_data_keys
                if all(
                    array_is_constant(mob.data[key])
                    for mob in (sm, sm1, sm2)
                )
            )

        return self