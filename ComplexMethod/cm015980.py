def test_memory_timeline(self) -> None:
        model = torch.nn.Sequential(
            torch.nn.Linear(64, 512, bias=True),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 512, bias=False),
            torch.nn.Softmax(dim=1),
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=0.1)

        with profile() as prof:
            x = torch.ones((1024, 64))
            targets = torch.ones((1024, 512))
            y = model(x)
            loss = torch.nn.functional.mse_loss(y, targets)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

        memory_profile = prof._memory_profile()
        timeline = memory_profile.timeline
        times = tuple(t for t, _, _, _ in timeline)
        self.assertTrue(all(t1 >= t0 for t0, t1 in it.pairwise(times)), times)
        self.assertTrue(
            all(
                (t == -1) if action == _memory_profiler.Action.PREEXISTING else (t > 0)
                for t, action, _, _ in timeline
            )
        )

        def category_name(category):
            return category.name if category else "???"

        def format_action(action, key, version):
            category = memory_profile._categories.get(key, version)
            if action == _memory_profiler.Action.INCREMENT_VERSION:
                new_category = memory_profile._categories.get(key, version + 1)
                if category != new_category:
                    return f"{category_name(category)} -> {category_name(new_category)}"
            return category_name(category)

        def format_size(size: int):
            if size < 1024:
                return f"{size / 1024:3.1f} kB"
            return f"{size // 1024} kB"

        # We generate sequential IDs for Tensors; however platforms vary
        # slightly in the exact computation executed. If this results in
        # tensor creation the IDs will be shifted and the unit test will fail.
        # (Even though the behavior we're testing is unchanged.) To correct for
        # this we assign sequential numbers to the tensors which are actually
        # tested, effectively suppressing the extraneous implementation details.
        id_map = {}

        def id_for_testing(key):
            return id_map.setdefault(key.storage.allocation_id, len(id_map))

        lines = [
            f"{action.name.lower():<25}  {format_action(action, key, version):<25}  "
            f"{id_for_testing(key):>3}(v{version}) {format_size(size):>15}"
            for _, action, (key, version), size in prof._memory_profile().timeline
            # We generally don't care about tiny allocations during memory
            # profiling and they add a lot of noise to the unit test.
            if size > 1024 and isinstance(key, _memory_profiler.TensorKey)
        ]

        self.assertExpectedInline(
            textwrap.indent("\n".join(lines), " " * 12),
            """\
            preexisting                PARAMETER                    0(v0)          128 kB
            preexisting                PARAMETER                    1(v0)            2 kB
            preexisting                PARAMETER                    2(v0)         1024 kB
            create                     INPUT                        3(v0)          256 kB
            create                     INPUT                        4(v0)         2048 kB
            create                     ACTIVATION                   5(v0)         2048 kB
            create                     ACTIVATION                   6(v0)         2048 kB
            destroy                    ACTIVATION                   5(v0)         2048 kB
            create                     ACTIVATION                   7(v0)         2048 kB
            create                     ACTIVATION                   8(v0)         2048 kB
            destroy                    ACTIVATION                   7(v0)         2048 kB
            create                     ACTIVATION                   9(v0)         2048 kB
            create                     TEMPORARY                   10(v0)         2048 kB
            destroy                    TEMPORARY                   10(v0)         2048 kB
            create                     AUTOGRAD_DETAIL             11(v0)         2048 kB
            create                     AUTOGRAD_DETAIL             12(v0)         2048 kB
            destroy                    AUTOGRAD_DETAIL             11(v0)         2048 kB
            create                     GRADIENT                    13(v0)         1024 kB
            create                     AUTOGRAD_DETAIL             14(v0)         2048 kB
            destroy                    AUTOGRAD_DETAIL             12(v0)         2048 kB
            create                     AUTOGRAD_DETAIL             15(v0)         2048 kB
            destroy                    AUTOGRAD_DETAIL             14(v0)         2048 kB
            destroy                    ACTIVATION                   6(v0)         2048 kB
            create                     GRADIENT                    16(v0)          128 kB
            create                     GRADIENT                    17(v0)            2 kB
            destroy                    AUTOGRAD_DETAIL             15(v0)         2048 kB
            create                     OPTIMIZER_STATE             18(v0)          128 kB
            create                     OPTIMIZER_STATE             19(v0)          128 kB
            create                     OPTIMIZER_STATE             20(v0)            2 kB
            create                     OPTIMIZER_STATE             21(v0)            2 kB
            create                     OPTIMIZER_STATE             22(v0)         1024 kB
            create                     OPTIMIZER_STATE             23(v0)         1024 kB
            increment_version          OPTIMIZER_STATE             18(v0)          128 kB
            increment_version          OPTIMIZER_STATE             19(v0)          128 kB
            increment_version          OPTIMIZER_STATE             19(v1)          128 kB
            create                     ???                         24(v0)          128 kB
            create                     ???                         25(v0)          128 kB
            destroy                    ???                         24(v0)          128 kB
            increment_version          ???                         25(v0)          128 kB
            increment_version          PARAMETER                    0(v0)          128 kB
            increment_version          OPTIMIZER_STATE             20(v0)            2 kB
            increment_version          OPTIMIZER_STATE             21(v0)            2 kB
            increment_version          OPTIMIZER_STATE             21(v1)            2 kB
            create                     ???                         26(v0)            2 kB
            create                     ???                         27(v0)            2 kB
            destroy                    ???                         26(v0)            2 kB
            increment_version          ???                         27(v0)            2 kB
            destroy                    ???                         25(v1)          128 kB
            increment_version          PARAMETER                    1(v0)            2 kB
            increment_version          OPTIMIZER_STATE             22(v0)         1024 kB
            increment_version          OPTIMIZER_STATE             23(v0)         1024 kB
            increment_version          OPTIMIZER_STATE             23(v1)         1024 kB
            create                     ???                         28(v0)         1024 kB
            create                     ???                         29(v0)         1024 kB
            destroy                    ???                         28(v0)         1024 kB
            increment_version          ???                         29(v0)         1024 kB
            destroy                    ???                         27(v1)            2 kB
            increment_version          PARAMETER                    2(v0)         1024 kB
            destroy                    ???                         29(v1)         1024 kB
            destroy                    GRADIENT                    16(v0)          128 kB
            destroy                    GRADIENT                    17(v0)            2 kB
            destroy                    GRADIENT                    13(v0)         1024 kB""",
        )