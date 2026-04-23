def parser_txt(cls, txt, chunk_token_num):
        if not isinstance(txt, str):
            raise TypeError("txt type should be string!")

        temp_sections = []
        soup = BeautifulSoup(txt, "html5lib")
        # delete <style> tag
        for style_tag in soup.find_all(["style", "script"]):
            style_tag.decompose()
        # delete <script> tag in <div>
        for div_tag in soup.find_all("div"):
            for script_tag in div_tag.find_all("script"):
                script_tag.decompose()
        # delete inline style
        for tag in soup.find_all(True):
            if 'style' in tag.attrs:
                del tag.attrs['style']
        # delete HTML comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        cls.read_text_recursively(soup.body, temp_sections, chunk_token_num=chunk_token_num)
        block_txt_list, table_list = cls.merge_block_text(temp_sections)
        sections = cls.chunk_block(block_txt_list, chunk_token_num=chunk_token_num)
        for table in table_list:
            sections.append(table.get("content", ""))
        return sections