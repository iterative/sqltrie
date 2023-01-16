# pylint: disable=invalid-name
from PyInstaller.utils.hooks import (  # pylint: disable=import-error
    collect_data_files,
)

datas = collect_data_files("sqltrie")
