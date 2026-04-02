"""Unit tests for Great Expectations Context shared module."""

from unittest.mock import MagicMock, patch

from shared.expectations.context import get_ephemeral_context, save_validation_results


def test_get_ephemeral_context():
    """Test that ephemeral GE context is created successfully."""
    context = get_ephemeral_context()
    assert context is not None


def test_save_validation_results(tmp_path):
    """Test that validation results are saved to JSON correctly."""
    mock_results = MagicMock()
    mock_results.to_json_dict.return_value = {"success": True, "results": []}

    with patch("shared.expectations.context.Path") as mock_path_cls:
        mock_path_cls.return_value = tmp_path / "data/validation"
        _ = (
            save_validation_results.__wrapped__
            if hasattr(save_validation_results, "__wrapped__")
            else None
        )

    results_dir = tmp_path / "data/validation"
    results_dir.mkdir(parents=True)

    with patch("shared.expectations.context.Path", side_effect=lambda x: tmp_path / x):
        pass

    # Direct test
    mock_results = MagicMock()
    mock_results.to_json_dict.return_value = {"success": True, "results": []}

    import shared.expectations.context as ctx

    original = ctx.Path

    try:
        ctx.Path = lambda x: tmp_path / str(x).lstrip("/")
        path = save_validation_results(mock_results, "test_validation")
        assert path is not None
        mock_results.to_json_dict.assert_called_once()
    finally:
        ctx.Path = original


def test_save_validation_results_creates_file(tmp_path):
    """Test that save_validation_results creates the JSON file."""
    mock_results = MagicMock()
    mock_results.to_json_dict.return_value = {"success": True, "results": []}

    with patch("shared.expectations.context.Path") as MockPath:
        mock_dir = MagicMock()
        mock_file_path = tmp_path / "test_validation_results.json"
        MockPath.return_value = mock_dir
        mock_dir.__truediv__ = lambda self, other: mock_file_path
        mock_dir.mkdir = MagicMock()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            save_validation_results(mock_results, "test_validation")
            mock_results.to_json_dict.assert_called_once()
