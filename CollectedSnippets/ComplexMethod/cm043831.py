def test_parse_label_linkbase_documentation(self, us_gaap_doc_bytes):
        """FASB documentation lives in a separate *-doc-{year}.xml file."""
        p = XBRLParser()
        result = p.parse_label_linkbase(
            BytesIO(us_gaap_doc_bytes), TaxonomyStyle.FASB_STANDARD
        )

        all_roles: set[str] = set()
        for v in result.values():
            all_roles.update(v.keys())
        assert "documentation" in all_roles

        assert len(result) > 10000, f"Only {len(result)} doc entries"
        assert len(p.documentation) > 10000

        assets_docs = [
            v for k, v in p.documentation.items() if k.split("_")[-1] == "Assets"
        ]
        assert len(assets_docs) > 0, "No documentation for 'Assets'"
        assert len(assets_docs[0]) > 20, "Assets documentation is too short"