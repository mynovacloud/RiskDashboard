from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter


@dataclass
class Automation:
    """Describes a single automation that plugs into the app.

    Each automation owns its own APIRouter (its pages + processing endpoints).
    The factory mounts every registered automation's router under its
    mount_prefix. The 'primary' automation owns the root path ("/").
    """

    slug: str
    name: str
    description: str
    router: APIRouter
    mount_prefix: str = ""
    nav_label: Optional[str] = None
    is_primary: bool = False


_REGISTRY: "dict[str, Automation]" = {}


def register(automation: Automation) -> Automation:
    _REGISTRY[automation.slug] = automation
    return automation


def all_automations() -> "list[Automation]":
    return list(_REGISTRY.values())


def get(slug: str) -> Automation:
    return _REGISTRY[slug]


def primary() -> Optional[Automation]:
    for automation in _REGISTRY.values():
        if automation.is_primary:
            return automation
    values = list(_REGISTRY.values())
    return values[0] if values else None
