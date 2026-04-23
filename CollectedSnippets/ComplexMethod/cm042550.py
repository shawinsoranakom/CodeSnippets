def test_file_path(self):
        file_path = self.pipeline.file_path
        assert (
            file_path(Request("https://dev.mydeco.com/mydeco.gif"))
            == "full/3fd165099d8e71b8a48b2683946e64dbfad8b52d.jpg"
        )
        assert (
            file_path(
                Request(
                    "http://www.maddiebrown.co.uk///catalogue-items//image_54642_12175_95307.jpg"
                )
            )
            == "full/0ffcd85d563bca45e2f90becd0ca737bc58a00b2.jpg"
        )
        assert (
            file_path(
                Request("https://dev.mydeco.com/two/dirs/with%20spaces%2Bsigns.gif")
            )
            == "full/b250e3a74fff2e4703e310048a5b13eba79379d2.jpg"
        )
        assert (
            file_path(
                Request(
                    "http://www.dfsonline.co.uk/get_prod_image.php?img=status_0907_mdm.jpg"
                )
            )
            == "full/4507be485f38b0da8a0be9eb2e1dfab8a19223f2.jpg"
        )
        assert (
            file_path(Request("http://www.dorma.co.uk/images/product_details/2532/"))
            == "full/97ee6f8a46cbbb418ea91502fd24176865cf39b2.jpg"
        )
        assert (
            file_path(Request("http://www.dorma.co.uk/images/product_details/2532"))
            == "full/244e0dd7d96a3b7b01f54eded250c9e272577aa1.jpg"
        )
        assert (
            file_path(
                Request("http://www.dorma.co.uk/images/product_details/2532"),
                response=Response("http://www.dorma.co.uk/images/product_details/2532"),
                info=object(),
            )
            == "full/244e0dd7d96a3b7b01f54eded250c9e272577aa1.jpg"
        )