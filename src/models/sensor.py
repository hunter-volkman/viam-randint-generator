from typing import (Any, ClassVar, Dict, Final, List, Mapping, Optional,
                    Sequence, Tuple)

import numpy as np
from typing_extensions import Self
from viam.components.sensor import *
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import SensorReading, ValueTypes


class RandintGenerator(Sensor, EasyResource):
    """
    A Viam sensor module that generates random integer data using numpy.random.randint.
    
    This module is designed for testing and development purposes where fake sensor data
    is needed. Provides flexible configuration options for generating single or multiple 
    random integer readings with customizable ranges.
    """
    
    MODEL: ClassVar[Model] = Model(ModelFamily("hunter", "randint-generator"), "sensor")

    def __init__(self, name: str):
        super().__init__(name)
        # Default configuration values
        self.low = 0
        self.high = 100
        self.num_readings = 1
        self.reading_names = ["value"]
        self.dtype = "int32"
        self.seed = None
        
    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """Creates a new instance of the RandintGenerator sensor component."""
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        return sensor

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        """
        Validates the configuration for the randint generator.
        
        Expected configuration attributes:
        - low (int, optional): Lower bound (inclusive). Default: 0
        - high (int, optional): Upper bound (exclusive). Default: 100
        - num_readings (int, optional): Number of readings to generate. Default: 1
        - reading_names (list, optional): Names for each reading. Default: ["value"]
        - dtype (str, optional): Data type for integers. Default: "int32"
        - seed (int, optional): Random seed for reproducibility. Default: None
        
        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Tuple[Sequence[str], Sequence[str]]: Required and optional dependencies
        """
        # Validate num_readings and reading_names consistency
        attributes = config.attributes.fields
        
        if "num_readings" in attributes and "reading_names" in attributes:
            num_readings = int(attributes["num_readings"].number_value)
            reading_names = [item.string_value for item in attributes["reading_names"].list_value.values]
            
            if len(reading_names) != num_readings:
                raise ValueError(f"Number of reading_names ({len(reading_names)}) must match num_readings ({num_readings})")
        
        # Validate bounds
        if "low" in attributes and "high" in attributes:
            low = int(attributes["low"].number_value)
            high = int(attributes["high"].number_value)
            
            if low >= high:
                raise ValueError(f"low ({low}) must be less than high ({high})")
        
        # Validate dtype
        if "dtype" in attributes:
            dtype = attributes["dtype"].string_value
            valid_dtypes = ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"]
            if dtype not in valid_dtypes:
                raise ValueError(f"dtype must be one of {valid_dtypes}, got {dtype}")
        
        return [], []  # No dependencies required

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """
        Reconfigures the sensor with new settings.
        
        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Dependencies (unused)
        """
        attributes = config.attributes.fields
        
        # Configure bounds
        self.low = int(attributes.get("low", self._make_number_value(0)).number_value)
        self.high = int(attributes.get("high", self._make_number_value(100)).number_value)
        
        # Configure number of readings
        self.num_readings = int(attributes.get("num_readings", self._make_number_value(1)).number_value)
        
        # Configure reading names
        if "reading_names" in attributes:
            self.reading_names = [
                item.string_value for item in attributes["reading_names"].list_value.values
            ]
        else:
            # Generate default names based on num_readings
            if self.num_readings == 1:
                self.reading_names = ["value"]
            else:
                self.reading_names = [f"value_{i+1}" for i in range(self.num_readings)]
        
        # Configure data type
        self.dtype = attributes.get("dtype", self._make_string_value("int32")).string_value
        
        # Configure random seed
        if "seed" in attributes:
            self.seed = int(attributes["seed"].number_value)
            np.random.seed(self.seed)
        else:
            self.seed = None
        
        self.logger.info(f"Configured randint generator: low={self.low}, high={self.high}, "
                        f"num_readings={self.num_readings}, reading_names={self.reading_names}, "
                        f"dtype={self.dtype}, seed={self.seed}")

    def _make_number_value(self, value: float):
        """Helper to create a number value for default handling."""
        from google.protobuf.struct_pb2 import Value
        v = Value()
        v.number_value = value
        return v
    
    def _make_string_value(self, value: str):
        """Helper to create a string value for default handling."""
        from google.protobuf.struct_pb2 import Value
        v = Value()
        v.string_value = value
        return v

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, SensorReading]:
        """
        Generate random integer readings.
        
        Returns:
            Mapping[str, SensorReading]: Dictionary of reading names to their random values
        """
        try:
            # Convert dtype string to numpy dtype
            np_dtype = getattr(np, self.dtype)
            
            # Generate random integers
            if self.num_readings == 1:
                # Single value
                value = np.random.randint(self.low, self.high, dtype=np_dtype)
                readings = {self.reading_names[0]: int(value)}
            else:
                # Multiple values
                values = np.random.randint(self.low, self.high, size=self.num_readings, dtype=np_dtype)
                readings = {
                    name: int(value) 
                    for name, value in zip(self.reading_names, values)
                }
            
            self.logger.debug(f"Generated readings: {readings}")
            return readings
            
        except Exception as e:
            self.logger.error(f"Error generating random integers: {e}")
            raise

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        """
        Execute custom commands on the randint generator.
        
        Supported commands:
        - get_config: Returns current configuration
        - reseed: Sets a new random seed  
        - generate_batch: Generates a batch of readings
        
        Args:
            command: Command dictionary with "command" key
            
        Returns:
            Command response
        """
        cmd = command.get("command")
        if not cmd:
            raise ValueError("Missing 'command' field in do_command")
        
        if cmd == "get_config":
            return {
                "low": self.low,
                "high": self.high,
                "num_readings": self.num_readings,
                "reading_names": self.reading_names,
                "dtype": self.dtype,
                "seed": self.seed
            }
        
        elif cmd == "reseed":
            new_seed = command.get("seed")
            if new_seed is None:
                raise ValueError("reseed command requires 'seed' parameter")
            if not isinstance(new_seed, (int, float)):
                raise ValueError("seed must be an integer")
            
            self.seed = int(new_seed)
            np.random.seed(self.seed)
            self.logger.info(f"Reseeded random generator with seed: {self.seed}")
            return {"status": "reseeded", "seed": self.seed}
        
        elif cmd == "generate_batch":
            batch_size = command.get("size", 10)
            if not isinstance(batch_size, (int, float)) or batch_size <= 0:
                raise ValueError("batch size must be a positive integer")
            
            batch_size = int(batch_size)
            np_dtype = getattr(np, self.dtype)
            
            if self.num_readings == 1:
                batch_values = np.random.randint(self.low, self.high, size=batch_size, dtype=np_dtype)
                return {
                    "batch": [int(val) for val in batch_values],
                    "batch_size": batch_size,
                    "reading_name": self.reading_names[0]
                }
            else:
                batch_values = np.random.randint(
                    self.low, self.high, 
                    size=(batch_size, self.num_readings), 
                    dtype=np_dtype
                )
                return {
                    "batch": [
                        {name: int(val) for name, val in zip(self.reading_names, row)}
                        for row in batch_values
                    ],
                    "batch_size": batch_size,
                    "reading_names": self.reading_names
                }
        
        else:
            raise NotImplementedError(f"Command '{cmd}' is not implemented")

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Geometry]:
        """
        Returns the geometries associated with the sensor.
        
        For a virtual sensor like this randint generator, no physical geometries exist.
        """
        return []