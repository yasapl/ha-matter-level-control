# Matter Level Control for Home Assistant

A Home Assistant custom integration exposing native Matter **Level Control** commands.

Its primary purpose is smooth, native control of continuously adjustable Matter devices — most notably **light brightness / dimming**. Matter Level Control is the cluster behind level-based operations such as moving a level up or down, stepping it, moving to a specific level, and stopping movement.

If you are looking for **Matter light brightness control**, **smooth hold-to-dim**, **Matter dimming**, **continuous brightness adjustment**, or other Matter devices that expose a controllable level (for example a device using Level Control for speed), this integration provides access to Matter's native `Move` and `Stop` commands from Home Assistant automations.

> **Current implementation:** entity targeting is currently limited to Home Assistant Matter `light` entities. The underlying Matter Level Control cluster is not inherently lighting-specific, so support for other Matter entity types may be added where devices expose the cluster appropriately.

## Why this integration exists

Home Assistant's normal `light.turn_on` brightness control works well when setting a specific brightness. It is less suitable for a physical switch or rotary controller where the desired behaviour is:

**press and hold → smoothly increase/decrease brightness → release → stop immediately**

One way to implement this in Home Assistant is to repeatedly send slightly different brightness values. In practice that can produce visible stepping, overlapping transitions and unnecessary command traffic.

Matter already has commands specifically designed for continuous level changes. A single `Move` command tells the Matter device itself to start changing its level. A subsequent `Stop` command stops it at its current level.

This integration exposes those native commands to Home Assistant.

## Matter Level Control

The Matter Level Control cluster is a generic level-control mechanism. Depending on the Matter device type and implementation, a level may represent something such as:

- light brightness / dimming
- another continuously adjustable actuator level
- speed on a device that implements speed through Level Control

Many device classes have their own dedicated Matter clusters — for example, fans can use Matter Fan Control — so the presence of an adjustable value does **not** automatically mean that a device supports Level Control.

The device must actually expose the Matter Level Control cluster and implement the required commands.

## Features

- Native Matter `Move` command for continuous level changes
- Native Matter `Stop` command to stop immediately at the current level
- Move up or down
- Configurable movement rate
- Targets Home Assistant Matter light entities directly
- Uses Home Assistant's existing Matter integration and Matter Server connection
- No additional Matter fabric, Matter Server, MQTT broker, or helper daemon required

## Requirements

- Home Assistant with the built-in Matter integration configured
- Currently, a Matter light exposed as a Home Assistant `light` entity
- The Matter endpoint must expose the Level Control cluster
- The device must support the required Level Control `Move` and `Stop` commands

## Installation

### HACS

1. Add this repository to HACS as a custom repository with category **Integration**.
2. Install **Matter Level Control**.
3. Add the following to your Home Assistant `configuration.yaml`:

```yaml
matter_level:
```

4. Restart Home Assistant.
5. After restart, `matter_level.move` and `matter_level.stop` should be available under **Developer Tools → Actions** and in automations.

The YAML entry is currently required because the integration does not yet use a Home Assistant config flow/UI setup.

This project is currently under development and should be considered experimental.

## Usage

### Start increasing brightness

```yaml
action: matter_level.move
target:
  entity_id: light.example_matter_light
data:
  direction: up
  rate: 50
```

### Start decreasing brightness

```yaml
action: matter_level.move
target:
  entity_id: light.example_matter_light
data:
  direction: down
  rate: 50
```

### Stop at the current brightness

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

Matter's `Move` command instead tells the device itself to continuously change its level. The device continues moving without further commands until a `Stop` command is received (or a limit is reached). This generally provides much smoother control and requires only two commands for an entire button hold.

## Status

Early development version. Initial testing is focused on Matter lights and the Level Control `Move` / `Stop` command pair.

Not all Matter lights necessarily implement these commands even if they support ordinary brightness control.

## Development

Technical notes and implementation details are available in [`DEVELOPMENT.md`](DEVELOPMENT.md).
