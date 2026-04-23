def save(
        self,
        verbose=False,
        fid_range=False,
        step=False,
        progress=False,
        silent=False,
        stream=sys.stdout,
        strict=False,
    ):
        """
        Save the contents from the OGR DataSource Layer into the database
        according to the mapping dictionary given at initialization.

        Keyword Parameters:
         verbose:
           If set, information will be printed subsequent to each model save
           executed on the database.

         fid_range:
           May be set with a slice or tuple of (begin, end) feature ID's to map
           from the data source. In other words, this keyword enables the user
           to selectively import a subset range of features in the geographic
           data source.

         step:
           If set with an integer, transactions will occur at every step
           interval. For example, if step=1000, a commit would occur after
           the 1,000th feature, the 2,000th feature etc.

         progress:
           When this keyword is set, status information will be printed giving
           the number of features processed and successfully saved. By default,
           progress information will pe printed every 1000 features processed,
           however, this default may be overridden by setting this keyword with
           an integer for the desired interval.

         stream:
           Status information will be written to this file handle. Defaults to
           using `sys.stdout`, but any object with a `write` method is
           supported.

         silent:
           By default, non-fatal error notifications are printed to stdout, but
           this keyword may be set to disable these notifications.

         strict:
           Execution of the model mapping will cease upon the first error
           encountered. The default behavior is to attempt to continue.
        """
        # Getting the default Feature ID range.
        default_range = self.check_fid_range(fid_range)

        # Setting the progress interval, if requested.
        if progress:
            if progress is True or not isinstance(progress, int):
                progress_interval = 1000
            else:
                progress_interval = progress

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

        if self.transaction_decorator is not None:
            _save = self.transaction_decorator(_save)

        nfeat = self.layer.num_feat
        if step and isinstance(step, int) and step < nfeat:
            # Incremental saving is requested at the given interval (step)
            if default_range:
                raise LayerMapError(
                    "The `step` keyword may not be used in conjunction with the "
                    "`fid_range` keyword."
                )
            beg, num_feat, num_saved = (0, 0, 0)
            indices = range(step, nfeat, step)
            n_i = len(indices)

            for i, end in enumerate(indices):
                # Constructing the slice to use for this step; the last slice
                # is special (e.g, [100:] instead of [90:100]).
                if i + 1 == n_i:
                    step_slice = slice(beg, None)
                else:
                    step_slice = slice(beg, end)

                try:
                    num_feat, num_saved = _save(step_slice, num_feat, num_saved)
                    beg = end
                except Exception:  # Deliberately catch everything
                    stream.write(
                        "%s\nFailed to save slice: %s\n" % ("=-" * 20, step_slice)
                    )
                    raise
        else:
            # Otherwise, just calling the previously defined _save() function.
            _save()