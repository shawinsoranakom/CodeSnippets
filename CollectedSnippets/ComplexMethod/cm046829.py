def compare_aime_results(all_results):
    """Generate comprehensive comparison for AIME evaluation results"""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE AIME MODEL COMPARISON")
    print(f"{'='*80}")

    # Main comparison table
    print(
        f"{'Model':<15} {'Accuracy %':<12} {'Pass@K %':<10} {'Correct':<8} {'Total':<8}"
    )
    print("-" * 80)

    for result in all_results:
        print(
            f"{result['model_type']:<15} "
            f"{result['accuracy']:<12.1f} "
            f"{result['pass_at_k']:<10.1f} "
            f"{result['correct_answers']:<8} "
            f"{result['total_problems']:<8}"
        )

    # Performance improvement analysis
    if len(all_results) > 1:
        print(f"\n{'='*50}")
        print("IMPROVEMENT ANALYSIS")
        print(f"{'='*50}")

        base_result = all_results[0]  # Assume first is base model

        for i, result in enumerate(all_results[1:], 1):
            print(f"\n{result['model_type']} vs {base_result['model_type']}:")

            accuracy_improvement = result["accuracy"] - base_result["accuracy"]
            pass_k_improvement = result["pass_at_k"] - base_result["pass_at_k"]

            print(f"  Accuracy improvement:  {accuracy_improvement:+.1f}%")
            print(f"  Pass@K improvement:    {pass_k_improvement:+.1f}%")

    # Dataset breakdown
    print(f"\n{'='*50}")
    print("PERFORMANCE BY DATASET")
    print(f"{'='*50}")

    # Get all unique datasets from the first result
    if all_results and "source_accuracies" in all_results[0]:
        datasets = list(all_results[0]["source_accuracies"].keys())

        print(f"{'Model':<15}", end = "")
        for dataset in datasets:
            print(f"{dataset:<15}", end = "")
        print()
        print("-" * (15 + 15 * len(datasets)))

        for result in all_results:
            print(f"{result['model_type']:<15}", end = "")
            for dataset in datasets:
                accuracy = result["source_accuracies"].get(dataset, 0)
                print(f"{accuracy:<15.1f}", end = "")
            print()

    # Save comparison
    comparison_data = {
        "summary": all_results,
        "best_model": max(all_results, key = lambda x: x["accuracy"]),
    }

    with open("aime_model_comparison.json", "w") as f:
        json.dump(comparison_data, f, indent = 4)

    print(
        f"\nBest performing model: {comparison_data['best_model']['model_type']} "
        f"({comparison_data['best_model']['accuracy']:.1f}% accuracy)"
    )