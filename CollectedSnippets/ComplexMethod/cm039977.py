def test_features_html_structure():
    """Test that HTML structure contains expected elements."""
    features = ["feat1", "feat2"]
    html = _features_html(features)

    assert "<details>" in html
    assert "<summary>" in html
    assert "</summary>" in html
    assert "</details>" in html
    assert '<table class="features-table">' in html
    assert "<tbody>" in html
    assert "</tbody>" in html
    assert '<i class="copy-paste-icon"' in html
    assert "copyFeatureNamesToClipboard" in html