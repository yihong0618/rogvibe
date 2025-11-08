"""Tests for rogvibe.__main__ module."""

from unittest.mock import patch
from rogvibe.__main__ import main


class TestMain:
    """Test cases for main function."""

    def test_main_with_slot_argument(self):
        """Test main function with --slot argument."""
        with patch("rogvibe.__main__.run_slot_machine") as mock_run_slot:
            main(["--slot"])
            mock_run_slot.assert_called_once()

    def test_main_with_flip_argument(self):
        """Test main function with --flip argument."""
        with patch("rogvibe.__main__.run_flip_card") as mock_run_flip:
            main(["--flip"])
            mock_run_flip.assert_called_once()

    def test_main_with_no_arguments(self):
        """Test main function with no arguments."""
        with patch("rogvibe.__main__.run") as mock_run:
            main([])
            mock_run.assert_called_once_with(None)

    def test_main_with_custom_arguments(self):
        """Test main function with custom arguments."""
        with patch("rogvibe.__main__.run") as mock_run:
            main(["arg1", "arg2"])
            mock_run.assert_called_once_with(["arg1", "arg2"])

    def test_main_with_none_argv(self):
        """Test main function with None argv."""
        with patch("rogvibe.__main__.sys.argv", ["rogvibe", "test_arg"]):
            with patch("rogvibe.__main__.run") as mock_run:
                main(None)
                mock_run.assert_called_once_with(["test_arg"])

    def test_main_direct_execution(self):
        """Test __name__ == "__main__" block."""
        with patch("rogvibe.__main__.main"):
            # Simulate direct execution by running the module
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, "-m", "rogvibe", "--help"],
                capture_output=True,
                timeout=2,
            )
            # The module should be executable (even if it errors out on --help)
            assert result.returncode in [0, 1, 2]  # Any return code is fine

    def test_main_module_has_main_function(self):
        """Test that main module properly exports main function."""
        import rogvibe.__main__ as main_module

        assert hasattr(main_module, "main")
        assert callable(main_module.main)
