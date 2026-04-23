def simpson_integration(function, a: float, b: float, precision: int = 4) -> float:
    """
    Args:
        function : the function which's integration is desired
        a : the lower limit of integration
        b : upper limit of integration
        precision : precision of the result,error required default is 4

    Returns:
        result : the value of the approximated integration of function in range a to b

    Raises:
        AssertionError: function is not callable
        AssertionError: a is not float or integer
        AssertionError: function should return float or integer
        AssertionError: b is not float or integer
        AssertionError: precision is not positive integer

    >>> simpson_integration(lambda x : x*x,1,2,3)
    2.333

    >>> simpson_integration(lambda x : x*x,'wrong_input',2,3)
    Traceback (most recent call last):
        ...
    AssertionError: a should be float or integer your input : wrong_input

    >>> simpson_integration(lambda x : x*x,1,'wrong_input',3)
    Traceback (most recent call last):
        ...
    AssertionError: b should be float or integer your input : wrong_input

    >>> simpson_integration(lambda x : x*x,1,2,'wrong_input')
    Traceback (most recent call last):
        ...
    AssertionError: precision should be positive integer your input : wrong_input
    >>> simpson_integration('wrong_input',2,3,4)
    Traceback (most recent call last):
        ...
    AssertionError: the function(object) passed should be callable your input : ...

    >>> simpson_integration(lambda x : x*x,3.45,3.2,1)
    -2.8

    >>> simpson_integration(lambda x : x*x,3.45,3.2,0)
    Traceback (most recent call last):
        ...
    AssertionError: precision should be positive integer your input : 0

    >>> simpson_integration(lambda x : x*x,3.45,3.2,-1)
    Traceback (most recent call last):
        ...
    AssertionError: precision should be positive integer your input : -1

    """
    assert callable(function), (
        f"the function(object) passed should be callable your input : {function}"
    )
    assert isinstance(a, (float, int)), f"a should be float or integer your input : {a}"
    assert isinstance(function(a), (float, int)), (
        "the function should return integer or float return type of your function, "
        f"{type(a)}"
    )
    assert isinstance(b, (float, int)), f"b should be float or integer your input : {b}"
    assert isinstance(precision, int) and precision > 0, (
        f"precision should be positive integer your input : {precision}"
    )

    # just applying the formula of simpson for approximate integration written in
    # mentioned article in first comment of this file and above this function

    h = (b - a) / N_STEPS
    result = function(a) + function(b)

    for i in range(1, N_STEPS):
        a1 = a + h * i
        result += function(a1) * (4 if i % 2 else 2)

    result *= h / 3
    return round(result, precision)