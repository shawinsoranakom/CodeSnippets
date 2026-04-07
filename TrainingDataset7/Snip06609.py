def check_relate_argument(self, arg):
        masks = (
            "TOUCH|OVERLAPBDYDISJOINT|OVERLAPBDYINTERSECT|EQUAL|INSIDE|COVEREDBY|"
            "CONTAINS|COVERS|ANYINTERACT|ON"
        )
        mask_regex = re.compile(r"^(%s)(\+(%s))*$" % (masks, masks), re.I)
        if not isinstance(arg, str) or not mask_regex.match(arg):
            raise ValueError('Invalid SDO_RELATE mask: "%s"' % arg)