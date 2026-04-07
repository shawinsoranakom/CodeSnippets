def test_argon2_version_upgrade(self):
        hasher = get_hasher("argon2")
        state = {"upgraded": False}
        encoded = (
            "argon2$argon2id$v=19$m=102400,t=2,p=8$Y041dExhNkljRUUy$TMa6A8fPJh"
            "CAUXRhJXCXdw"
        )

        def setter(password):
            state["upgraded"] = True

        old_m = hasher.memory_cost
        old_t = hasher.time_cost
        old_p = hasher.parallelism
        try:
            hasher.memory_cost = 8
            hasher.time_cost = 1
            hasher.parallelism = 1
            self.assertTrue(check_password("secret", encoded, setter, "argon2"))
            self.assertTrue(state["upgraded"])
        finally:
            hasher.memory_cost = old_m
            hasher.time_cost = old_t
            hasher.parallelism = old_p