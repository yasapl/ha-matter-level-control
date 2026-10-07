# Matter Level Control for Home Assistant

A Home Assistant custom integration that exposes native Matter **Level Control** commands for Matter lights.

The integration was created to support smooth press-and-hold dimming. Home Assistant's normal `light.turn_on` brightness changes work well for setting a specific brightness, but repeatedly sending brightness values during a button hold can result in visible stepping or overlapping transitions.

Matter already provides native Level Control commands designed for this purpose. This integration makes those commands available to Home Assistant automations.

## Features

- Native Matter `Move` command for continuous dimming
- Native Matter `Stop` command to stop immediately at the current brightness
- Dimming up or down
- Configurable movement rate
- Targets Home Assistant Matter light entities directly
- Uses Home Assistant's existing Matter integration and Matter Server connection
- No additional Matter fabric, Matter Server, MQTT broker, or helper daemon required

## Requirements

- Home Assistant with the built-in Matter integration configured
- A Matter light exposing the Matter Level Control cluster
- The device must support the required Level Control `Move` and `Stop` commands

## Installation

### HACS

Add this repository to HACS as a custom repository with category **Integration**, install **Matter Level Control**, and restart Home Assistant.

This project is currently under development and should be considered experimental.

## Usage

### Start dimming up

```yaml
action: matter_level.move
target:
  entity_id: light.example_matter_light
data:
  direction: up
  rate: 50
```

### Start dimming down

```yaml
action: matter_level.move
target:
  entity_id: light.example_matter_light
data:
  direction: down
  rate: 50
```

### Stop dimming

```yaml
action: matter_level.stop
target:
  entity_id: light.example_matter_light
```

A typical wall-switch automation sends `matter_level.move` when a button is held and `matter_level.stop` when the button is released.

## Rate

`rate` is the Matter Level Control movement rate. The useful range depends on the device. A value of `50` is the default used by this integration and is a good starting point.

## Why native Matter Level Control?

A conventional Home Assistant hold-to-dim automation often repeatedly calls `light.turn_on` with a slightly different brightness. Each call sets another absolute level and may start another transition.

Matter's `Move` command instead tells the light itself to continuously change its level. The light continues moving without further commands until a `Stop` command is received (or a limit is reached). This generally provides much smoother dimming and requires only two commands for an entire button hold.

## Status

Early development version. Initial testing is focused on Matter lights and the Level Control `Move` / `Stop` command pair.

Not all Matter lights necessarily implement these commands even if they support ordinary brightness control.

## Development

Technical notes and implementation details are available in [`DEVELOPMENT.md`](DEVELOPMENT.md).
