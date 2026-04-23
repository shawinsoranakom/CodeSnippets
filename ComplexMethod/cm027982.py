def interactive_mode():
    """Interactive mode for analyzing product reviews"""
    print("=== Interactive Product Review Analysis ===")
    print("Paste a product review and I'll extract structured data from it.")
    print("Type 'quit' to exit.")
    print()

    while True:
        review_text = input("Product Review: ").strip()

        if review_text.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break

        if not review_text:
            continue

        try:
            print("\nAnalyzing review...")
            result = Runner.run_sync(product_review_agent, review_text)
            analysis = result.final_output

            print("\n" + "="*50)
            print("📊 REVIEW ANALYSIS COMPLETE")
            print("="*50)

            # Product Information
            print("🏷️  PRODUCT INFO:")
            print(f"   Name: {analysis.product_info.name or 'Not specified'}")
            print(f"   Brand: {analysis.product_info.brand or 'Not specified'}")
            print(f"   Category: {analysis.product_info.category.value.title()}")
            if analysis.product_info.price_mentioned:
                print(f"   Price: {analysis.product_info.price_mentioned}")

            # Metrics
            print(f"\n📊 METRICS:")
            print(f"   Rating: {analysis.metrics.rating}/5 ⭐")
            print(f"   Sentiment: {analysis.metrics.sentiment.value.replace('_', ' ').title()}")
            print(f"   Confidence: {analysis.metrics.confidence_score:.1%}")

            # Key Points
            if analysis.main_positives:
                print(f"\n✅ POSITIVES: {', '.join(analysis.main_positives)}")
            if analysis.main_negatives:
                print(f"\n❌ NEGATIVES: {', '.join(analysis.main_negatives)}")

            # Summary
            print(f"\n📋 SUMMARY: {analysis.summary}")

            print("="*50)
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()