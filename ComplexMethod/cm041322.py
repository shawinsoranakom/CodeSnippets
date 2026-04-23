def test_can_parse_standard_format(self):
        """Test detection of standard checksum format."""
        parser = StandardFormat()

        # Valid standard formats
        assert parser.can_parse("d41d8cd98f00b204e9800998ecf8427e  file.txt")
        assert parser.can_parse(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  test.zip"
        )
        assert parser.can_parse("da39a3ee5e6b4b0d3255bfef95601890afd80709 *binary.exe")

        # Multiple lines
        content = """
d41d8cd98f00b204e9800998ecf8427e  file1.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  file2.zip
"""
        assert parser.can_parse(content)

        # Invalid formats
        assert not parser.can_parse("SHA256 (file.txt) = d41d8cd98f00b204e9800998ecf8427e")
        assert not parser.can_parse("file.txt: d41d8cd98f00b204e9800998ecf8427e")
        assert not parser.can_parse("just some random text")
        assert not parser.can_parse("")