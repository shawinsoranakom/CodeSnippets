def summarize_results(self, results):
        dev_scores = [result["score_dict"]["dev_score"] for result in results]
        best_dev_score = (
            max(dev_scores)
            if not self.args.low_is_better
            else min([score for score in dev_scores if score != -1] + [np.inf])
        )
        best_score_idx = dev_scores.index(best_dev_score)

        test_scores = [result["score_dict"]["test_score"] for result in results]
        avg_score = sum(test_scores) / len(test_scores)
        global_best_score = (
            max(test_scores)
            if not self.args.low_is_better
            else min([score for i, score in enumerate(test_scores) if dev_scores[i] != -1] + [np.inf])
        )

        results.insert(
            0,
            {
                "best_dev_score": best_dev_score,
                "best_dev_score_idx": best_score_idx,
                "best_dev_test_score": test_scores[best_score_idx],
                "avg_test_score": avg_score,
                "global_best_test_score": global_best_score,
            },
        )
        return results