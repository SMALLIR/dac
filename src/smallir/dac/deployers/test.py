from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from smallir.dac.deployers.protocol import Deployer


class TestDeployer(Deployer):

    def deploy(self, transformed_rules: Iterable[dict[str, Any]]) -> Iterator[Path]: ...
