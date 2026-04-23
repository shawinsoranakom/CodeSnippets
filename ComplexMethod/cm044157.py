def surface3d(
    X: "Series",
    Y: "Series",
    Z: "Series",
    xtitle: str | None = "DTE",
    ytitle: str | None = "Strike",
    ztitle: str | None = "IV",
    colorscale: str | list | None = None,
    title: str | None = None,
    layout_kwargs: dict[str, Any] | None = None,
    theme: Literal["dark", "light"] | None = None,
) -> Union["OpenBBFigure", "Figure"]:
    """Create a 3D surface chart.

    Parameters
    ----------
    X : pd.Series
        The x-axis data.
    Y : pd.Series
        The y-axis data.
    Z : pd.Series
        The z-axis data.
    xtitle : str, optional
        The title for the x-axis, by default "DTE".
    ytitle : str, optional
        The title for the y-axis, by default "Strike".
    ztitle : str, optional
        The title for the z-axis, by default "IV".
    colorscale : Union[str, list], optional
        The colorscale to use for the surface, by default None.
    title : str, optional
        The title of the chart, by default None.
    layout_kwargs : Optional[dict[str, Any]], optional
        Additional keyword arguments to apply with figure.update_layout(), by default None.

    Returns
    -------
    OpenBBFigure
        The OpenBBFigure object.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.app.model.abstract.error import OpenBBError  # noqa
    from openbb_charting.core.openbb_figure import OpenBBFigure
    from numpy import vstack
    from scipy.spatial import Delaunay
    import numpy as np

    try:
        points3D = vstack((X, Y, Z)).T
        points2D = points3D[:, :2]
        tri = Delaunay(points2D)
        II, J, K = tri.simplices.T
    except Exception as e:
        raise OpenBBError(f"Not enough points to render 3D: {e}") from e

    fig = OpenBBFigure(create_backend=False)
    chart_style = ChartStyle()
    if theme:
        chart_style.plt_style = theme
    fig.set_title(f"{title if title and title != 'OpenBB Platform' else ''}")
    fig_kwargs = dict(z=Z, x=X, y=Y, i=II, j=J, k=K, intensity=Z)
    customdata = np.array([[xtitle, ytitle, ztitle]] * len(X))

    fig.add_mesh3d(
        **fig_kwargs,
        alphahull=0,
        opacity=1,
        contour=dict(color="black", show=True, width=15),
        colorscale=(
            colorscale
            if colorscale
            else [
                [0, "darkred"],
                [0.001, "crimson"],
                [0.005, "red"],
                [0.0075, "orangered"],
                [0.015, "darkorange"],
                [0.025, "orange"],
                [0.04, "goldenrod"],
                [0.055, "gold"],
                [0.11, "magenta"],
                [0.15, "plum"],
                [0.4, "lightblue"],
                [0.7, "royalblue"],
                [0.9, "blue"],
                [1, "darkblue"],
            ]
        ),
        colorbar=dict(
            len=0.66,
            y=0.5,
            thickness=15,
        ),
        customdata=customdata,
        hovertemplate="<b>%{customdata[0]}</b>: %{x} <br>"
        "<b>%{customdata[1]}</b>: %{y} <br>"
        "<b>%{customdata[2]}</b>: %{z}<extra></extra>",
        showscale=True,
        flatshading=True,
        lighting=dict(
            ambient=0.95,
            diffuse=0.9,
            roughness=0.8,
            specular=0.9,
            fresnel=0.001,
            vertexnormalsepsilon=0.0001,
            facenormalsepsilon=0.0001,
        ),
    )
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                backgroundcolor="rgb(94, 94, 94)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white",
                title=dict(text=xtitle if xtitle else "DTE", font=dict(size=18)),
                autorange="reversed",
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                backgroundcolor="rgb(94, 94, 94)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white",
                title=dict(text=ytitle if ytitle else "Strike", font=dict(size=18)),
                tickfont=dict(size=12),
            ),
            zaxis=dict(
                backgroundcolor="rgb(94, 94, 94)",
                gridcolor="white",
                showbackground=True,
                zerolinecolor="white",
                title=dict(text=ztitle if ztitle else "IV", font=dict(size=18)),
                tickfont=dict(size=12),
            ),
            domain=dict(y=[0.0125, 0.95], x=[0.0125, 1]),
        ),
        title_x=0.5,
        title_y=0.98,
        scene_camera=dict(
            up=dict(x=0, y=0, z=0.75),
            center=dict(x=-0.01, y=0, z=-0.3),
            eye=dict(x=1.75, y=1.75, z=0.69),
        ),
    )

    fig.update_scenes(
        aspectmode="manual",
        aspectratio=dict(x=1.5, y=2.0, z=0.75),
        dragmode="turntable",
    )

    if layout_kwargs:
        fig.update_layout(layout_kwargs, overwrite=False)

    return fig