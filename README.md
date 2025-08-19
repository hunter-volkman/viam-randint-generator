# Randint Generator Module

A Viam `sensor` component that generates random integer data using `numpy.random.randint` for testing and development purposes.

## Model hunter:randint-generator:sensor

This model implements the `rdk:component:sensor` API by generating configurable random integer readings with support for single or multiple named values, custom ranges, and reproducible seeds.

### Configuration

```json
{
  "low": 0,
  "high": 100,
  "num_readings": 1,
  "reading_names": ["value"],
  "dtype": "int32",
  "seed": null
}
```

#### Attributes

The following attributes are available for this model:

| Name          | Type   | Inclusion | Description                |
|---------------|--------|-----------|----------------------------|
| `low` | integer  | Optional  | Lower bound (inclusive) for random integers. Defaults to 0. |
| `high` | integer | Optional  | Upper bound (exclusive) for random integers. Defaults to 100. |
| `num_readings` | integer | Optional  | Number of readings to generate per call. Defaults to 1. |
| `reading_names` | list[string] | Optional  | Names for each reading (must match num_readings). Defaults to ["value"]. |
| `dtype` | string | Optional  | Data type: int8/16/32/64, uint8/16/32/64. Defaults to "int32". |
| `seed` | integer | Optional  | Random seed for reproducible results. Defaults to null. |

#### Example Configuration

```json
{
  "low": -40,
  "high": 100,
  "num_readings": 3,
  "reading_names": ["temp_cpu", "temp_gpu", "temp_ambient"],
  "dtype": "int8",
  "seed": 42
}
```

### DoCommand

The randint-generator model supports the following DoCommand operations:

#### Get Configuration

```json
{
  "command": "get_config"
}
```

Response:

```json
{
  "low": 0,
  "high": 100,
  "num_readings": 1,
  "reading_names": ["value"],
  "dtype": "int32",
  "seed": null
}
```

#### Reseed Random Generator

Sets a new random seed for reproducible number generation.

```json
{
  "command": "reseed",
  "seed": 12345
}
```

Response:

```json
{
  "status": "reseeded",
  "seed": 12345
}
```

#### Generate Batch Data

Generates a batch of random readings for bulk data collection.

```json
{
  "command": "generate_batch",
  "size": 10
}
```

Response for a single reading:

```json
{
  "batch": [15, 73, 9, 88, 42, 67, 23, 91, 56, 34],
  "batch_size": 10,
  "reading_name": "value"
}
```

Response for multiple readings:

```json
{
  "batch": [
    {"temp_cpu": 65, "temp_gpu": 72, "temp_ambient": 28},
    {"temp_cpu": 68, "temp_gpu": 75, "temp_ambient": 29},
    {"temp_cpu": 63, "temp_gpu": 70, "temp_ambient": 27}
  ],
  "batch_size": 3,
  "reading_names": ["temp_cpu", "temp_gpu", "temp_ambient"]
}
```

### Data Capture Integration

This module works with Viam's DoCommand data capture feature:

```json
"service_configs": [
  {
    "type": "data_manager",
    "attributes": {
      "capture_methods": [
        {
          "method": "DoCommand",
          "capture_frequency_hz": 1,
          "additional_params": {
            "docommand_input": {
              "command": "generate_batch",
              "size": 100
            }
          }
        }
      ]
    }
  }
]
```