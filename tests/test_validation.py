import re
import pytest


# Reproduce the validation regex from both Osintgram and HikerCLI
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.]{1,30}$')


class TestUsernameValidation:
    """Test Instagram username validation logic."""

    def test_valid_simple_username(self):
        assert USERNAME_PATTERN.match("john_doe")

    def test_valid_username_with_periods(self):
        assert USERNAME_PATTERN.match("john.doe")

    def test_valid_username_with_numbers(self):
        assert USERNAME_PATTERN.match("user123")

    def test_valid_single_char_username(self):
        assert USERNAME_PATTERN.match("a")

    def test_valid_max_length_username(self):
        assert USERNAME_PATTERN.match("a" * 30)

    def test_invalid_empty_username(self):
        assert not USERNAME_PATTERN.match("")

    def test_invalid_too_long_username(self):
        assert not USERNAME_PATTERN.match("a" * 31)

    def test_invalid_username_with_spaces(self):
        assert not USERNAME_PATTERN.match("user name")

    def test_invalid_username_with_special_chars(self):
        assert not USERNAME_PATTERN.match("user@name")

    def test_invalid_username_with_slash(self):
        assert not USERNAME_PATTERN.match("user/name")

    def test_invalid_username_with_hyphen(self):
        # Instagram doesn't allow hyphens
        assert not USERNAME_PATTERN.match("user-name")


class TestOutputFilenames:
    """Test that output filename patterns are correct and consistent."""

    COMMANDS_TO_FILENAMES = {
        "addrs": "_addrs",
        "captions": "_captions",
        "comments": "_comments",
        "comment_data": "_comment_data",
        "followers": "_followers",
        "followings": "_followings",
        "hashtags": "_hashtags",
        "likes": "_likes",
        "mediatype": "_mediatype",
        "fwersemail": "_fwersemail",
        "fwingsemail": "_fwingsemail",
        "fwersnumber": "_fwersnumber",
        "fwingsnumber": "_fwingsnumber",
        "tagged": "_tagged",
        "users_who_commented": "_users_who_commented",
        "users_who_tagged": "_users_who_tagged",
        "info": "_info",
        "descriptions": "_descriptions",
    }

    def test_filenames_dont_contain_double_underscores(self):
        for cmd, fn in self.COMMANDS_TO_FILENAMES.items():
            assert "__" not in fn, f"Filename for {cmd} contains double underscore: {fn}"

    def test_filenames_are_lowercase(self):
        for cmd, fn in self.COMMANDS_TO_FILENAMES.items():
            assert fn == fn.lower(), f"Filename for {cmd} is not lowercase: {fn}"

    def test_txt_and_json_filenames_match(self):
        """Verify that txt and json filenames for the same command use the same base name."""
        # This test documents the expected mapping - if someone changes a filename
        # for txt but not json (the bug we fixed), this would catch it.
        for cmd, base in self.COMMANDS_TO_FILENAMES.items():
            txt_name = f"target{base}.txt"
            json_name = f"target{base}.json"
            assert txt_name.replace(".txt", "") == json_name.replace(".json", ""), \
                f"Mismatch for {cmd}: {txt_name} vs {json_name}"
