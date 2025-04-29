import os


def get_hook_dirs():
    return [os.path.dirname(__file__)]


def get_PyInstaller_tests():  # noqa: N802
    return [os.path.dirname(__file__)]
