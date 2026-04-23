def calculation(
    self, index="", red=None, green=None, blue=None, red_edge=None, nir=None
):
    self.set_matricies(red=red, green=green, blue=blue, red_edge=red_edge, nir=nir)
    funcs = {
        "ARVI2": self.arv12,
        "CCCI": self.ccci,
        "CVI": self.cvi,
        "GLI": self.gli,
        "NDVI": self.ndvi,
        "BNDVI": self.bndvi,
        "redEdgeNDVI": self.red_edge_ndvi,
        "GNDVI": self.gndvi,
        "GBNDVI": self.gbndvi,
        "GRNDVI": self.grndvi,
        "RBNDVI": self.rbndvi,
        "PNDVI": self.pndvi,
        "ATSAVI": self.atsavi,
        "BWDRVI": self.bwdrvi,
        "CIgreen": self.ci_green,
        "CIrededge": self.ci_rededge,
        "CI": self.ci,
        "CTVI": self.ctvi,
        "GDVI": self.gdvi,
        "EVI": self.evi,
        "GEMI": self.gemi,
        "GOSAVI": self.gosavi,
        "GSAVI": self.gsavi,
        "Hue": self.hue,
        "IVI": self.ivi,
        "IPVI": self.ipvi,
        "I": self.i,
        "RVI": self.rvi,
        "MRVI": self.mrvi,
        "MSAVI": self.m_savi,
        "NormG": self.norm_g,
        "NormNIR": self.norm_nir,
        "NormR": self.norm_r,
        "NGRDI": self.ngrdi,
        "RI": self.ri,
        "S": self.s,
        "IF": self._if,
        "DVI": self.dvi,
        "TVI": self.tvi,
        "NDRE": self.ndre,
    }

    try:
        return funcs[index]()
    except KeyError:
        print("Index not in the list!")
        return False
