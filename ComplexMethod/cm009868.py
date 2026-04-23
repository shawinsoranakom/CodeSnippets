def _cosine_distance(a: Any, b: Any) -> Any:
        """Compute the cosine distance between two vectors.

        Args:
            a (np.ndarray): The first vector.
            b (np.ndarray): The second vector.

        Returns:
            np.ndarray: The cosine distance.
        """
        try:
            from langchain_core.vectorstores.utils import _cosine_similarity

            return 1.0 - _cosine_similarity(a, b)
        except ImportError:
            # Fallback to scipy if available
            try:
                from scipy.spatial.distance import cosine

                return cosine(a.flatten(), b.flatten())
            except ImportError:
                # Pure numpy fallback
                if _check_numpy():
                    np = _import_numpy()
                    a_flat = a.flatten()
                    b_flat = b.flatten()
                    dot_product = np.dot(a_flat, b_flat)
                    norm_a = np.linalg.norm(a_flat)
                    norm_b = np.linalg.norm(b_flat)
                    if norm_a == 0 or norm_b == 0:
                        return 0.0
                    return 1.0 - (dot_product / (norm_a * norm_b))
                # Pure Python implementation
                a_flat = a if hasattr(a, "__len__") else [a]
                b_flat = b if hasattr(b, "__len__") else [b]
                if hasattr(a, "flatten"):
                    a_flat = a.flatten()
                if hasattr(b, "flatten"):
                    b_flat = b.flatten()

                dot_product = sum(x * y for x, y in zip(a_flat, b_flat, strict=False))
                norm_a = sum(x * x for x in a_flat) ** 0.5
                norm_b = sum(x * x for x in b_flat) ** 0.5
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                return 1.0 - (dot_product / (norm_a * norm_b))