from typing import List

import numpy as np
import sympy as sp


def calculate_derivative_maxima(data: np.ndarray) -> List[float]:
    """
    data is array[tuple(float, float)]
    x = motor position
    y = transmission strength
    todo need to pass an x argument to the function

    """
    x = sp.Symbol("x")
    y = sp.interpolating_spline(3, sp.lambdify(x, data))
    derivative = y.diff(x)
    critical_points = sp.solve(derivative, x)
    return [float(cp) for cp in critical_points if cp.is_real]


def get_quadratic_curve(redis_client, harmonic: int, element: str, edge: str):
    # Retrieve the record from Redis
    record_json = redis_client.get(element)
    if not record_json:
        raise ValueError(f"No record found for element: {element}")

    record = IdGapLookupRecord.from_json(record_json)

    # Verify if the record matches the harmonic, element, and edge
    if record.harmonic != harmonic or record.element != element or record.edge != edge:
        raise ValueError(
            f"""Record does not match the specified harmonic ({harmonic}),
            element ({element}), or edge ({edge})"""
        )

    # Get the regression function
    regression_func = record.get_regression_function()

    return regression_func
