""" Test Python MCC bindings and MCC-RGB algorithm """

import os

import pytest
import unittest

import numpy as np

from context import pymccrgb

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

TEST_SCALES = [0.5, 1.0, 1.5]
TEST_TOLS = [0.01, 0.05, 0.3, 0.5, 1.0]
SEED_VALUE = 42


class MCCTestCase(unittest.TestCase):
    def setUp(self):
        print("\n  Loading test data...", flush=True)
        self.data = pymccrgb.ioutils.read_las(
            os.path.join(TEST_DATA_DIR, "points_rgb.laz")
        )
        print(f"  Loaded {len(self.data)} points", flush=True)

    def _test_classify_ground_mcc(self, scale, tol):
        print(f"\n  classify_ground_mcc(scale={scale}, tol={tol})...", flush=True)
        test = pymccrgb.core.classify_ground_mcc(self.data, scale, tol)
        print(f"  done, checking results...", flush=True)
        true = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"classification_mcc_{scale}_{tol}.npy"),
            allow_pickle=True,
        )
        np.testing.assert_array_equal(
            test,
            true,
            err_msg=f"MCC ground classification is incorrect for scale {scale} and height tolerance {tol}",
        )
        print(f"  passed", flush=True)

    def test_mcc_classification(self):
        for scale in TEST_SCALES:
            for tol in TEST_TOLS:
                self._test_classify_ground_mcc(scale, tol)

    def test_mcc_default(self):
        test_points, test_labels = pymccrgb.core.mcc(self.data, verbose=True)
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mcc_default.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for default MCC configuration",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for default MCC configuration",
        )

    def test_mcc_default_las_codes(self):
        test_points, test_labels = pymccrgb.core.mcc(self.data, verbose=True,
                                                     use_las_codes=True)
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mcc_default_las.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for default MCC configuration using LAS codes",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for default MCC configuration using LAS codes",
        )


class MCCRGBTestCase(unittest.TestCase):
    def setUp(self):
        print("\n  Loading test data...", flush=True)
        self.data = pymccrgb.ioutils.read_las(
            os.path.join(TEST_DATA_DIR, "points_rgb.laz")
        )
        print(f"  Loaded {len(self.data)} points", flush=True)

    def test_mcc_rgb_default(self):
        test_points, test_labels = pymccrgb.core.mcc_rgb(
            self.data, seed=SEED_VALUE, verbose=True
        )
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mccrgb_default.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for default MCC-RGB configuration",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for default MCC-RGB configuration",
        )

    def test_mcc_default_las_codes(self):
        test_points, test_labels = pymccrgb.core.mcc_rgb(self.data,
                                                         seed=SEED_VALUE,
                                                         verbose=True,
                                                         use_las_codes=True)
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mccrgb_default_las.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for default MCC-RGB configuration using LAS codes",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for default MCC-RGB configuration using LAS codes",
        )

    def test_mcc_rgb_default_parallel(self):
        test_points, test_labels = pymccrgb.core.mcc_rgb(
            self.data, seed=SEED_VALUE, n_jobs=2, verbose=True
        )
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mccrgb_default.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for default MCC-RGB configuration with parallelization",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for default MCC-RGB configuration with parallelization",
        )

    def test_mcc_rgb_two_training_tols(self):
        test_points, test_labels = pymccrgb.core.mcc_rgb(
            self.data,
            tols=[1.0, 0.3, 0.3],
            scales=[0.5, 1.0, 1.5],
            training_tols=[1.0, 0.3],
            training_scales=[0.5, 0.5],
            seed=SEED_VALUE,
            verbose=True,
        )
        true_points, true_labels = np.load(
            os.path.join(TEST_OUTPUT_DIR, f"ground_labels_mccrgb_twotols_1.0_0.3.npy"),
            allow_pickle=True,
        )
        self.assertTrue(
            np.allclose(test_points, true_points),
            "Ground points are incorrect for MCC-RGB using training tols 1.0 and 0.3",
        )
        np.testing.assert_array_equal(
            test_labels,
            true_labels,
            err_msg="Classification is incorrect for MCC-RGB using training tols 1.0 and 0.3",
        )
