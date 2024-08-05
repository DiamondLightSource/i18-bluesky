import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List

import numpy as np
import redis
from scipy.optimize import curve_fit


# Define a Gaussian function for fitting
def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma**2))


@dataclass
class Measurement:
    bragg: float
    gap: float


@dataclass
class Record:
    element: str
    edge: str
    date: datetime
    detector: str
    comment: str
    harmonic: int
    measurements: List[Measurement] = field(default_factory=list)

    def to_json(self):
        return json.dumps(asdict(self), default=str, indent=4)

    @classmethod
    def from_json(cls, data: str):
        data_dict = json.loads(data)
        data_dict["date"] = datetime.fromisoformat(data_dict["date"])
        data_dict["harmonic"] = int(data_dict["harmonic"])
        measurements = [Measurement(**m) for m in data_dict["measurements"]]
        return cls(**data_dict, measurements=measurements)

    def quadratic_regression(self):
        x = np.array([m.bragg for m in self.measurements])
        y = np.array([m.gap for m in self.measurements])

        def quadratic(x, a, b, c):
            return a * x**2 + b * x + c

        params, _ = curve_fit(quadratic, x, y)
        return params

    def get_regression_function(self):
        params = self.quadratic_regression()

        def regression_function(x):
            a, b, c = params
            return a * x**2 + b * x + c

        return regression_function


async def scan(undulator, diode) -> Record:
    """
    the goal here is to make a serializable strucutre for those and some functions, alogn with algorithms
    this would be agnostic wrt the saving mechanism, be it redis or etcd, etc
    """
    min_val = undulator.min
    max_val = undulator.max
    bragg_values = []
    gap_values = []

    for i in range(10):
        # todo not sure about the offsets
        bragg = min_val + i * (max_val - min_val) / 10
        await undulator.set_bragg(bragg)  # Assume set_bragg is an async function
        gap = await diode.read()  # Assume read is an async function
        bragg_values.append(bragg)
        gap_values.append(gap)

    bragg_array = np.array(bragg_values)
    gap_array = np.array(gap_values)

    try:
        popt, _ = curve_fit(
            gaussian,
            bragg_array,
            gap_array,
            p0=[max(gap_array), bragg_array[np.argmax(gap_array)], 1],
        )
        peak_bragg = popt[1]
    except Exception as e:
        print(f"Gaussian fitting failed: {e}")
        peak_bragg = bragg_array[np.argmax(gap_array)]

    record = Record(
        element=undulator.element,
        edge=undulator.edge,
        date=datetime.now(),
        detector="Diode",
        comment="Measurement at peak diode value",
        harmonic=undulator.harmonic,
        measurements=[Measurement(peak_bragg, max(gap_array))],
    )

    return record


# Define possible harmonics
harmonics = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]

# Create Redis client
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)


async def main():
    # Example setup for undulator and diode
    undulator = ...  # Define your undulator object here
    diode = ...  # Define your diode object here

    tasks = []
    for h in harmonics:
        undulator.harmonic = h
        undulator.element = "Si"  # Example, set this appropriately
        undulator.edge = "K"  # Example, set this appropriately

        tasks.append(asyncio.create_task(scan(undulator, diode)))

    records = await asyncio.gather(*tasks)

    for record in records:
        record_json = record.to_json()
        print(record_json)
        save_record_to_redis(redis_client, record)


def save_record_to_redis(redis_client, record):
    redis_client.set(record.element, record.to_json())


def get_quadratic_curve(redis_client, harmonic: int, element: str, edge: str):
    # Retrieve the record from Redis
    record_json = redis_client.get(element)
    if not record_json:
        raise ValueError(f"No record found for element: {element}")

    record = Record.from_json(record_json)

    # Verify if the record matches the harmonic, element, and edge
    if record.harmonic != harmonic or record.element != element or record.edge != edge:
        raise ValueError(
            f"Record does not match the specified harmonic ({harmonic}), element ({element}), or edge ({edge})"
        )

    # Get the regression function
    regression_func = record.get_regression_function()

    return regression_func


if __name__ == "__main__":
    asyncio.run(main())
