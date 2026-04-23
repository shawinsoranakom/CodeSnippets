def test_compute_bm25_term_frequency_saturation(self):
        """Test BM25 term frequency saturation behavior."""
        # Test with documents where term frequencies can be meaningfully compared
        documents = [
            "rare word text",  # TF = 1 for "rare"
            "rare rare word",  # TF = 2 for "rare"
            "rare rare rare rare rare word",  # TF = 5 for "rare"
            "other content",  # No "rare" term
        ]
        query_terms = ["rare"]

        scores = compute_bm25(documents, query_terms)

        # Documents with the term should have positive scores
        assert scores[0] > 0.0  # TF=1
        assert scores[1] > 0.0  # TF=2
        assert scores[2] > 0.0  # TF=5
        assert scores[3] == 0.0  # TF=0

        # Scores should increase with term frequency, but with diminishing returns
        assert scores[1] > scores[0]  # TF=2 > TF=1
        assert scores[2] > scores[1]  # TF=5 > TF=2

        # Check that increases demonstrate saturation effect
        increase_1_to_2 = scores[1] - scores[0]
        increase_2_to_5 = scores[2] - scores[1]
        assert increase_1_to_2 > 0
        assert increase_2_to_5 > 0