#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import msms

import numpy as np

BENZENE_COORDS = [
   [ 1.3831,   -0.2214,    0.0054],
   [ 0.5069,   -1.3065,   -0.0079],
   [-0.8709,   -1.0905,   -0.0147],
   [-1.3729,    0.2110,   -0.0044],
   [-0.4967,    1.2961,    0.0106],
   [ 0.8812,    1.0800,    0.0137],
   [ 2.4568,   -0.3898,    0.0092],
   [ 0.8979,   -2.3206,   -0.0132],
   [-1.5535,   -1.9359,   -0.0274],
   [-2.4465,    0.3793,   -0.0083],
   [-0.8878,    2.3100,    0.0197],
   [ 1.5638,    1.9255,    0.0230],
]

BENZENE_RADII = [
   1.7000,
   1.7000,
   1.7000,
   1.7000,
   1.7000,
   1.7000,
   1.2000,
   1.2000,
   1.2000,
   1.2000,
   1.2000,
   1.2000,
]


def test_run_msms_no_error():
    msms.run_msms(BENZENE_COORDS, BENZENE_RADII)


def test_run_msms_faces():
    out = msms.run_msms(BENZENE_COORDS, BENZENE_RADII)
    expected_faces = np.loadtxt("tests/surface.face", skiprows=3, usecols=[0, 1, 2], dtype=int)
    np.testing.assert_allclose(out.faces["i"], expected_faces[:, 0])
    np.testing.assert_allclose(out.faces["j"], expected_faces[:, 1])
    np.testing.assert_allclose(out.faces["k"], expected_faces[:, 2])


def test_run_msms_vertices():
    out = msms.run_msms(BENZENE_COORDS, BENZENE_RADII)
    expected_verts = np.loadtxt("tests/surface.vert", skiprows=3, usecols=[0, 1, 2], dtype=float)
    np.testing.assert_allclose(out.vertices["x"], expected_verts[:, 0])
    np.testing.assert_allclose(out.vertices["y"], expected_verts[:, 1])
    np.testing.assert_allclose(out.vertices["z"], expected_verts[:, 2])

def test_uses_extra_args():
    out = msms.run_msms(BENZENE_COORDS, BENZENE_RADII, "-density", "2.0")
    assert out.params().density == 2.0

def test_uses_extra_kwargs():
    out = msms.run_msms(BENZENE_COORDS, BENZENE_RADII, density=2.0)
    assert out.params().density == 2.0
