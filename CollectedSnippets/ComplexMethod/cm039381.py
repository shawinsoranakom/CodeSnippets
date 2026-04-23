def test_graphviz_toy():
    # Check correctness of export_graphviz
    clf = DecisionTreeClassifier(
        max_depth=3, min_samples_split=2, criterion="gini", random_state=2
    )
    clf.fit(X, y)

    # Test export code
    contents1 = export_graphviz(clf, out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="x[0] <= 0.0\\ngini = 0.5\\nsamples = 6\\n'
        'value = [3, 3]"] ;\n'
        '1 [label="gini = 0.0\\nsamples = 3\\nvalue = [3, 0]"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="gini = 0.0\\nsamples = 3\\nvalue = [0, 3]"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )
    assert contents1 == contents2

    # Test with feature_names
    contents1 = export_graphviz(
        clf, feature_names=["feature0", "feature1"], out_file=None
    )
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="feature0 <= 0.0\\ngini = 0.5\\nsamples = 6\\n'
        'value = [3, 3]"] ;\n'
        '1 [label="gini = 0.0\\nsamples = 3\\nvalue = [3, 0]"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="gini = 0.0\\nsamples = 3\\nvalue = [0, 3]"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )

    assert contents1 == contents2

    # Test with feature_names (escaped)
    contents1 = export_graphviz(
        clf, feature_names=['feature"0"', 'feature"1"'], out_file=None
    )
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="feature\\"0\\" <= 0.0\\n'
        "gini = 0.5\\nsamples = 6\\n"
        'value = [3, 3]"] ;\n'
        '1 [label="gini = 0.0\\nsamples = 3\\nvalue = [3, 0]"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="gini = 0.0\\nsamples = 3\\nvalue = [0, 3]"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )

    assert contents1 == contents2

    # Test with class_names
    contents1 = export_graphviz(clf, class_names=["yes", "no"], out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="x[0] <= 0.0\\ngini = 0.5\\nsamples = 6\\n'
        'value = [3, 3]\\nclass = yes"] ;\n'
        '1 [label="gini = 0.0\\nsamples = 3\\nvalue = [3, 0]\\n'
        'class = yes"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="gini = 0.0\\nsamples = 3\\nvalue = [0, 3]\\n'
        'class = no"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )

    assert contents1 == contents2

    # Test with class_names (escaped)
    contents1 = export_graphviz(clf, class_names=['"yes"', '"no"'], out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="x[0] <= 0.0\\ngini = 0.5\\nsamples = 6\\n'
        'value = [3, 3]\\nclass = \\"yes\\""] ;\n'
        '1 [label="gini = 0.0\\nsamples = 3\\nvalue = [3, 0]\\n'
        'class = \\"yes\\""] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="gini = 0.0\\nsamples = 3\\nvalue = [0, 3]\\n'
        'class = \\"no\\""] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )

    assert contents1 == contents2

    # Test plot_options
    contents1 = export_graphviz(
        clf,
        filled=True,
        impurity=False,
        proportion=True,
        special_characters=True,
        rounded=True,
        out_file=None,
        fontname="sans",
    )
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, style="filled, rounded", color="black", '
        'fontname="sans"] ;\n'
        'edge [fontname="sans"] ;\n'
        "0 [label=<x<SUB>0</SUB> &le; 0.0<br/>samples = 100.0%<br/>"
        'value = [0.5, 0.5]>, fillcolor="#ffffff"] ;\n'
        "1 [label=<samples = 50.0%<br/>value = [1.0, 0.0]>, "
        'fillcolor="#e58139"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        "2 [label=<samples = 50.0%<br/>value = [0.0, 1.0]>, "
        'fillcolor="#399de5"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        "}"
    )

    assert contents1 == contents2

    # Test max_depth
    contents1 = export_graphviz(clf, max_depth=0, class_names=True, out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="x[0] <= 0.0\\ngini = 0.5\\nsamples = 6\\n'
        'value = [3, 3]\\nclass = y[0]"] ;\n'
        '1 [label="(...)"] ;\n'
        "0 -> 1 ;\n"
        '2 [label="(...)"] ;\n'
        "0 -> 2 ;\n"
        "}"
    )

    assert contents1 == contents2

    # Test max_depth with plot_options
    contents1 = export_graphviz(
        clf, max_depth=0, filled=True, out_file=None, node_ids=True
    )
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, style="filled", color="black", '
        'fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="node #0\\nx[0] <= 0.0\\ngini = 0.5\\n'
        'samples = 6\\nvalue = [3, 3]", fillcolor="#ffffff"] ;\n'
        '1 [label="(...)", fillcolor="#C0C0C0"] ;\n'
        "0 -> 1 ;\n"
        '2 [label="(...)", fillcolor="#C0C0C0"] ;\n'
        "0 -> 2 ;\n"
        "}"
    )

    assert contents1 == contents2

    # Test multi-output with weighted samples
    clf = DecisionTreeClassifier(
        max_depth=2, min_samples_split=2, criterion="gini", random_state=2
    )
    clf = clf.fit(X, y2, sample_weight=w)

    contents1 = export_graphviz(clf, filled=True, impurity=False, out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, style="filled", color="black", '
        'fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="x[0] <= 0.0\\nsamples = 6\\n'
        "value = [[3.0, 1.5, 0.0]\\n"
        '[3.0, 1.0, 0.5]]", fillcolor="#ffffff"] ;\n'
        '1 [label="samples = 3\\nvalue = [[3, 0, 0]\\n'
        '[3, 0, 0]]", fillcolor="#e58139"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=45, "
        'headlabel="True"] ;\n'
        '2 [label="x[0] <= 1.5\\nsamples = 3\\n'
        "value = [[0.0, 1.5, 0.0]\\n"
        '[0.0, 1.0, 0.5]]", fillcolor="#f1bd97"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=-45, "
        'headlabel="False"] ;\n'
        '3 [label="samples = 2\\nvalue = [[0, 1, 0]\\n'
        '[0, 1, 0]]", fillcolor="#e58139"] ;\n'
        "2 -> 3 ;\n"
        '4 [label="samples = 1\\nvalue = [[0.0, 0.5, 0.0]\\n'
        '[0.0, 0.0, 0.5]]", fillcolor="#e58139"] ;\n'
        "2 -> 4 ;\n"
        "}"
    )

    assert contents1 == contents2

    # Test regression output with plot_options
    clf = DecisionTreeRegressor(
        max_depth=3, min_samples_split=2, criterion="squared_error", random_state=2
    )
    clf.fit(X, y)

    contents1 = export_graphviz(
        clf,
        filled=True,
        leaves_parallel=True,
        out_file=None,
        rotate=True,
        rounded=True,
        fontname="sans",
    )
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, style="filled, rounded", color="black", '
        'fontname="sans"] ;\n'
        "graph [ranksep=equally, splines=polyline] ;\n"
        'edge [fontname="sans"] ;\n'
        "rankdir=LR ;\n"
        '0 [label="x[0] <= 0.0\\nsquared_error = 1.0\\nsamples = 6\\n'
        'value = 0.0", fillcolor="#f2c09c"] ;\n'
        '1 [label="squared_error = 0.0\\nsamples = 3\\'
        'nvalue = -1.0", '
        'fillcolor="#ffffff"] ;\n'
        "0 -> 1 [labeldistance=2.5, labelangle=-45, "
        'headlabel="True"] ;\n'
        '2 [label="squared_error = 0.0\\nsamples = 3\\nvalue = 1.0", '
        'fillcolor="#e58139"] ;\n'
        "0 -> 2 [labeldistance=2.5, labelangle=45, "
        'headlabel="False"] ;\n'
        "{rank=same ; 0} ;\n"
        "{rank=same ; 1; 2} ;\n"
        "}"
    )

    assert contents1 == contents2

    # Test classifier with degraded learning set
    clf = DecisionTreeClassifier(max_depth=3)
    clf.fit(X, y_degraded)

    contents1 = export_graphviz(clf, filled=True, out_file=None)
    contents2 = (
        "digraph Tree {\n"
        'node [shape=box, style="filled", color="black", '
        'fontname="helvetica"] ;\n'
        'edge [fontname="helvetica"] ;\n'
        '0 [label="gini = 0.0\\nsamples = 6\\nvalue = 6.0", '
        'fillcolor="#ffffff"] ;\n'
        "}"
    )