from typing import Dict, Optional, Sequence

def setup(
    name: str,
    version: str,
    description: Optional[str],
    long_description: Optional[str],
    author: str,
    python_requires: Optional[str],
    packages: Sequence[str],
    package_dir: Optional[Dict[str, str]],
    install_requires: Sequence[str],
    extras_require: Dict[str, Sequence[str]],
    entry_points: Optional[Dict[str, Sequence[str]]],
) -> None: ...
