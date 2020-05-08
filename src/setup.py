import sys
from pathlib import Path
from typing import Dict

from setuptools import setup

this = Path(__file__)
info: Dict[str, str] = {}
# read in the __version__ from the src file
with open(this.parent / "den" / "__version__.py", "r") as v:
    exec(v.read(), info)

# read in the README for the long description
with open(this.parent.parent / "README.md", "r") as f:
    info["readme"] = f.read()


setup(
    name="den",
    version=info["__version__"],
    author="jdost",
    description="Command line utility for managing docker based development "
    "containers.",
    long_description=info["readme"],
    python_requires=">=3.6.0",
    packages=["den", "den.commands"],
    package_dir={"den": "den/", "den.commands": "den/commands/"},
    install_requires=["click>=7.0", "docker>=2.7.0", "colorama"],
    extras_require={
        "dev": [
            "black>=19.3b0",
            "isort>=4.3.21",
            "mypy>=0.770",
            "pylint>=2.3.1",
            "pytest>=5.0.0",
        ]
    },
    entry_points={"console_scripts": ["den = den:main"]},
)
