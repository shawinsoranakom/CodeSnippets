def test_exhaustive_binary_op_rules(self):
        """
        Exhaustively test all placement combinations for binary ops.

        For each op, we define the complete set of valid rules. The test then:
        1. Verifies all listed rules are detected as valid
        2. Verifies all unlisted combinations are detected as invalid
        """

        def parse_rule(rule_str):
            """Parse 'S(0),S(0)->S(0)' into ((Shard(0), Shard(0)), Shard(0))."""
            inputs_str, output_str = rule_str.split("->")
            inputs = tuple(parse_placement(s.strip()) for s in inputs_str.split(","))
            return (inputs, (parse_placement(output_str.strip()),))

        # Valid rules for 2D binary ops with shape (8, 4)
        # Format: "input1,input2->output"
        # NOTE: These rules are for ground-truth validation (no redistribution).
        # Only placements that produce compatible local tensor shapes are valid.
        # - Shard(d) produces chunks (4,4) for d=0 or (8,2) for d=1
        # - Replicate and Partial produce full tensors (8,4)
        # So Shard can only pair with same-dim Shard, not with R or P.
        #
        # For Partial:
        # - P(sum) + P(sum) -> P(sum) works for add (sums distribute)
        # - R * P(sum) -> P(sum) works for mul (multiplication distributes into sum)
        # - P(sum) / R -> P(sum) works for div
        # But NOT:
        # - R + P(sum) -> P(sum) for add (R gets added on each rank, then summed)
        VALID_RULES = {
            torch.add: [
                # Same-dim sharding (chunks match)
                "S(0),S(0)->S(0)",
                "S(1),S(1)->S(1)",
                # Partial sum/avg + Partial sum/avg -> same (linearity of addition)
                # (a0+a1) + (b0+b1) = (a0+b0) + (a1+b1) where ai/bi are per-rank
                "P(sum),P(sum)->P(sum)",
                "P(avg),P(avg)->P(avg)",
                # Partial sum/avg with Replicate: avg normalizes the extra
                # copies, so P(avg)+R works even though P(sum)+R does not
                "P(avg),R->P(avg)",
                "R,P(avg)->P(avg)",
                # Partial max/min with Replicate: adding a constant preserves
                # the reduce structure (NOT Pmax+Pmax, offsets accumulate)
                "P(max),R->P(max)",
                "P(min),R->P(min)",
                # NOTE: these two rules are NOT valid in general for torch.add since it accepts alpha=a, which if negative
                # flips the partial output from max to min or vice versa.
                # However, this test is simpler than the end to end validator and ignores alpha, and the rules have to
                # be listed as valid since without alpha they DO produce correct results and the test asserts any rule
                # NOT listed here produces incorrect results.
                "R,P(max)->P(max)",
                "R,P(min)->P(min)",
            ],
            torch.mul: [
                # Same-dim sharding
                "S(0),S(0)->S(0)",
                "S(1),S(1)->S(1)",
                # Partial sum/avg * Replicate -> same (multiplicative linearity)
                # r * (p0+p1) = r*p0 + r*p1 where pi are per-rank
                "P(sum),R->P(sum)",
                "R,P(sum)->P(sum)",
                "P(avg),R->P(avg)",
                "R,P(avg)->P(avg)",
                # No P(min)/P(max) rules: negative multiplier flips ordering
            ],
            torch.div: [
                # Same-dim sharding
                "S(0),S(0)->S(0)",
                "S(1),S(1)->S(1)",
                # Partial sum/avg / Replicate -> same (division by constant is linear)
                "P(sum),R->P(sum)",
                "P(avg),R->P(avg)",
                # No R/P(avg) rule: 1/x is not linear
                # No P(min)/P(max) rules: negative divisor flips ordering
            ],
            torch.maximum: [
                # Same-dim sharding
                "S(0),S(0)->S(0)",
                "S(1),S(1)->S(1)",
                # Partial max + Partial max -> Partial max
                # max(max(a0,a1), max(b0,b1)) = max(max(a0,b0), max(a1,b1))
                "P(max),P(max)->P(max)",
                # Partial max/min with Replicate (lattice distributivity):
                # max(min(a0,a1), r) = min(max(a0,r), max(a1,r)) ✓
                "P(max),R->P(max)",
                "R,P(max)->P(max)",
                "P(min),R->P(min)",
                "R,P(min)->P(min)",
                # No P(avg) rules: max is not linear
            ],
        }

        # All possible placements for 2D tensor
        ALL_PLACEMENTS = [
            Replicate(),
            Shard(0),
            Shard(1),
            Partial("sum"),
            Partial("max"),
        ]
        if TEST_WITH_SLOW:
            # This makes the test go from 4 sec to 12 sec, and I don't think it really adds much useful coverage, but
            # why not have it run in CI.
            ALL_PLACEMENTS += [Partial("avg"), Partial("min")]

        # Test each operator
        for op, valid_rule_strs in VALID_RULES.items():
            valid_rules = {parse_rule(r) for r in valid_rule_strs}

            # Create test tensors
            a = torch.randn(8, 4)
            b = torch.randn(8, 4)
            sample = SampleInput(a, args=(b,))
            tensors = extract_tensors_from_sample(sample)
            ground_truth = op(a, b)

            with LocalTensorMode(frozenset(range(self.world_size))):
                mesh = init_device_mesh("cpu", (self.world_size,))

                # Test all combinations
                for p1 in ALL_PLACEMENTS:
                    for p2 in ALL_PLACEMENTS:
                        # Skip fully replicated inputs (degenerate case: any output works)
                        if isinstance(p1, Replicate) and isinstance(p2, Replicate):
                            continue

                        for p_out in ALL_PLACEMENTS:
                            input_plcs = (p1, p2)
                            combo = (input_plcs, (p_out,))

                            is_valid, msg = validate_combination(
                                op,
                                sample,
                                tensors,
                                combo,
                                ground_truth,
                                self.world_size,
                                mesh,
                            )

                            # Check if this combo matches any valid rule
                            should_be_valid = (input_plcs, (p_out,)) in valid_rules

                            if should_be_valid:
                                self.assertTrue(
                                    is_valid,
                                    f"{op.__name__}: {p1},{p2}->{p_out} should be valid but got: {msg}",
                                )
                            else:
                                self.assertFalse(
                                    is_valid,
                                    f"{op.__name__}: {p1},{p2}->{p_out} should be invalid",
                                )