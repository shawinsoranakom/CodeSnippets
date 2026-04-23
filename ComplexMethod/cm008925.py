def test_happy_path_splitting_based_on_header_with_whitespace_chars() -> None:
    # arrange
    html_string = """<!DOCTYPE html>
            <html>
            <body>
                <div>
                    <span style="font-size: 22px">\nFoo </span>
                    <p>Some intro text about Foo.</p>
                    <div>
                        <h2>Bar main section</h2>
                        <p>Some intro text about Bar.</p>
                        <h3>Bar subsection 1</h3>
                        <p>Some text about the first subtopic of Bar.</p>
                        <h3>Bar subsection 2</h3>
                        <p>Some text about the second subtopic of Bar.</p>
                    </div>
                    <div>
                        <h2>Baz</h2>
                        <p>Some text about Baz</p>
                    </div>
                    <br>
                    <p>Some concluding text about Foo</p>
                </div>
            </body>
            </html>"""

    sec_splitter = HTMLSectionSplitter(
        headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2")]
    )

    docs = sec_splitter.split_text(html_string)

    assert len(docs) == 3
    assert docs[0].page_content == "Foo  \n Some intro text about Foo."
    assert docs[0].metadata["Header 1"] == "Foo"

    assert docs[1].page_content == (
        "Bar main section \n Some intro text about Bar. \n "
        "Bar subsection 1 \n Some text about the first subtopic of Bar. \n "
        "Bar subsection 2 \n Some text about the second subtopic of Bar."
    )
    assert docs[1].metadata["Header 2"] == "Bar main section"

    assert docs[2].page_content == (
        "Baz \n Some text about Baz \n \n \n Some concluding text about Foo"
    )
    assert docs[2].metadata["Header 2"] == "Baz"