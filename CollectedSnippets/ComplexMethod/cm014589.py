def main():
    parser = argparse.ArgumentParser(
        description="Evaluate trained AutoHeuristics for pad_mm optimization"
    )
    parser.add_argument("csv_file", help="Path to CSV file with M,K,N,dtype columns")
    parser.add_argument(
        "--num-reps", type=int, default=3, help="Benchmark repetitions (default: 3)"
    )
    parser.add_argument(
        "--device", type=int, default=None, help="CUDA device (default: current)"
    )
    parser.add_argument(
        "--max-shapes",
        type=int,
        default=10000,
        help="Max shapes to test (default: 10000)",
    )
    parser.add_argument(
        "--float32_matmul_precision",
        type=str,
        choices=["high", "highest"],
        default="highest",
        help="Matmul precision for float32 (default: highest). Non-fp32 always uses 'high'.",
    )

    args = parser.parse_args()

    torch.set_default_device("cuda")
    if args.device is not None:
        torch.cuda.set_device(args.device)

    print(f"Using CUDA device: {torch.cuda.current_device()}")
    print()

    shapes = load_shapes_from_csv(args.csv_file)
    if not shapes:
        print("No shapes found!")
        return

    shapes = filter_shapes(shapes)
    if not shapes:
        print("No suitable shapes found!")
        return

    if len(shapes) > args.max_shapes:
        shapes = shapes[: args.max_shapes]
        print(f"Limited to first {args.max_shapes} shapes")

    print(f"Evaluating {len(shapes)} shapes with {args.num_reps} reps each")
    print()

    total_decisions = 0
    correct_decisions = 0
    true_positives = 0  # Chose pad, should pad
    true_negatives = 0  # Chose orig, should orig
    false_positives = 0  # Chose pad, should orig
    false_negatives = 0  # Chose orig, should pad
    no_decision_shapes = 0

    tp_speedups = []  # Speed-up percentages for true positives
    fp_slowdowns = []  # Speed-down percentages for false positives

    # Track non-confident decisions and confident decisions by dtype
    no_decision_shape_list = []  # List of (M, K, N, dtype) where heuristic chose no_decision
    confident_by_dtype = {}  # Count of confident decisions by dtype

    for i, (m, k, n, dtype) in enumerate(shapes, 1):
        print(f"Shape {i}/{len(shapes)}: M={m}, K={k}, N={n}, dtype={dtype}")

        heuristic_choice = get_heuristic_decision(m, k, n, dtype)
        print(f"  Heuristic: {heuristic_choice}")

        orig_time, pad_time = benchmark_both_choices(
            m, k, n, dtype, args.num_reps, args.float32_matmul_precision
        )
        ground_truth = "pad" if pad_time < orig_time else "orig"

        print(f"  Times: orig={orig_time:.6f}s, pad={pad_time:.6f}s")
        print(f"  Ground truth: {ground_truth}")

        if heuristic_choice == "no_decision":
            # Heuristic punted to benchmarking - this is correct behavior for small/uncertain shapes
            no_decision_shapes += 1
            no_decision_shape_list.append((m, k, n, dtype))
            print("  Heuristic chose to benchmark (conservative)")
        else:
            # Heuristic made a confident decision - evaluate accuracy
            total_decisions += 1
            # Track confident decisions by dtype
            dtype_str = str(dtype).replace("torch.", "")
            confident_by_dtype[dtype_str] = confident_by_dtype.get(dtype_str, 0) + 1
            if heuristic_choice == ground_truth:
                correct_decisions += 1
                print("  ✓ CORRECT")
                if heuristic_choice == "pad":
                    true_positives += 1  # Correctly chose pad
                    # Calculate speed-up: (orig_time - pad_time) / orig_time * 100
                    speedup = (orig_time - pad_time) / orig_time * 100
                    tp_speedups.append(speedup)
                    print(f"    Speed-up: {speedup:.1f}%")
                else:
                    true_negatives += 1  # Correctly chose orig
            else:
                print("  ✗ WRONG")
                if heuristic_choice == "pad" and ground_truth == "orig":
                    false_positives += 1
                    # Calculate speed-down: (pad_time - orig_time) / orig_time * 100
                    slowdown = (pad_time - orig_time) / orig_time * 100
                    fp_slowdowns.append(slowdown)
                    print(f"    Speed-down: {slowdown:.1f}%")
                elif heuristic_choice == "orig" and ground_truth == "pad":
                    false_negatives += 1

        print(f"  Confidence Rate: {total_decisions}/{i}")
        if total_decisions > 0:
            accuracy = correct_decisions / total_decisions * 100
            tp_rate = true_positives / total_decisions * 100
            tn_rate = true_negatives / total_decisions * 100
            fp_rate = false_positives / total_decisions * 100
            fn_rate = false_negatives / total_decisions * 100

            # Compute average speedup/slowdown
            avg_tp_speedup = sum(tp_speedups) / len(tp_speedups) if tp_speedups else 0
            avg_fp_slowdown = (
                sum(fp_slowdowns) / len(fp_slowdowns) if fp_slowdowns else 0
            )

            print(
                f"  Accuracy: {correct_decisions}/{total_decisions} ({accuracy:.1f}%) "
                f"| TP: {tp_rate:.1f}% (avg speedup: {avg_tp_speedup:.1f}%) "
                f"| TN: {tn_rate:.1f}% "
                f"| FP: {fp_rate:.1f}% (avg slowdown: {avg_fp_slowdown:.1f}%)"
                f"| FN: {fn_rate:.1f}%"
            )

        print()

    print("=== FINAL RESULTS ===")
    print(f"Confident decisions: {total_decisions}")
    print(f"#Shapes without confident decisions: {no_decision_shapes}")

    if total_decisions > 0:
        accuracy = correct_decisions / total_decisions * 100
        tp_rate = true_positives / total_decisions * 100
        tn_rate = true_negatives / total_decisions * 100
        fp_rate = false_positives / total_decisions * 100
        fn_rate = false_negatives / total_decisions * 100

        avg_tp_speedup = sum(tp_speedups) / len(tp_speedups) if tp_speedups else 0
        avg_fp_slowdown = sum(fp_slowdowns) / len(fp_slowdowns) if fp_slowdowns else 0

        print(
            f"\nConfident decision accuracy: {accuracy:.1f}% ({correct_decisions}/{total_decisions})"
        )

        if tp_speedups:
            print(
                f"True Positives (chose pad, should pad): {tp_rate:.1f}% ({true_positives}) "
                f"| Avg speed-up: {avg_tp_speedup:.1f}%"
            )
        else:
            print(
                f"True Positives (chose pad, should pad): {tp_rate:.1f}% ({true_positives})"
            )

        print(
            f"True Negatives (chose orig, should orig): {tn_rate:.1f}% ({true_negatives})"
        )

        if fp_slowdowns:
            print(
                f"False Positives (chose pad, should orig): {fp_rate:.1f}% ({false_positives}) "
                f"| Avg speed-down: {avg_fp_slowdown:.1f}%"
            )
        else:
            print(
                f"False Positives (chose pad, should orig): {fp_rate:.1f}% ({false_positives})"
            )

        print(
            f"False Negatives (chose orig, should pad): {fn_rate:.1f}% ({false_negatives})"
        )
    else:
        print("No confident decisions made!")

    total_evaluated = total_decisions + no_decision_shapes
    if total_evaluated > 0:
        print(
            f"\nConfidence rate: ({total_decisions}/{total_evaluated} made confident decisions)"
        )

    # Print shapes where AutoHeuristics did not make a confident decision
    print(f"\n=== NON-CONFIDENT DECISIONS ({len(no_decision_shape_list)}) ===")
    if no_decision_shape_list:
        print("Shapes where AutoHeuristics chose 'no_decision' (non-confident):")
        for m, k, n, dtype in no_decision_shape_list:
            dtype_str = str(dtype).replace("torch.", "")
            print(f"  M={m}, K={k}, N={n}, dtype={dtype_str}")
    else:
        print("All shapes had confident decisions!")

    # Print confident decisions by dtype
    print("\n=== CONFIDENT DECISIONS BY DTYPE ===")
    if confident_by_dtype:
        print("Number of confident decisions per dtype:")
        for dtype_str, count in sorted(confident_by_dtype.items()):
            print(f"  {dtype_str}: {count} confident decisions")
        print(f"Total confident decisions: {sum(confident_by_dtype.values())}")
    else:
        print("No confident decisions made!")