# Matter Level Control for Home Assistant — Development Specification

## Repository

- Repository: `yasapl/ha-matter-level-control`
- Intended integration domain: `matter_level`
- Repository must be HACS-compatible.
- This repository is dedicated to this integration; it is not a multi-integration collection.

## Goal

Create a Home Assistant custom integration that exposes native Matter **Level Control** continuous dimming commands as Home Assistant actions/services.

The immediate use case is a physical wall switch:

- short press/release: toggle the light;
- hold: start continuous dimming up or down;
- release after hold: stop dimming at the current level;
- after each completed hold, reverse the direction for the next hold.

The important design requirement is that the Matter device performs the continuous ramp locally. Home Assistant must not simulate continuous dimming by repeatedly sending new absolute brightness targets.

## Why this is needed

The original Home Assistant automation repeatedly called `light.turn_on` with a modified brightness while the wall switch remained held.

Initial implementation used roughly:

- brightness increment/decrement: 25
- delay: 500 ms
- transition: 0.5 s

This worked but appeared choppy.

A test with smaller changes:

- increment/decrement: 10
- delay: 250 ms
- transition around 0.4 s

caused the Matter bulb to stall because new commands were arriving while previous transitions were still active.

Reducing the transition to approximately 0.15 s prevented that behaviour, but produced visibly stepped brightness changes rather than smooth dimming.

Therefore repeatedly issuing `MoveToLevelWithOnOff`/absolute brightness commands is not the desired solution.

## Native Matter solution

Matter Level Control supports continuous movement.

Required behaviour:

### Hold

Send a single Level Control `Move` command.

For increasing brightness:

```json
{
  "moveMode": 0,
  "rate": 50,
  "optionsMask": 0,
  "optionsOverride": 0
}
```

For decreasing brightness:

```json
{
  "moveMode": 1,
  "rate": 50,
  "optionsMask": 0,
  "optionsOverride": 0
}
```

### Release

Send:

```json
{}
```

using the Level Control `Stop` command.

This was tested manually from the Matter Server UI and works correctly:

1. `Move` starts a smooth continuous brightness ramp.
2. The bulb performs the ramp itself without repeated HA commands.
3. `Stop` immediately stops the ramp and leaves the bulb at approximately its current brightness.

## Tested Matter device

Test device is a Matter-over-Thread bulb managed by Home Assistant.

Matter details:

- Node ID: **57**
- Endpoint: **1**
- Level Control cluster ID: **8 / 0x0008**
- Network type: Thread
- Device type reported by HA: Routing end device
- Thread network: `NEST-PAN-890D`

The node/endpoint values above are test values only. The integration must not hard-code them.

The Matter Server UI confirmed that endpoint 1 exposes the Level Control cluster.

### Level Control capabilities

The device reports:

`AcceptedCommandList = [0, 1, 2, 3, 4, 5, 6, 7]`

Relevant commands include:

- 0 — MoveToLevel
- 1 — Move
- 2 — Step
- 3 — Stop
- 4 — MoveToLevelWithOnOff
- 5 — MoveWithOnOff
- 6 — StepWithOnOff
- 7 — StopWithOnOff

The bulb therefore explicitly supports native `Move` and `Stop`.

The Level Control cluster also reports:

`DefaultMoveRate = 50`

A rate of 50 was used successfully during manual testing.

## Matter Server environment

At the time of development:

- Home Assistant: 2026.10 generation/current installation
- Home Assistant Matter Server add-on: **9.2.0**
- Matter Server hostname inside HA add-on networking: `core-matter-server`
- Matter Server TCP port: 5580 exists internally but is not exposed to the LAN
- Matter Server uses the newer matter.js-based server stack.

Do **not** require port 5580 to be exposed to the LAN.

## Integration architecture

Preferred architecture:

1. Implement a normal Home Assistant custom integration.
2. Depend on Home Assistant's built-in `matter` integration.
3. Reuse Home Assistant's already-established Matter client/server connection.
4. Do not create a second Matter Server connection unless current HA architecture makes reuse impossible.
5. Do not require an external helper daemon or separate add-on.
6. Verify APIs against the current Home Assistant and Matter implementation before coding. Do not assume older Python Matter Server examples still match current HA.

Home Assistant's built-in Matter entities already send Matter commands internally. The custom integration should use the supported/current equivalent mechanism to issue Level Control commands.

## Required Home Assistant API

The integration should expose at least two HA actions/services.

Suggested API:

### `matter_level.move`

Example:

```yaml
action: matter_level.move
data:
  node_id: 57
  endpoint_id: 1
  direction: up
  rate: 50
```

Required inputs:

- `node_id`
- `endpoint_id`
- `direction`: `up` or `down`
- `rate`

Possible future improvement: allow selecting a Matter light entity/device instead of manually entering node and endpoint IDs.

The implementation should translate:

- `up` -> Matter `moveMode: 0`
- `down` -> Matter `moveMode: 1`

and send Level Control cluster command `Move`.

### `matter_level.stop`

Example:

```yaml
action: matter_level.stop
data:
  node_id: 57
  endpoint_id: 1
```

This sends Level Control cluster command `Stop`.

## Original automation context

Wall switch sensor:

`sensor.playroom_light_switch_switch_press_action_switch`

Controlled light:

`light.play_room_playroom_main_light`

Direction helper:

`input_boolean.playroom_main_light_dimming_direction`

Relevant switch transitions:

### Normal press/release

Trigger:

```yaml
from: press
to: released
```

Action:

```yaml
action: light.toggle
target:
  entity_id: light.play_room_playroom_main_light
```

### Hold

Trigger when state becomes:

`long_press`

The direction helper determines whether the native Matter Move should be up or down.

### Release after hold

Trigger:

```yaml
from: long_press
to: released
```

Required behaviour:

1. Send Matter `Stop`.
2. Toggle `input_boolean.playroom_main_light_dimming_direction` so the next hold moves in the opposite direction.

## Important automation finding

The original automation used:

```yaml
mode: single
```

This prevented the release-from-hold trigger from running.

Reason:

- the automation instance handling the long-press repeat loop was still active;
- the sensor changed from `long_press` to `released`;
- the release trigger fired while the existing automation execution was still running;
- `mode: single` rejected the new execution;
- the repeat loop then exited, but the release trigger had already been discarded.

Changing the automation to:

```yaml
mode: parallel
```

fixed the direction-change behaviour.

Keep this in mind when producing the final example automation.

## HACS requirements

Repository should follow the normal HACS custom-integration structure, approximately:

```text
ha-matter-level-control/
├── custom_components/
│   └── matter_level/
│       ├── __init__.py
│       ├── manifest.json
│       ├── services.yaml
│       ├── const.py
│       └── other files as required
├── hacs.json
├── README.md
├── LICENSE
└── .gitignore
```

Only add files that are actually useful/current for modern HA custom integrations.

The manifest should declare the built-in Matter integration as a dependency if that remains the correct mechanism after checking the current HA API.

## Development rules

Before implementing the command calls:

1. Inspect the current Home Assistant Matter integration source.
2. Determine how its existing Matter client is stored/accessed.
3. Determine the current supported method for sending an arbitrary Matter cluster command.
4. Verify the exact command classes/payload types for Level Control `Move` and `Stop`.
5. Avoid relying on historical `python-matter-server` APIs without verifying they are still applicable.
6. Prefer HA's existing Matter connection rather than opening a new WebSocket to `core-matter-server:5580`.
7. Do not hard-code Node 57 or Endpoint 1.
8. Validate node, endpoint, direction and rate inputs.
9. Produce clear HA service/action schemas so the actions are usable from Developer Tools and automations.

## Initial success criteria

Version 0.1 should be considered successful when this sequence works from Home Assistant:

1. Invoke `matter_level.move` for Node 57 / Endpoint 1 / direction up / rate 50.
2. Bulb smoothly increases brightness continuously.
3. Invoke `matter_level.stop`.
4. Bulb stops immediately and remains at its current level.
5. Repeat using direction down.
6. Replace the existing brightness repeat loops in the Playroom automation with these two actions.
7. Holding/releasing the wall switch feels smooth and responsive without flooding the Matter network with brightness commands.

## Future improvements

Potential enhancements after the basic implementation works:

- Accept HA Matter light entity IDs rather than node/endpoint IDs.
- Automatically resolve Matter node and endpoint from an HA entity.
- Detect whether the target endpoint actually exposes Level Control.
- Inspect `AcceptedCommandList` and reject unsupported Move/Stop operations cleanly.
- Optional default rate configuration.
- Support `MoveWithOnOff`, `Step`, and `StopWithOnOff` if useful.
- Add a config flow if persistent configuration becomes necessary.
- Add diagnostics.
- Add automated tests.
- Prepare HACS metadata/release workflow and documentation.

## Known-good manual test

The following was manually invoked from Matter Server Developer Mode and confirmed working on the test bulb.

Move up:

```json
{
  "moveMode": 0,
  "rate": 50,
  "optionsMask": 0,
  "optionsOverride": 0
}
```

Move down:

```json
{
  "moveMode": 1,
  "rate": 50,
  "optionsMask": 0,
  "optionsOverride": 0
}
```

Stop:

```json
{}
```

Target:

- Node 57
- Endpoint 1
- Cluster 8 (Level Control)

These manual tests are the baseline against which the HA custom integration should be validated.
