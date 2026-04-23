def test_file_path(self):
        file_path = self.pipeline.file_path
        assert (
            file_path(Request("https://dev.mydeco.com/mydeco.pdf"))
            == "full/c9b564df929f4bc635bdd19fde4f3d4847c757c5.pdf"
        )
        assert (
            file_path(
                Request(
                    "http://www.maddiebrown.co.uk///catalogue-items//image_54642_12175_95307.txt"
                )
            )
            == "full/4ce274dd83db0368bafd7e406f382ae088e39219.txt"
        )
        assert (
            file_path(
                Request("https://dev.mydeco.com/two/dirs/with%20spaces%2Bsigns.doc")
            )
            == "full/94ccc495a17b9ac5d40e3eabf3afcb8c2c9b9e1a.doc"
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
            == "full/97ee6f8a46cbbb418ea91502fd24176865cf39b2"
        )
        assert (
            file_path(Request("http://www.dorma.co.uk/images/product_details/2532"))
            == "full/244e0dd7d96a3b7b01f54eded250c9e272577aa1"
        )
        assert (
            file_path(
                Request("http://www.dorma.co.uk/images/product_details/2532"),
                response=Response("http://www.dorma.co.uk/images/product_details/2532"),
                info=object(),
            )
            == "full/244e0dd7d96a3b7b01f54eded250c9e272577aa1"
        )
        assert (
            file_path(
                Request(
                    "http://www.dfsonline.co.uk/get_prod_image.php?img=status_0907_mdm.jpg.bohaha"
                )
            )
            == "full/76c00cef2ef669ae65052661f68d451162829507"
        )
        assert (
            file_path(
                Request(
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAR0AAACxCAMAAADOHZloAAACClBMVEX/\
                                    //+F0tzCwMK76ZKQ21AMqr7oAAC96JvD5aWM2kvZ78J0N7fmAAC46Y4Ap7y"
                )
            )
            == "full/178059cbeba2e34120a67f2dc1afc3ecc09b61cb.png"
        )