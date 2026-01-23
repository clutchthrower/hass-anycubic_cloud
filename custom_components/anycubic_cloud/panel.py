"""Anycubic Cloud frontend panel."""
from __future__ import annotations

import os
from typing import Any

from homeassistant.components import frontend, panel_custom
from homeassistant.components.lovelace.const import (
    CONF_RESOURCE_TYPE_WS,
    CONF_URL,
    DOMAIN as LOVELACE_DOMAIN,
    MODE_STORAGE,
)
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    CARD_FILENAME,
    CARD_URL,
    CUSTOM_COMPONENTS,
    DOMAIN,
    INTEGRATION_FOLDER,
    LOGGER,
    PANEL_FILENAME,
    PANEL_FOLDER,
    PANEL_ICON,
    PANEL_NAME,
    PANEL_TITLE,
)
from .helpers import extract_panel_card_config

PANEL_URL = "/anycubic-cloud-panel-static"


def process_card_config(
    conf_object: Any,
) -> dict[str, Any]:
    if isinstance(conf_object, dict):
        return extract_panel_card_config(conf_object)
    else:
        return {}


async def async_register_lovelace_card_resource(hass: HomeAssistant) -> None:
    lovelace_data = hass.data.get(LOVELACE_DOMAIN)
    if not lovelace_data:
        return

    if lovelace_data.get("mode") != MODE_STORAGE:
        LOGGER.debug(
            "Lovelace in %s mode; skipping card resource registration",
            lovelace_data.get("mode"),
        )
        return

    resources = lovelace_data.get("resources")
    if not isinstance(resources, ResourceStorageCollection):
        return

    if getattr(resources, "loaded", False) is False:
        await resources.async_load()
        resources.loaded = True

    if any(item.get(CONF_URL) == CARD_URL for item in resources.async_items()):
        return

    await resources.async_create_item(
        {
            CONF_RESOURCE_TYPE_WS: "module",
            CONF_URL: CARD_URL,
        }
    )


async def async_register_panel(
    hass: HomeAssistant,
    conf_object: Any,
) -> None:
    """Register the Anycubic Cloud frontend panel."""
    if DOMAIN not in hass.data.get("frontend_panels", {}):
        root_dir = os.path.join(
            hass.config.path(CUSTOM_COMPONENTS),
            INTEGRATION_FOLDER,
        )
        panel_dir = os.path.join(root_dir, PANEL_FOLDER)
        view_url = os.path.join(panel_dir, PANEL_FILENAME)
        card_url = os.path.join(panel_dir, CARD_FILENAME)

        try:
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(PANEL_URL, view_url, cache_headers=False),
                    StaticPathConfig(CARD_URL, card_url, cache_headers=False),
                ]
            )
        except RuntimeError as e:
            if "already registered" not in str(e):
                raise e

        conf = process_card_config(conf_object)

        LOGGER.debug(f"Processed panel config: {conf}")

        await panel_custom.async_register_panel(
            hass,
            webcomponent_name=PANEL_NAME,
            frontend_url_path=DOMAIN,
            module_url=PANEL_URL,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            require_admin=False,
            config=conf,
        )

        await async_register_lovelace_card_resource(hass)


def async_unregister_panel(hass: HomeAssistant) -> None:
    frontend.async_remove_panel(hass, DOMAIN)
    LOGGER.debug("Removing panel")
