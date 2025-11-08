"""Tests for rogvibe.utils.executor module."""

from unittest.mock import Mock, patch
from rogvibe.utils.executor import execute_command


class TestExecutor:
    """Test cases for executor module."""

    def test_execute_command_with_code(self):
        """Test execute_command with 'code' command adds '.' argument."""
        mock_app = Mock()
        mock_app.suspend = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/code"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                execute_command("code", mock_app)

                # Should be called with 'code' and '.'
                mock_exec.assert_called_once_with("code", ["code", "."])

    def test_execute_command_with_cursor(self):
        """Test execute_command with 'cursor' command adds '.' argument."""
        mock_app = Mock()
        mock_app.suspend = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/cursor"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                execute_command("cursor", mock_app)

                mock_exec.assert_called_once_with("cursor", ["cursor", "."])

    def test_execute_command_with_empty_string(self):
        """Test execute_command with empty string exits with code 0."""
        mock_app = Mock()

        execute_command("", mock_app)

        mock_app.exit.assert_called_once_with(0)

    def test_execute_command_not_found(self):
        """Test execute_command when command is not on PATH."""
        mock_app = Mock()

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = None

            execute_command("nonexistent", mock_app)

            mock_app.exit.assert_called_once_with(127)

    def test_execute_command_with_arguments(self):
        """Test execute_command with arguments."""
        mock_app = Mock()
        mock_app.suspend = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ls"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                execute_command("ls -la", mock_app)

                mock_exec.assert_called_once_with("ls", ["ls", "-la"])

    def test_execute_command_file_not_found_error(self):
        """Test execute_command when FileNotFoundError is raised."""
        mock_app = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        mock_app.suspend = Mock(return_value=mock_context)

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/cmd"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                with patch("rogvibe.utils.executor.print"):
                    mock_exec.side_effect = FileNotFoundError()

                    execute_command("cmd", mock_app)

                    mock_app.exit.assert_called_once_with(127)

    def test_execute_command_permission_error(self):
        """Test execute_command when PermissionError is raised."""
        mock_app = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        mock_app.suspend = Mock(return_value=mock_context)

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/cmd"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                with patch("rogvibe.utils.executor.print"):
                    mock_exec.side_effect = PermissionError()

                    execute_command("cmd", mock_app)

                    mock_app.exit.assert_called_once_with(126)

    def test_execute_command_os_error(self):
        """Test execute_command when OSError is raised."""
        mock_app = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        mock_app.suspend = Mock(return_value=mock_context)

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/cmd"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                with patch("rogvibe.utils.executor.print"):
                    mock_exec.side_effect = OSError("Some OS error")

                    execute_command("cmd", mock_app)

                    mock_app.exit.assert_called_once_with(1)

    def test_execute_command_without_suspend(self):
        """Test execute_command with app that doesn't have suspend method."""
        mock_app = Mock(spec=[])  # No suspend method
        delattr(mock_app, "suspend")

        with patch("rogvibe.utils.executor.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/echo"

            with patch("rogvibe.utils.executor.os.execvp") as mock_exec:
                execute_command("echo hello", mock_app)

                mock_exec.assert_called_once_with("echo", ["echo", "hello"])
