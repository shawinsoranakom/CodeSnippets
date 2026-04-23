def demonstrate_review_analysis():
    """Demonstrate the product review agent with various examples"""
    print("🎯 OpenAI Agents SDK - Tutorial 2: Product Review Agent")
    print("=" * 60)
    print()

    # Test cases with different types of reviews
    test_reviews = [
        {
            "title": "Positive Electronics Review",
            "review": "This MacBook Pro M2 is absolutely incredible! The battery life lasts all day, the screen is gorgeous, and it's lightning fast. Worth every penny of the $2,499 I paid. Apple really knocked it out of the park. The build quality is premium and it handles video editing like a dream. Highly recommend to any creative professional!"
        },
        {
            "title": "Mixed Clothing Review", 
            "review": "The Nike running shoes are decent for the price ($120). Comfortable for short runs but the sizing runs a bit small. Quality seems okay but not amazing. Shipping was fast though, arrived in 2 days. Customer service was helpful when I had questions. Would maybe recommend if you size up."
        },
        {
            "title": "Negative Food Review",
            "review": "Terrible experience with this organic coffee subscription. The beans taste stale and bitter, nothing like the description. Customer service ignored my complaints for weeks. Way overpriced at $35/month for this quality. Save your money and buy local. Will not be ordering again."
        },
        {
            "title": "Neutral Home Product Review",
            "review": "The IKEA desk lamp does its job. Easy to assemble and decent lighting for work. Not the brightest but sufficient. Build quality is what you'd expect for $25. The cord could be longer. It's an okay purchase, nothing special but functional."
        }
    ]

    for i, test_case in enumerate(test_reviews, 1):
        print(f"=== Review Analysis {i}: {test_case['title']} ===")
        print("Original Review:")
        print(f'"{test_case["review"]}"')
        print()

        try:
            # Analyze the review
            result = Runner.run_sync(product_review_agent, test_case["review"])
            analysis = result.final_output

            print("📊 STRUCTURED ANALYSIS:")
            print(f"🏷️  Product: {analysis.product_info.name or 'Not specified'}")
            print(f"🏢 Brand: {analysis.product_info.brand or 'Not specified'}")
            print(f"📱 Category: {analysis.product_info.category.value.title()}")
            if analysis.product_info.price_mentioned:
                print(f"💰 Price: {analysis.product_info.price_mentioned}")

            print(f"\n⭐ Rating: {analysis.metrics.rating}/5 stars")
            print(f"😊 Sentiment: {analysis.metrics.sentiment.value.replace('_', ' ').title()}")
            print(f"🎯 Confidence: {analysis.metrics.confidence_score:.1%}")
            print(f"📝 Word Count: ~{analysis.metrics.word_count}")

            if analysis.main_positives:
                print(f"\n✅ Positives: {', '.join(analysis.main_positives)}")
            if analysis.main_negatives:
                print(f"❌ Negatives: {', '.join(analysis.main_negatives)}")

            if analysis.would_recommend is not None:
                recommend_text = "Yes" if analysis.would_recommend else "No"
                print(f"👍 Would Recommend: {recommend_text}")

            print(f"\n📋 Summary: {analysis.summary}")

            if analysis.key_phrases:
                print(f"🔑 Key Phrases: {', '.join(analysis.key_phrases)}")

            # Show aspects that were mentioned
            aspects_mentioned = []
            if analysis.aspects.quality:
                aspects_mentioned.append(f"Quality: {analysis.aspects.quality}")
            if analysis.aspects.value_for_money:
                aspects_mentioned.append(f"Value: {analysis.aspects.value_for_money}")
            if analysis.aspects.shipping:
                aspects_mentioned.append(f"Shipping: {analysis.aspects.shipping}")
            if analysis.aspects.customer_service:
                aspects_mentioned.append(f"Service: {analysis.aspects.customer_service}")
            if analysis.aspects.ease_of_use:
                aspects_mentioned.append(f"Usability: {analysis.aspects.ease_of_use}")

            if aspects_mentioned:
                print(f"\n🔍 Specific Aspects: {' | '.join(aspects_mentioned)}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print()
        print("-" * 60)
        print()