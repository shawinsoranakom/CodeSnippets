def __annotate__(format):
            annos = {}
            for base in bases:
                if base is Generic:
                    continue
                base_annotate = base.__annotate__
                if base_annotate is None:
                    continue
                base_annos = _lazy_annotationlib.call_annotate_function(
                    base_annotate, format, owner=base)
                annos.update(base_annos)
            if own_annotate is not None:
                own = _lazy_annotationlib.call_annotate_function(
                    own_annotate, format, owner=tp_dict)
                if format != _lazy_annotationlib.Format.STRING:
                    own = {
                        n: _type_check(tp, msg, module=tp_dict.__module__)
                        for n, tp in own.items()
                    }
            elif format == _lazy_annotationlib.Format.STRING:
                own = _lazy_annotationlib.annotations_to_string(own_annotations)
            elif format in (_lazy_annotationlib.Format.FORWARDREF, _lazy_annotationlib.Format.VALUE):
                own = own_checked_annotations
            else:
                raise NotImplementedError(format)
            annos.update(own)
            return annos