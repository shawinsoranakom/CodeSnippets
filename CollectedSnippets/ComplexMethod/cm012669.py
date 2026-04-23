def tile_ranges(is_pointwise: bool, ranges, rw) -> list[CandidateTiling]:
            """
            Compute tiling candidates by dividing up the iteration ranges.
            """
            assert len(rw.range_vars) == len(ranges), f"{rw.range_vars=} {ranges=}"

            # isinstance(dep, MemoryDep): this filters out StarDeps. StarDeps refer to reads
            # that need to access the entire tensor; they don't contribute read indexing
            # information (and practically, they don't have dep.index so they can't be used
            # for stride_hints below
            dep_sources = [rw.reads, rw.writes]
            assert all(
                isinstance(dep, (MemoryDep, StarDep))
                for dep in itertools.chain.from_iterable(dep_sources)
            )
            deps = [
                dep
                for dep in itertools.chain.from_iterable(dep_sources)
                if dep.name not in V.graph.removed_buffers
                and isinstance(dep, MemoryDep)
            ]
            write_names = OrderedSet([dep.name for dep in rw.writes])

            def collapse_ranges(ranges: Sequence[sympy.Expr]) -> sympy.Expr:
                return V.graph.sizevars.simplify(sympy_product(ranges))

            # Default to no tiling.
            tilings = [
                CandidateTiling(
                    tiling=cls.create_partial_tiling(
                        [collapse_ranges(ranges)], is_pointwise
                    ),
                    name="none",
                    score=0,
                )
            ]

            # Find non-trivial tiling candidates.
            for dep in deps:
                strides = V.graph.sizevars.stride_hints(dep.index, rw.range_vars)
                assert len(strides) == len(ranges)
                try:
                    split = strides.index(1) + 1
                    if split == len(ranges):
                        continue
                    if all(s == 0 for s in strides[split:]):
                        # if this is a broadcasted tensor and all dimensions after split are broadcast,
                        # this is not a real split
                        continue

                except ValueError:
                    continue

                tiled_groups = (
                    collapse_ranges(ranges[:split]),
                    collapse_ranges(ranges[split:]),
                )

                # score by number of elements
                score = V.graph.sizevars.optimization_hint(
                    sympy_product(
                        size for size, stride in zip(ranges, strides) if stride != 0
                    )
                )
                if dep.name in write_names:
                    # ngimel said contiguous writes is more important than reads
                    score *= 2
                if CandidateTiling.is_good_size(tiled_groups[0]):
                    score *= 2
                if CandidateTiling.is_good_size(tiled_groups[1]):
                    score *= 2

                if (
                    V.graph.sizevars.optimization_hint(
                        score - sympy_product(itertools.chain(ranges, reduction_ranges))
                    )
                    >= 0
                ):
                    tilings.append(
                        CandidateTiling(
                            tiling=cls.create_partial_tiling(
                                [
                                    collapse_ranges(ranges[:split]),
                                    collapse_ranges(ranges[split:]),
                                ],
                                reduction_numel,
                            ),
                            score=score,
                            name=dep.name,
                        )
                    )

            return tilings