from dataclasses import dataclass

from smallir.dac.deployers.protocol import Deployer
from smallir.dac.loaders.protocol import Loader
from smallir.dac.parsers.protocol import Parser
from smallir.dac.transformers.protocol import Transformer


@dataclass
class Pipeline:
    loader: Loader
    parser: Parser
    transformer: Transformer
    deployer: Deployer

    def run(self):
        raw_content = self.loader.load()
        parsed_rules = self.parser.parse(raw_content)
        transformed_rules = self.transformer.transform(parsed_rules)
        self.deployer.deploy(transformed_rules)
