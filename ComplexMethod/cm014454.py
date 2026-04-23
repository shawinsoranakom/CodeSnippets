def __call__(self, extension, data):
        if extension.lower() not in ["jpg", "jpeg", "png", "ppm", "pgm", "pbm", "pnm"]:
            return None

        try:
            import numpy as np
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Package `numpy` is required to be installed for default image decoder."
                "Please use `pip install numpy` to install the package"
            ) from e

        try:
            import PIL.Image
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Package `PIL` is required to be installed for default image decoder."
                "Please use `pip install Pillow` to install the package"
            ) from e

        imagespec = self.imagespec
        atype, etype, mode = imagespecs[imagespec]

        with io.BytesIO(data) as stream:
            img = PIL.Image.open(stream)
            img.load()
            img = img.convert(mode.upper())
            if atype == "pil":
                return img
            elif atype == "numpy":
                result = np.asarray(img)
                if result.dtype != np.uint8:
                    raise AssertionError(
                        f"numpy image array should be type uint8, but got {result.dtype}"
                    )
                if etype == "uint8":
                    return result
                else:
                    return result.astype("f") / 255.0
            elif atype == "torch":
                result = np.asarray(img)
                if result.dtype != np.uint8:
                    raise AssertionError(
                        f"numpy image array should be type uint8, but got {result.dtype}"
                    )

                if etype == "uint8":
                    result = np.array(result.transpose(2, 0, 1))
                    return torch.tensor(result)
                else:
                    result = np.array(result.transpose(2, 0, 1))
                    return torch.tensor(result) / 255.0
            return None