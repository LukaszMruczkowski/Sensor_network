import unittest
from unittest.mock import MagicMock
import numpy as np
from project import SimulatedAnnealing

class TestSimulatedAnnealing(unittest.TestCase):
    def setUp(self):
        # Create a mock SensorNetwork object
        self.mock_sensor_network = MagicMock()

        # Create initial parameters for SimulatedAnnealing
        initial_solution = [[0, 0], [1, 1], [2, 2]]
        temperature = 100
        cooling_rate = 0.95
        iteration_limit = 10

        # Create SimulatedAnnealing object
        self.sa = SimulatedAnnealing(initial_solution, temperature, cooling_rate, iteration_limit, self.mock_sensor_network)

    def test_evaluate(self):
        # Mock coverage percentage method of SensorNetwork
        self.mock_sensor_network.coverage_percentage.return_value = 70
        # Ensure evaluate method returns the correct score
        self.assertEqual(self.sa.evaluate([[0, 0], [1, 1], [2, 2]]), 70)


if __name__ == '__main__':
    unittest.main()
