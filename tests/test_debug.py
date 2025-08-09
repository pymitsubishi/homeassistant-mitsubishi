"""Debug test to understand hass fixture."""

import pytest


@pytest.mark.asyncio
async def test_hass_debug(hass):
    """Debug what hass provides."""
    print(f"hass type: {type(hass)}")
    print(f"hass attributes: {[attr for attr in dir(hass) if not attr.startswith('_')]}")
    if hasattr(hass, "config_entries"):
        print(f"config_entries type: {type(hass.config_entries)}")
        print(
            f"config_entries methods: {[method for method in dir(hass.config_entries) if not method.startswith('_')]}"
        )
    assert True  # Just to pass the test
