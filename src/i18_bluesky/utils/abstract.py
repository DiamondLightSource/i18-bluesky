from dataclasses import dataclass
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class XYRelationship:
    x_data: np.ndarray
    y_data: np.ndarray
    fft_frequencies: np.ndarray
    fft_magnitude_x: np.ndarray
    fft_magnitude_y: np.ndarray

    def summary(self) -> str:
        return (
            f"XY Relationship:\n"
            f"Number of data points: {len(self.x_data)}\n"
            f"FFT Frequency Range: {self.fft_frequencies.min()} to {self.fft_frequencies.max()}\n"
            f"Max FFT Magnitude for x: {self.fft_magnitude_x.max()}\n"
            f"Max FFT Magnitude for y: {self.fft_magnitude_y.max()}"
        )

    def get_expanded_data(
        self, start: float, stop: float, step: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Expand the x_data and y_data over a wider range using the cached FFT values.

        :param start: The start of the expanded range (frequency).
        :param stop: The end of the expanded range (frequency).
        :param step: The step size for the expanded range.
        :return: A tuple (expanded_x_data, expanded_y_data) where each is a numpy array.
        """
        # Generate the new frequency range
        new_freqs = np.arange(start, stop, step)

        # Interpolate the FFT magnitudes to the new frequency range
        expanded_magnitude_x = np.interp(
            new_freqs, self.fft_frequencies, self.fft_magnitude_x, left=0, right=0
        )
        expanded_magnitude_y = np.interp(
            new_freqs, self.fft_frequencies, self.fft_magnitude_y, left=0, right=0
        )

        # Generate the expanded x and y data based on the new frequencies
        expanded_x_data = np.fft.ifft(expanded_magnitude_x).real
        expanded_y_data = np.fft.ifft(expanded_magnitude_y).real

        return expanded_x_data, expanded_y_data


def find_peak_xy_pairs(data: np.ndarray) -> np.ndarray:
    n_x, n_y, _ = data.shape
    peak_indices = np.argmax(data, axis=2)
    x_values, y_values = np.meshgrid(np.arange(n_x), np.arange(n_y), indexing="ij")
    x_flat = x_values.flatten()
    y_flat = y_values.flatten()
    z_flat = peak_indices.flatten()
    peak_xy_pairs = np.column_stack((x_flat, y_flat, z_flat))
    return peak_xy_pairs[:, :2]


def find_com_xy_pairs_gaussian(data: np.ndarray) -> np.ndarray:
    n_x, n_y, n_z = data.shape
    z_sum = np.sum(data, axis=2)
    x_values, y_values = np.meshgrid(np.arange(n_x), np.arange(n_y), indexing="ij")

    # Compute weighted average (center of mass) along the z-axis
    com_z_indices = np.sum(data * np.arange(n_z), axis=2) / z_sum

    # Flatten to create (x, y) pairs
    x_flat = x_values.flatten()
    y_flat = y_values.flatten()
    com_flat = com_z_indices.flatten()

    com_xy_pairs = np.column_stack((x_flat, y_flat, com_flat))
    return com_xy_pairs[:, :2]


def find_com_xy_pairs_integral(data: np.ndarray) -> np.ndarray:
    n_x, n_y, n_z = data.shape
    integral = np.sum(data, axis=2)
    x_values, y_values = np.meshgrid(np.arange(n_x), np.arange(n_y), indexing="ij")

    # Compute the center of mass weighted by the integral
    com_x = np.sum(x_values * integral, axis=1) / np.sum(integral, axis=1)
    com_y = np.sum(y_values * integral, axis=0) / np.sum(integral, axis=0)

    # Flatten to create (x, y) pairs
    com_x_flat = com_x.flatten()
    com_y_flat = com_y.flatten()

    com_xy_pairs = np.column_stack((com_x_flat, com_y_flat))
    return com_xy_pairs


def compute_fft(
    x_data: np.ndarray, y_data: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    fft_x = np.fft.fft(x_data)
    fft_y = np.fft.fft(y_data)
    n = len(x_data)
    freqs = np.fft.fftfreq(n)
    magnitude_x = np.abs(fft_x)
    magnitude_y = np.abs(fft_y)
    return freqs, magnitude_x, magnitude_y


if __name__ == "__main__":
    # Example data generation
    n_x, n_y, n_z = 10, 10, 5
    data = np.random.random((n_x, n_y, n_z))

    # Step 1: Find the (x, y) pairs based on peak, Gaussian center of mass, and integral center of mass
    peak_xy_pairs = find_peak_xy_pairs(data)
    gaussian_com_xy_pairs = find_com_xy_pairs_gaussian(data)
    integral_com_xy_pairs = find_com_xy_pairs_integral(data)

    # Select one variant to proceed with (here we use peak_xy_pairs as an example)
    x_data = peak_xy_pairs[:, 0]
    y_data = peak_xy_pairs[:, 1]

    # Step 2: Compute the FFT
    freqs, magnitude_x, magnitude_y = compute_fft(x_data, y_data)

    # Step 3: Store the relationship in a dataclass
    xy_relationship = XYRelationship(
        x_data=x_data,
        y_data=y_data,
        fft_frequencies=freqs,
        fft_magnitude_x=magnitude_x,
        fft_magnitude_y=magnitude_y,
    )

    # Print a summary of the relationship
    print(xy_relationship.summary())

    # Step 4: Plot the FFT results
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.plot(
        xy_relationship.fft_frequencies,
        xy_relationship.fft_magnitude_x,
        label="FFT of x",
    )
    plt.title("FFT of x")
    plt.xlabel("Frequency")
    plt.ylabel("Magnitude")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(
        xy_relationship.fft_frequencies,
        xy_relationship.fft_magnitude_y,
        label="FFT of y",
        color="orange",
    )
    plt.title("FFT of y")
    plt.xlabel("Frequency")
    plt.ylabel("Magnitude")
    plt.grid(True)

    plt.tight_layout()
    plt.show()

    # Example data generation
    n_x, n_y, n_z = 10, 10, 5
    data = np.random.random((n_x, n_y, n_z))

    # Find the (x, y) pairs based on peak
    peak_xy_pairs = find_peak_xy_pairs(data)
    x_data = peak_xy_pairs[:, 0]
    y_data = peak_xy_pairs[:, 1]

    # Compute the FFT
    freqs, magnitude_x, magnitude_y = compute_fft(x_data, y_data)

    # Store the relationship in a dataclass
    xy_relationship = XYRelationship(
        x_data=x_data,
        y_data=y_data,
        fft_frequencies=freqs,
        fft_magnitude_x=magnitude_x,
        fft_magnitude_y=magnitude_y,
    )

    # Print a summary of the relationship
    print(xy_relationship.summary())

    # Get expanded data
    expanded_x_data, expanded_y_data = xy_relationship.get_expanded_data(
        start=-1.0, stop=1.0, step=0.1
    )

    # Optionally: plot or analyze the expanded data
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(expanded_x_data, label="Expanded x data")
    plt.title("Expanded x data")
    plt.xlabel("Index")
    plt.ylabel("Value")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(expanded_y_data, label="Expanded y data", color="orange")
    plt.title("Expanded y data")
    plt.xlabel("Index")
    plt.ylabel("Value")
    plt.grid(True)

    plt.tight_layout()
    plt.show()
