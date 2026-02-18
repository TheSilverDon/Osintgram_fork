import sys
import io
import pytest

from src import printcolors as pc


class TestPrintColors:
    """Test the printcolors module."""

    def test_color_constants_defined(self):
        assert pc.BLACK == 0
        assert pc.RED == 1
        assert pc.GREEN == 2
        assert pc.YELLOW == 3
        assert pc.BLUE == 4
        assert pc.MAGENTA == 5
        assert pc.CYAN == 6
        assert pc.WHITE == 7

    def test_printout_writes_text(self, capsys):
        pc.printout("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_printout_default_color_is_white(self, capsys):
        pc.printout("test")
        captured = capsys.readouterr()
        assert "test" in captured.out

    def test_has_colours_is_bool(self):
        # After module init, has_colours is a bool (result of calling itself)
        assert isinstance(pc.has_colours, bool)
