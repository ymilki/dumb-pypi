from __future__ import annotations

import json
import os.path
import shutil
import subprocess
import sys
import tempfile
from typing import NamedTuple

from dumb_pypi import main


class FakePackage(NamedTuple):
    filename: str
    requires_python: str | None = None

    @property
    def setup_py_contents(self):
        return (
            'from setuptools import setup\n'
            'setup(name={!r}, version={!r})\n'
        ).format(*main.guess_name_version_from_filename(self.filename))

    def as_json(self):
        return json.dumps({
            'filename': self.filename,
            'requires_python': self.requires_python,
        })


def make_package(package: FakePackage, path: str) -> None:
    """Make a fake package at path.

    Even with --download, pip insists on extracting the downloaded packages (in
    order to find dependencies), so we can't just make empty files.
    """
    with tempfile.TemporaryDirectory() as td:
        setup_py = os.path.join(td, 'setup.py')
        with open(setup_py, 'w') as f:
            f.write(package.setup_py_contents)

        args: tuple[str, ...] = ('sdist', '--formats=zip')
        if package.filename.endswith(('.tgz', '.tar.gz')):
            args = ('sdist', '--formats=gztar')
        elif package.filename.endswith('.tar'):
            args = ('sdist', '--formats=tar')
        elif package.filename.endswith('.whl'):
            args = ('bdist_wheel',)

        subprocess.check_call((sys.executable, setup_py) + args, cwd=td)
        created, = os.listdir(os.path.join(td, 'dist'))
        shutil.move(os.path.join(td, 'dist', created), os.path.join(path, package.filename))
