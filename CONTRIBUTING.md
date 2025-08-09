# Contributing to Home Assistant Mitsubishi Integration

Thank you for your interest in contributing to the Home Assistant Mitsubishi Integration! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- Virtual environment (recommended)
- Home Assistant development environment (optional but recommended)

### Setting Up Your Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pymitsubishi/homeassistant-mitsubishi.git
   cd homeassistant-mitsubishi
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements-test.txt
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **(Optional) Set up Home Assistant development environment:**
   ```bash
   # Install Home Assistant in development mode
   pip install homeassistant

   # Or clone Home Assistant core for full development
   git clone https://github.com/home-assistant/core.git
   ```

## Code Quality Standards

We maintain code quality standards aligned with Home Assistant's guidelines:

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- **Ruff**: Formats and lints Python code according to Home Assistant standards
- **mypy**: Type checking for Python code
- **File fixes**: Trailing whitespace, end-of-file, YAML/JSON validation
- **HACS validation**: Ensures compatibility with HACS

To run pre-commit manually:
```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

### Manual Code Quality Checks

#### Formatting (Ruff)
```bash
# Check formatting
ruff format --check custom_components tests

# Auto-format code
ruff format custom_components tests
```

#### Linting (Ruff)
```bash
# Check for linting issues
ruff check custom_components tests

# Auto-fix linting issues
ruff check --fix custom_components tests
```

#### Type Checking (mypy)
```bash
mypy custom_components --config-file mypy.ini
```

#### Testing
```bash
# Run tests with coverage report
pytest tests/ -v --cov=custom_components.mitsubishi --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=custom_components.mitsubishi --cov-report=html
# Open htmlcov/index.html in your browser

# Run specific test file
pytest tests/test_climate.py -v
```

## Home Assistant Integration Guidelines

### Following Home Assistant Standards

1. **Entity naming**: Follow Home Assistant's entity naming conventions
2. **Device classes**: Use appropriate device classes for sensors and binary sensors
3. **Units**: Use Home Assistant's standard units (metric by default)
4. **Translations**: Update `strings.json` for user-facing text
5. **Config flow**: Ensure smooth setup experience through UI

### Integration Structure

```
custom_components/mitsubishi/
├── __init__.py           # Integration setup and configuration entry
├── manifest.json         # Integration metadata
├── climate.py           # Climate platform implementation
├── sensor.py            # Sensor platform implementation
├── binary_sensor.py     # Binary sensor platform implementation
├── select.py            # Select platform implementation
├── number.py            # Number platform implementation
├── config_flow.py       # Configuration flow for UI setup
├── coordinator.py       # Data update coordinator
├── entity.py           # Base entity classes
├── const.py            # Constants
├── utils.py            # Utility functions
├── strings.json        # User-facing strings
├── icon.png           # Integration icon (256x256)
└── icon@2x.png        # High-res icon (512x512)
```

### Writing Tests

Tests should cover:

1. **Config flow**: Test discovery and manual setup
2. **Entity creation**: Test that entities are created correctly
3. **State updates**: Test entity state changes
4. **Error handling**: Test error scenarios and recovery
5. **Coordinator**: Test data fetching and distribution

Example test:
```python
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from custom_components.mitsubishi import async_setup_entry
from custom_components.mitsubishi.const import DOMAIN

async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up the integration."""
    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.mitsubishi.MitsubishiController") as mock_controller:
        mock_controller.return_value.fetch_unit_info = AsyncMock(return_value=True)

        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
```

## Version Management

**CRITICAL**: Version updates must be synchronized in multiple places:

1. **custom_components/mitsubishi/manifest.json** - `"version": "X.Y.Z"`
2. **For HACS releases**: Create a GitHub release with tag `vX.Y.Z`
3. **PyPI dependency**: When pymitsubishi is updated, update the requirement in manifest.json

### Release Process

1. Update version in `manifest.json`
2. Update CHANGELOG.md
3. Commit with message: `chore: Release version X.Y.Z`
4. Create GitHub release with tag `vX.Y.Z`
5. HACS will automatically pick up the new release

## HACS Compatibility

Ensure HACS compatibility:

1. **hacs.json**: Must be valid and include correct configuration
2. **manifest.json**: Must include all required fields
3. **Icons**: PNG format, 256x256 and 512x512 (icon.png, icon@2x.png)
4. **GitHub Topics**: Repository should have appropriate topics (hacs, home-assistant, integration)
5. **Documentation**: README.md must be comprehensive

## Testing with Home Assistant

### Local Testing

1. **Copy integration to Home Assistant:**
   ```bash
   # Assuming HA config is at ~/.homeassistant
   cp -r custom_components/mitsubishi ~/.homeassistant/custom_components/
   ```

2. **Restart Home Assistant:**
   ```bash
   # If running in Docker
   docker restart homeassistant

   # Or if running directly
   hass --script restart
   ```

3. **Check logs:**
   ```bash
   tail -f ~/.homeassistant/home-assistant.log
   ```

### Testing Checklist

- [ ] Integration loads without errors
- [ ] Config flow works (discovery and manual)
- [ ] All entities are created correctly
- [ ] State updates work as expected
- [ ] Retries work on connection failure
- [ ] Errors are handled gracefully
- [ ] Icons display correctly
- [ ] Translations are correct

## Making a Pull Request

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following Home Assistant and code quality standards

3. **Ensure all tests pass:**
   ```bash
   pytest tests/ --cov=custom_components.mitsubishi
   ```

4. **Run pre-commit hooks:**
   ```bash
   pre-commit run --all-files
   ```

5. **Update documentation** if needed (README.md, strings.json)

6. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

7. **Push to GitHub:**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** on GitHub

## Commit Message Convention

We follow conventional commits for consistency:

- `feat:` New feature or integration capability
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks (dependencies, configs, etc.)
- `perf:` Performance improvements
- `ci:` CI/CD changes

Examples:
```bash
git commit -m "feat: Add horizontal swing support"
git commit -m "fix: Correct temperature conversion for Fahrenheit"
git commit -m "docs: Update configuration instructions"
git commit -m "chore: Update pymitsubishi to 0.2.0"
git commit -m "test: Add tests for config flow"
```

## Dependencies

### PyMitsubishi Library

This integration depends on the [pymitsubishi](https://github.com/pymitsubishi/pymitsubishi) library. When contributing:

1. **Library changes**: If you need changes in pymitsubishi, contribute there first
2. **Version updates**: Update the requirement in manifest.json after pymitsubishi releases
3. **Compatibility**: Ensure backward compatibility when possible

### Home Assistant Compatibility

- Minimum supported Home Assistant version is specified in `manifest.json`
- Follow Home Assistant's deprecation policy
- Test with both minimum and latest HA versions

## Getting Help

If you have questions:

1. Check existing [GitHub Issues](https://github.com/pymitsubishi/homeassistant-mitsubishi/issues)
2. Review the [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
3. Review the [README](README.md)
4. Create a new issue for discussion

## Related Projects

- [pymitsubishi](https://github.com/pymitsubishi/pymitsubishi) - The Python library this integration uses
- [Home Assistant](https://github.com/home-assistant/core) - The home automation platform
- [HACS](https://github.com/hacs/integration) - Home Assistant Community Store

Thank you for contributing to the Home Assistant Mitsubishi Integration!
