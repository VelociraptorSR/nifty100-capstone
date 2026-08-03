"""Unit tests for src/reports/radar_charts.py — Sprint 3, Day 19."""

import os
import pandas as pd
import pytest

from src.reports.radar_charts import draw_radar_chart, AXES, AXIS_LABELS


def test_axes_and_labels_same_length():
    assert len(AXES) == len(AXIS_LABELS) == 8


def test_draw_radar_chart_creates_file(tmp_path):
    company_values = [80, 70, 60, 90, 50, 40, 30, 75]
    peer_values = [50, 50, 50, 50, 50, 50, 50, 50]
    output_path = str(tmp_path / "TEST_radar.png")

    draw_radar_chart("TEST", company_values, peer_values, output_path)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_draw_radar_chart_handles_zero_values(tmp_path):
    company_values = [0, 0, 0, 0, 0, 0, 0, 0]
    peer_values = [50, 50, 50, 50, 50, 50, 50, 50]
    output_path = str(tmp_path / "ZERO_radar.png")

    draw_radar_chart("ZERO_TEST", company_values, peer_values, output_path)

    assert os.path.exists(output_path)