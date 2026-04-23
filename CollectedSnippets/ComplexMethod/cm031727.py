def declare_parser(
    f: Function,
    *,
    hasformat: bool = False,
    codegen: CodeGen,
) -> str:
    """
    Generates the code template for a static local PyArg_Parser variable,
    with an initializer.  For core code (incl. builtin modules) the
    kwtuple field is also statically initialized.  Otherwise
    it is initialized at runtime.
    """
    limited_capi = codegen.limited_capi
    if hasformat:
        fname = ''
        format_ = '.format = "{format_units}:{name}",'
    else:
        fname = '.fname = "{name}",'
        format_ = ''

    num_keywords = len([
        p for p in f.parameters.values()
        if p.is_positional_or_keyword() or p.is_keyword_only()
    ])

    condition = '#if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)'
    if limited_capi:
        declarations = """
            #define KWTUPLE NULL
        """
    elif num_keywords == 0:
        declarations = """
            #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)
            #  define KWTUPLE (PyObject *)&_Py_SINGLETON(tuple_empty)
            #else
            #  define KWTUPLE NULL
            #endif
        """

        codegen.add_include('pycore_runtime.h', '_Py_SINGLETON()',
                            condition=condition)
    else:
        # XXX Why do we not statically allocate the tuple
        # for non-builtin modules?
        declarations = """
            #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

            #define NUM_KEYWORDS %d
            static struct {{
                PyGC_Head _this_is_not_used;
                PyObject_VAR_HEAD
                Py_hash_t ob_hash;
                PyObject *ob_item[NUM_KEYWORDS];
            }} _kwtuple = {{
                .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
                .ob_hash = -1,
                .ob_item = {{ {keywords_py} }},
            }};
            #undef NUM_KEYWORDS
            #define KWTUPLE (&_kwtuple.ob_base.ob_base)

            #else  // !Py_BUILD_CORE
            #  define KWTUPLE NULL
            #endif  // !Py_BUILD_CORE
        """ % num_keywords

        codegen.add_include('pycore_gc.h', 'PyGC_Head',
                            condition=condition)
        codegen.add_include('pycore_runtime.h', '_Py_ID()',
                            condition=condition)

    declarations += """
            static const char * const _keywords[] = {{{keywords_c} NULL}};
            static _PyArg_Parser _parser = {{
                .keywords = _keywords,
                %s
                .kwtuple = KWTUPLE,
            }};
            #undef KWTUPLE
    """ % (format_ or fname)
    return libclinic.normalize_snippet(declarations)