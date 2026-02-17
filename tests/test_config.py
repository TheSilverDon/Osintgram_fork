import os
import configparser
import pytest


def test_credentials_ini_exists():
    """Verify the credentials config template exists."""
    assert os.path.isfile("config/credentials.ini")


def test_credentials_ini_has_required_sections():
    """Verify credentials.ini has the expected structure."""
    config = configparser.ConfigParser(interpolation=None)
    config.read("config/credentials.ini")
    assert "Credentials" in config.sections()


def test_credentials_ini_has_required_fields():
    """Verify credentials.ini has all required fields."""
    config = configparser.ConfigParser(interpolation=None)
    config.read("config/credentials.ini")
    creds = config["Credentials"]
    assert "username" in creds
    assert "password" in creds
