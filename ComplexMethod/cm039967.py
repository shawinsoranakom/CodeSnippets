def test_is_multilabel():
    for group, group_examples in EXAMPLES.items():
        dense_exp = group == "multilabel-indicator"

        for example in group_examples:
            # Only mark explicitly defined sparse examples as valid sparse
            # multilabel-indicators
            sparse_exp = dense_exp and issparse(example)

            if issparse(example) or (
                hasattr(example, "__array__")
                and np.asarray(example).ndim == 2
                and np.asarray(example).dtype.kind in "biuf"
                and np.asarray(example).shape[1] > 0
            ):
                examples_sparse = [
                    sparse_container(example)
                    for sparse_container in (
                        COO_CONTAINERS
                        + CSC_CONTAINERS
                        + CSR_CONTAINERS
                        + DOK_CONTAINERS
                        + LIL_CONTAINERS
                    )
                ]
                for exmpl_sparse in examples_sparse:
                    assert sparse_exp == is_multilabel(exmpl_sparse), (
                        f"is_multilabel({exmpl_sparse!r}) should be {sparse_exp}"
                    )

            # Densify sparse examples before testing
            if issparse(example):
                example = example.toarray()

            assert dense_exp == is_multilabel(example), (
                f"is_multilabel({example!r}) should be {dense_exp}"
            )