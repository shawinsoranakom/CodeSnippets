def backend(gm, args):
            context = torch._guards.TracingContext.get()
            guards = [str(g.expr) for g in context.fake_mode.shape_env.guards]

            # varies based on the type of view
            guard_str = "\n".join(guards)

            if nt_view_name == "base_is_nt_False_basic":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s20, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_False_leaf_False_False":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_False_leaf_False_True":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s20, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_False_leaf_True_False":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s20, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_False_leaf_True_True":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s20, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_False_obscure":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s64)
Eq(s20, s64)
Eq(s80 - 1, s77)
Eq(s72, s71)""",
                )
            elif nt_view_name == "base_is_nt_True_basic":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s17 - 1, s83)
Eq(s20, s83)""",
                )
            elif nt_view_name == "base_is_nt_True_leaf_False_False":
                self.assertExpectedInline(
                    guard_str,
                    """Eq(s17 - 1, s83)""",
                )
            elif nt_view_name == "base_is_nt_True_leaf_False_True":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s17 - 1, s83)
Eq(s20, s83)""",
                )
            elif nt_view_name == "base_is_nt_True_leaf_True_False":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s17 - 1, s83)
Eq(s20, s83)""",
                )
            elif nt_view_name == "base_is_nt_True_leaf_True_True":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s17 - 1, s83)
Eq(s20, s83)""",
                )
            elif nt_view_name == "base_is_nt_True_obscure":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s17 - 1, s83)
Eq(s20, s83)""",
                )
            elif nt_view_name == "dense_subclass_dense_subclass":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s77)
Eq(s80 - 1, s78)
Eq(s72, s71)""",
                )
            elif nt_view_name == "subclass_dense":
                self.assertExpectedInline(
                    guard_str,
                    """\
Eq(s85 - 1, s77)
Eq(s20, s77)""",
                )
            else:
                raise NotImplementedError
            return gm