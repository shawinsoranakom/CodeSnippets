def parse(self):
                post, files = super().parse()
                post._mutable = True
                post["custom_parser_used"] = "yes"
                post._mutable = False
                return post, files