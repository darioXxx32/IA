import unittest
from coordinator import weighted_average


class FedAvgProtocolTests(unittest.TestCase):
    def test_sample_weighted_average(self):
        updates = [
            {'num_samples': 10, 'weights': [1.0]},
            {'num_samples': 20, 'weights': [2.0]},
            {'num_samples': 30, 'weights': [4.0]},
        ]
        self.assertAlmostEqual(weighted_average(updates)[0], 2.8333333333333335)

    def test_rejects_different_tensor_shapes(self):
        with self.assertRaisesRegex(ValueError, 'dimensions differ'):
            weighted_average([
                {'num_samples': 10, 'weights': [1.0]},
                {'num_samples': 20, 'weights': [2.0, 3.0]},
            ])

    def test_rejects_non_positive_sample_count(self):
        with self.assertRaisesRegex(ValueError, 'positive sample counts'):
            weighted_average([{'num_samples': 0, 'weights': [1.0]}])


if __name__ == '__main__':
    unittest.main(verbosity=2)
