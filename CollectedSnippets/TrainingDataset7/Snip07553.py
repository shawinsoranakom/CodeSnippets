def _save(feat_range=default_range, num_feat=0, num_saved=0):
            if feat_range:
                layer_iter = self.layer[feat_range]
            else:
                layer_iter = self.layer

            for feat in layer_iter:
                num_feat += 1
                # Getting the keyword arguments
                try:
                    kwargs = self.feature_kwargs(feat)
                except LayerMapError as msg:
                    # Something borked the validation
                    if strict:
                        raise
                    elif not silent:
                        stream.write(
                            "Ignoring Feature ID %s because: %s\n" % (feat.fid, msg)
                        )
                else:
                    # Constructing the model using the keyword args
                    is_update = False
                    if self.unique:
                        # If we want unique models on a particular field,
                        # handle the geometry appropriately.
                        try:
                            # Getting the keyword arguments and retrieving
                            # the unique model.
                            u_kwargs = self.unique_kwargs(kwargs)
                            m = self.model.objects.using(self.using).get(**u_kwargs)
                            is_update = True

                            # Getting the geometry (in OGR form), creating
                            # one from the kwargs WKT, adding in additional
                            # geometries, and update the attribute with the
                            # just-updated geometry WKT.
                            geom_value = getattr(m, self.geom_field)
                            if geom_value is None:
                                geom = OGRGeometry(kwargs[self.geom_field])
                            else:
                                geom = geom_value.ogr
                                new = OGRGeometry(kwargs[self.geom_field])
                                for g in new:
                                    geom.add(g)
                            setattr(m, self.geom_field, geom.wkt)
                        except ObjectDoesNotExist:
                            # No unique model exists yet, create.
                            m = self.model(**kwargs)
                    else:
                        m = self.model(**kwargs)

                    try:
                        # Attempting to save.
                        m.save(using=self.using)
                        num_saved += 1
                        if verbose:
                            stream.write(
                                "%s: %s\n" % ("Updated" if is_update else "Saved", m)
                            )
                    except Exception as msg:
                        if strict:
                            # Bailing out if the `strict` keyword is set.
                            if not silent:
                                stream.write(
                                    "Failed to save the feature (id: %s) into the "
                                    "model with the keyword arguments:\n" % feat.fid
                                )
                                stream.write("%s\n" % kwargs)
                            raise
                        elif not silent:
                            stream.write(
                                "Failed to save %s:\n %s\nContinuing\n" % (kwargs, msg)
                            )

                # Printing progress information, if requested.
                if progress and num_feat % progress_interval == 0:
                    stream.write(
                        "Processed %d features, saved %d ...\n" % (num_feat, num_saved)
                    )

            # Only used for status output purposes -- incremental saving uses
            # the values returned here.
            return num_saved, num_feat