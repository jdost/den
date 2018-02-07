# Add the `src/` folder to the path (on the front to avoid collisions with
# previously installed versions
import os
import sys

sys.path.insert(0, os.getcwd() + "/src/")
import den
# read in the README for the long description
with open('README.md', 'r') as f:
    readme = f.read()

from setuptools import setup

setup(
    name="den",
    version=den.__version__,
    description="Command line utility for managing docker based development "
        "containers.",
    long_description=readme,

    packages=[
        "den",
        "den.commands",
    ],
    package_dir={
        "den": "src/den/",
        "den.commands": "src/den/commands/",
    },
    install_requires=[
        "click>=6.0",
        "docker>=2.7.0",
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "den = den:main"
        ],
    },
)
