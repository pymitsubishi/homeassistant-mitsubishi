# Home Assistant Mitsubishi Air Conditioner Integration

[![CI](https://github.com/pymitsubishi/homeassistant-mitsubishi/workflows/CI/badge.svg?branch=main)](https://github.com/pymitsubishi/homeassistant-mitsubishi/actions)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/pymitsubishi/homeassistant-mitsubishi.svg)](https://github.com/pymitsubishi/homeassistant-mitsubishi/releases)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/pymitsubishi/homeassistant-mitsubishi)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant custom component for controlling and monitoring Mitsubishi MAC-577IF-2E air conditioners.

## CI/CD

This repository uses GitHub Actions for continuous integration:

- **Python Versions**: 3.12, 3.13
- **Tests**: Runs pytest with coverage and enforces a 100% code coverage threshold.
- **Lint and Format**: Uses ruff for linting and formatting.
- **Type Checking**: Uses mypy for static type checking.
- **Pre-commit Hooks**: Runs a series of code quality checks on each commit.
- **Manifest Validation**: Checks Home Assistant manifest for required fields.

Check the .github/workflows/ci.yml file for more details.

To run tests locally:

```bash
git clone https://github.com/pymitsubishi/homeassistant-mitsubishi
cd homeassistant-mitsubishi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests --cov=custom_components/mitsubishi --cov-report=term-missing -v
```

## Features

- **Easy Setup**: Configure through Home Assistant UI with automatic device discovery
- **Climate Control**: Full climate entity support with temperature, mode, and fan control
- **Sensors**: Temperature sensors for room and outdoor readings
- **Capability Detection**: Automatic detection of device capabilities using ProfileCode analysis
- **Real-time Updates**: Efficient polling with 30-second update intervals

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/pymitsubishi/homeassistant-mitsubishi` as an integration
6. Install the integration
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/mitsubishi` folder to your `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations
4. Click "Add Integration" and search for "Mitsubishi Air Conditioner"

## Configuration

1. Go to Configuration → Integrations
2. Click "Add Integration"
3. Search for "Mitsubishi Air Conditioner"
4. Enter your air conditioner's IP address
5. Optionally enable capability detection (recommended)
6. Click "Submit"

The integration will automatically discover your device and create the appropriate entities.

## Supported Entities

### Climate
- **Power**: Turn the air conditioner on/off
- **Temperature**: Set target temperature (16-32°C)
- **Mode**: Heat, Cool, Auto, Dry, Fan
- **Fan Speed**: Auto, 1-3, Full
- **Vane Direction**: Vertical and horizontal vane control

### Sensors
- **Room Temperature**: Current room temperature
- **Outdoor Temperature**: Outside temperature (if available)
- **Error Status**: Device error codes and abnormal states
- **Dehumidifier Level**: Current dehumidifier setting percentage

### Diagnostic Sensors
- **Unit Information**: Complete device model and configuration details
- **Firmware Version**: WiFi adapter firmware and version information
- **Unit Type**: Air conditioner type and manufacturing details
- **WiFi Information**: Signal strength and communication status

## Requirements

- Home Assistant 2025.1 or later (requires Python 3.12+)
- [pymitsubishi](https://pypi.org/project/pymitsubishi/) library (automatically installed)
- Mitsubishi air conditioner with MAC-577IF-2E WiFi adapter

## Troubleshooting

### Connection Issues
- Ensure your air conditioner is connected to your WiFi network
- Verify the IP address is correct and accessible from Home Assistant
- Check firewall settings if connection fails

### Missing Features
- Some features may not be available depending on your specific model
- Enable capability detection to automatically discover supported features

## Development

This integration uses the [pymitsubishi](https://github.com/pymitsubishi/pymitsubishi) library for device communication.

### Local Development Setup

1. Clone this repository
2. Create a symbolic link in your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Enable logging for debugging:

```yaml
logger:
  default: info
  logs:
    custom_components.mitsubishi: debug
    pymitsubishi: debug
```

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for detailed information on:

- Development setup
- Code quality standards
- Testing requirements
- Commit message conventions
- Pull request process

Quick start:
1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Make your changes following our guidelines
4. Run tests (`pytest tests/`)
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/pymitsubishi/homeassistant-mitsubishi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pymitsubishi/homeassistant-mitsubishi/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)
