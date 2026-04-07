def test_quoting(self):
        """
        #9655 - Check urlize doesn't overquote already quoted urls. The
        teststring is the urlquoted version of 'http://hi.baidu.com/重新开始'
        """
        self.assertEqual(
            urlize("http://hi.baidu.com/%E9%87%8D%E6%96%B0%E5%BC%80%E5%A7%8B"),
            '<a href="http://hi.baidu.com/%E9%87%8D%E6%96%B0%E5%BC%80%E5%A7%8B" '
            'rel="nofollow">http://hi.baidu.com/%E9%87%8D%E6%96%B0%E5%BC%80%E5%A7%8B'
            "</a>",
        )