
from dataclasses import dataclass
from totoms import TotoLogger
from totoms.model.TotoEnvironment import TotoEnvironment
from totoms.evt.TotoMessageBus import TotoMessageBus
from totoms.model.TotoConfig import TotoControllerConfig

@dataclass
class ExecutionContext: 
    
    logger: TotoLogger
    cid: str 
    config: TotoControllerConfig
    message_bus: TotoMessageBus
    environment: TotoEnvironment