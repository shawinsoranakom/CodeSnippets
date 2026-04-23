def test_parse_atom_response(self, component_class, default_kwargs):
        # Arrange
        component = component_class(**default_kwargs)
        sample_xml = """<feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:arxiv="http://arxiv.org/schemas/atom">
            <entry>
                <id>http://arxiv.org/abs/quant-ph/0000001</id>
                <title>Test Paper</title>
                <summary>Test summary</summary>
                <published>2023-01-01</published>
                <updated>2023-01-01</updated>
                <author><name>Test Author</name></author>
                <link rel="alternate" href="http://arxiv.org/abs/quant-ph/0000001"/>
                <link rel="related" href="http://arxiv.org/pdf/quant-ph/0000001"/>
                <category term="quant-ph" scheme="http://arxiv.org/schemas/atom"/>
                <arxiv:comment>Test comment</arxiv:comment>
                <arxiv:journal_ref>Test Journal</arxiv:journal_ref>
                <arxiv:primary_category term="quant-ph"/>
            </entry>
        </feed>""".replace("<", "<").replace(">", ">")

        # Act
        papers = component.parse_atom_response(sample_xml)

        # Assert
        assert len(papers) == 1
        paper = papers[0]
        assert paper["title"] == "Test Paper"
        assert paper["summary"] == "Test summary"
        assert paper["authors"] == ["Test Author"]
        assert paper["arxiv_url"] == "http://arxiv.org/abs/quant-ph/0000001"
        assert paper["pdf_url"] == "http://arxiv.org/pdf/quant-ph/0000001"
        assert paper["comment"] == "Test comment"
        assert paper["journal_ref"] == "Test Journal"
        assert paper["primary_category"] == "quant-ph"