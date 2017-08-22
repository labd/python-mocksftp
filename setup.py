#!/usr/bin/env python
import codecs
import re
import os

from setuptools import find_packages, setup

install_requires = [
    "paramiko"
]

tests_require = [
    'pretend==1.0.8',
    'pytest-cov==2.4.0',
    'pytest==3.0.6',

    # Linting
    'isort==4.2.5',
    'flake8==3.2.1',
    'flake8-blind-except==0.1.1',
    'flake8-debugger==1.4.0',
]


def read(*parts):
    file_path = os.path.join(os.path.dirname(__file__), *parts)
    return codecs.open(file_path, encoding='utf-8').read()


def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return str(version_match.group(1))
    raise RuntimeError("Unable to find version string.")


def strip_no_pypi(text):
    return re.sub(
        '^.. start-no-pypi.*^.. end-no-pypi', '', text, flags=re.M | re.S)


setup(
    name="mocksftp",
    version=find_version('src', 'mocksftp', '__init__.py'),
    description="Mock SFTP server for testing purposes",
    long_description=strip_no_pypi(read('README.rst')),
    url="https://github.com/LabD/python-mocksftp",
    author="Michael van Tellingen",
    author_email="michaelvantellingen@gmail.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    package_dir={'': 'src'},
    package_data={
        'mocksftp': ['keys/*']
    },
    packages=find_packages('src'),
    entry_points={
        'pytest11': ['mocksftp = mocksftp.pytest_plugin']
    },
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },

    zip_safe=False,
)
