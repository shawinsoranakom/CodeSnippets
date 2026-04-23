def finish(self):
        super().finish()
        logger.info(bold("writing templatebuiltins.js..."))
        xrefs = self.env.domaindata["std"]["objects"]
        templatebuiltins = {
            "ttags": [
                n
                for ((t, n), (k, a)) in xrefs.items()
                if t == "templatetag" and k == "ref/templates/builtins"
            ],
            "tfilters": [
                n
                for ((t, n), (k, a)) in xrefs.items()
                if t == "templatefilter" and k == "ref/templates/builtins"
            ],
        }
        outfilename = os.path.join(self.outdir, "templatebuiltins.js")
        with open(outfilename, "w") as fp:
            fp.write("var django_template_builtins = ")
            json.dump(templatebuiltins, fp)
            fp.write(";\n")