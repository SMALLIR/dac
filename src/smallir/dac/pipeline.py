import logging
from dataclasses import dataclass

from smallir.dac.deployers.protocol import Deployer
from smallir.dac.loaders.protocol import Loader
from smallir.dac.parsers.protocol import Parser
from smallir.dac.transformers.protocol import Transformer

logger = logging.getLogger(__name__)


@dataclass
class Pipeline:
    loader: Loader
    parser: Parser
    transformer: Transformer
    deployer: Deployer

    def run(self) -> None:
        logger.info("Pipeline execution starting")

        try:
            logger.debug("Creating loader generators")
            raw_content = self.loader.load()

            logger.debug("Creating parser generators")
            parsed_rules = self.parser.parse(raw_content)

            logger.debug("Creating transformer generators")
            transformed_rules = self.transformer.transform(parsed_rules)

            logger.debug("Running deployer")
            self.deployer.deploy(transformed_rules)

        except Exception:
            logger.exception("Pipeline execution failed")
            raise

        logger.info("Pipeline execution completed successfully")
