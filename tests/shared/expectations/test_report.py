"""Unit tests for shared expectations report modules."""

import json

import pytest

from shared.expectations.report import generate_html_report


@pytest.fixture
def sample_results_dir(tmp_path):
    """Create sample validation JSON files in a temp directory."""
    results_dir = tmp_path / "validation"
    results_dir.mkdir()

    weather = {
        "success": True,
        "results": [
            {
                "success": True,
                "expectation_config": {
                    "type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "city"},
                },
                "result": {"unexpected_count": 0, "unexpected_percent": 0.0},
            },
            {
                "success": False,
                "expectation_config": {
                    "type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "temperature_c"},
                },
                "result": {"unexpected_count": 2, "unexpected_percent": 0.8},
            },
        ],
    }

    air_quality = {
        "success": False,
        "results": [
            {
                "success": True,
                "expectation_config": {
                    "type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "city"},
                },
                "result": {"unexpected_count": 0, "unexpected_percent": 0.0},
            },
        ],
    }

    with open(results_dir / "weather_validation_results.json", "w") as f:
        json.dump(weather, f)

    with open(results_dir / "air_quality_validation_results.json", "w") as f:
        json.dump(air_quality, f)

    return results_dir


def test_generate_html_report_creates_file(tmp_path, sample_results_dir):
    """Test that generate_html_report creates index.html."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    assert (output_dir / "index.html").exists()


def test_generate_html_report_contains_pipeline_names(tmp_path, sample_results_dir):
    """Test that the report contains pipeline names."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "Weather Validation" in content
    assert "Air Quality Validation" in content


def test_generate_html_report_shows_pass_fail(tmp_path, sample_results_dir):
    """Test that the report shows pass/fail status."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "✅ Passed" in content
    assert "❌ Failed" in content


def test_generate_html_report_empty_results_dir(tmp_path):
    """Test report generation with no JSON files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(empty_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "Data Platform" in content
    assert "<tbody>" in content


def test_generate_html_report_contains_timestamp(tmp_path, sample_results_dir):
    """Test that the report contains a timestamp."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "Generated:" in content
    assert "UTC" in content


def test_generate_html_report_contains_expectations(tmp_path, sample_results_dir):
    """Test that the report contains expectation details."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "city" in content
    assert "temperature_c" in content


def test_generate_html_report_collapsible(tmp_path, sample_results_dir):
    """Test that the report has collapsible toggle functionality."""
    output_dir = tmp_path / "output"
    generate_html_report(
        results_dir=str(sample_results_dir),
        output_dir=str(output_dir),
    )
    content = (output_dir / "index.html").read_text()
    assert "toggle(" in content
    assert "display:none" in content
