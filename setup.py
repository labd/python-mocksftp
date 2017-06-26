import re
import glob

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


with open('README.rst') as fh:
    long_description = re.sub(
        '^.. start-no-pypi.*^.. end-no-pypi', '', fh.read(), flags=re.M | re.S)



setup(
    name="mocksftp",
    version="0.1.0",
    description="Mock SFTP server for testing purposes",
    long_description=long_description,
    url="https://github.com/carletes/mock-ssh-server",
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
