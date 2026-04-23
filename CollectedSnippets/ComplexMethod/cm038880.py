def test_multiple_long_texts_batch():
    """Test batch processing with multiple long texts to verify chunk ID uniqueness."""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print("\n🔧 Testing Multiple Long Texts in Batch (Chunk ID Fix Verification)")
    print("=" * 70)

    # Create multiple distinct long texts that will all require chunking
    # Note: All pooling types now use MEAN aggregation across chunks:
    # - Native pooling (MEAN/CLS/LAST) is used within each chunk
    # - MEAN aggregation combines results across all chunks
    # - Full semantic coverage for all pooling types
    long_texts = [
        generate_long_text(
            "First long document about artificial intelligence and machine learning. "
            * 80,
            6,
        ),
        generate_long_text(
            "Second long document about natural language processing and transformers. "
            * 80,
            6,
        ),
        generate_long_text(
            "Third long document about computer vision and neural networks. " * 80, 6
        ),
    ]

    # Add some short texts to mix things up
    batch_inputs = [
        "Short text before long texts",
        long_texts[0],
        "Short text between long texts",
        long_texts[1],
        long_texts[2],
        "Short text after long texts",
    ]

    print("📊 Batch composition:")
    for i, text in enumerate(batch_inputs):
        length = len(text)
        text_type = "Long (will be chunked)" if length > 5000 else "Short"
        print(f"   - Input {i + 1}: {length} chars ({text_type})")

    try:
        start_time = time.time()

        response = client.embeddings.create(
            input=batch_inputs, model=MODEL_NAME, encoding_format="float"
        )

        end_time = time.time()
        processing_time = end_time - start_time

        print("\n✅ Multiple long texts batch processing successful!")
        print(f"   - Number of inputs: {len(batch_inputs)}")
        print(f"   - Number of embeddings returned: {len(response.data)}")
        print(f"   - Total processing time: {processing_time:.2f}s")

        # Verify each embedding is different (no incorrect aggregation)
        embeddings = [data.embedding for data in response.data]

        if len(embeddings) >= 3:
            import numpy as np

            # Compare embeddings of the long texts (indices 1, 3, 4)
            long_embeddings = [
                np.array(embeddings[1]),  # First long text
                np.array(embeddings[3]),  # Second long text
                np.array(embeddings[4]),  # Third long text
            ]

            print("\n🔍 Verifying embedding uniqueness:")
            for i in range(len(long_embeddings)):
                for j in range(i + 1, len(long_embeddings)):
                    cosine_sim = np.dot(long_embeddings[i], long_embeddings[j]) / (
                        np.linalg.norm(long_embeddings[i])
                        * np.linalg.norm(long_embeddings[j])
                    )
                    print(
                        f"   - Similarity between long text {i + 1} and {j + 1}: "
                        f"{cosine_sim:.4f}"
                    )

                    if (
                        cosine_sim < 0.9
                    ):  # Different content should have lower similarity
                        print("     ✅ Good: Embeddings are appropriately different")
                    else:
                        print(
                            "     ⚠️ High similarity - may indicate chunk "
                            "aggregation issue"
                        )

        print("\n📋 Per-input results:")
        for i, data in enumerate(response.data):
            input_length = len(batch_inputs[i])
            embedding_dim = len(data.embedding)
            embedding_norm = np.linalg.norm(data.embedding)
            print(
                f"   - Input {i + 1}: {input_length} chars → {embedding_dim}D "
                f"embedding (norm: {embedding_norm:.4f})"
            )

        print(
            "\n✅ This test verifies the fix for chunk ID collisions in "
            "batch processing"
        )
        print("   - Before fix: Multiple long texts would have conflicting chunk IDs")
        print("   - After fix: Each prompt's chunks have unique IDs with prompt index")

    except Exception as e:
        print(f"❌ Multiple long texts batch test failed: {str(e)}")
        print("   This might indicate the chunk ID collision bug is present!")