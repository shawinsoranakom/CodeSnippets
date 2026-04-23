def test_solvability_report_well_formed(solvability_classifier, mock_llm_config):
    """Test that the SolvabilityReport is well-formed and all required fields are present."""
    issues = pd.Series(['Test issue', 'Another test issue'])
    labels = pd.Series([1, 0])
    # Fit the classifier
    solvability_classifier.fit(issues, labels, llm_config=mock_llm_config)

    report = solvability_classifier.solvability_report(
        issues.iloc[0], llm_config=mock_llm_config
    )

    # Generation of the report is a strong enough test (as it has to get past all
    # the pydantic validators). But just in case we can also double-check the field
    # values.
    assert report.identifier == solvability_classifier.identifier
    assert report.issue == issues.iloc[0]
    assert 0 <= report.score <= 1
    assert report.samples == solvability_classifier.samples
    assert set(report.features.keys()) == set(
        solvability_classifier.featurizer.feature_identifiers()
    )
    assert report.importance_strategy == solvability_classifier.importance_strategy
    assert set(report.feature_importances.keys()) == set(
        solvability_classifier.featurizer.feature_identifiers()
    )
    assert report.random_state == solvability_classifier.random_state
    assert report.created_at is not None
    assert report.prompt_tokens >= 0
    assert report.completion_tokens >= 0
    assert report.response_latency >= 0
    assert report.metadata is None