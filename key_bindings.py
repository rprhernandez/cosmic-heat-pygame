"""
key_bindings.py – Runtime-editable keyboard bindings for Cosmic Heat.

The ``KeyBindings`` class is the single source of truth for every
remappable action in the game.  Both ``controls.py`` (held-key movement)
and ``main.py`` (event-driven shoot / pause / quit) read their keys from
the shared ``bindings`` instance that is created at the bottom of this
module.

Actions
-------
move_left, move_right, move_up, move_down
    Directional movement, read every frame via ``pygame.key.get_pressed``.
shoot
    Fire a bullet; triggers on KEYDOWN and is cleared on KEYUP.
pause
    Toggle the pause overlay.
quit
    Immediately exit the game.

Remapping
---------
Call ``bindings.start_remap(action)`` to enter capture mode for a single
action.  On the next call to ``bindings.process_event(event)`` that
delivers a KEYDOWN event, the new key is recorded and capture mode ends.
The method returns True when a remap was consumed so callers can skip
their own event handling for that event.

Collision detection
-------------------
``KeyBindings.set_key`` refuses to bind a key that is already claimed by
another action, returning False in that case.  The remapping screen
displays the rejection message so the player always knows why a key was
not accepted.

Persistence
-----------
Bindings are saved to ``keybindings.json`` in the game directory.
``save()`` writes the current bindings; ``load()`` restores them.
The module calls ``load()`` automatically at import time so that
player customisations survive across sessions.
"""

from __future__ import annotations

import json
import os
import pygame


# Human-readable display names for every action shown on the remap screen.
ACTION_LABELS = {
    "move_left":  "Move Left",
    "move_right": "Move Right",
    "move_up":    "Move Up",
    "move_down":  "Move Down",
    "shoot":      "Shoot",
    "pause":      "Pause",
    "quit":       "Quit",
}

# Canonical order in which actions are listed on the remap screen.
ACTION_ORDER = [
    "move_left",
    "move_right",
    "move_up",
    "move_down",
    "shoot",
    "pause",
    "quit",
]

# Default key assignments (original hard-coded values from the game).
DEFAULT_BINDINGS = {
    "move_left":  pygame.K_LEFT,
    "move_right": pygame.K_RIGHT,
    "move_up":    pygame.K_UP,
    "move_down":  pygame.K_DOWN,
    "shoot":      pygame.K_SPACE,
    "pause":      pygame.K_p,
    "quit":       pygame.K_ESCAPE,
}

# Path to the JSON file where bindings are persisted.
_BINDINGS_FILE = os.path.join(os.path.dirname(__file__), "keybindings.json")


class KeyBindings:
    """Holds the current key assignment for every remappable action."""

    def __init__(self):
        # Live mapping: action name → pygame key constant.
        self._keys: dict[str, int] = dict(DEFAULT_BINDINGS)

        # When not None, the next KEYDOWN event will be bound to this action.
        self._pending_action: str | None = None

        # Queue of actions still to be remapped during a "Remap All" session.
        self._remap_queue: list[str] = []

        # Set to a non-empty string when the most recent remap attempt was
        # rejected (e.g. the key was already in use).  Cleared as soon as a
        # new remap session starts.
        self.conflict_message: str = ""

    # ------------------------------------------------------------------
    # Key lookups used by controls.py and main.py
    # ------------------------------------------------------------------

    def get(self, action: str) -> int:
        """Return the pygame key constant currently bound to *action*."""
        return self._keys[action]

    # ------------------------------------------------------------------
    # Remapping API
    # ------------------------------------------------------------------

    def start_remap(self, action: str) -> None:
        """Enter capture mode: the next KEYDOWN event binds *action*."""
        if action not in self._keys:
            raise ValueError(f"Unknown action: {action!r}")
        self._pending_action = action
        self.conflict_message = ""

    def start_remap_all(self) -> None:
        """Begin a sequential remap of every action in ACTION_ORDER."""
        self._remap_queue = list(ACTION_ORDER)
        self._advance_remap_queue()

    def _advance_remap_queue(self) -> None:
        """Pop the next action from the queue and start its capture."""
        if self._remap_queue:
            next_action = self._remap_queue.pop(0)
            self._pending_action = next_action
            self.conflict_message = ""
        else:
            self._pending_action = None

    def cancel_remap_all(self) -> None:
        """Cancel any in-progress remap-all session."""
        self._remap_queue = []
        self._pending_action = None
        self.conflict_message = ""

    @property
    def is_waiting(self) -> bool:
        """True while a remap capture is in progress."""
        return self._pending_action is not None

    @property
    def is_remap_all_active(self) -> bool:
        """True while a remap-all session is in progress."""
        return self.is_waiting or len(self._remap_queue) > 0

    @property
    def waiting_for(self) -> str | None:
        """The action currently awaiting a new key, or None."""
        return self._pending_action

    def process_event(self, event: pygame.event.Event) -> bool:
        """
        Feed a pygame event into the remap system.

        Returns True if the event was consumed by the remap system (the
        caller should then skip its own handling of that event), False
        otherwise.
        """
        if not self.is_waiting:
            return False
        if event.type != pygame.KEYDOWN:
            return False

        new_key = event.key

        # Escape cancels the remap without changing anything.
        if new_key == pygame.K_ESCAPE:
            self.cancel_remap_all()
            return True

        action = self._pending_action
        accepted = self._set_key(action, new_key)
        if not accepted:
            # Keep capture mode active so the player can try again.
            owner = self._owner_of(new_key)
            label = ACTION_LABELS.get(owner, owner)
            self.conflict_message = (
                f"{pygame.key.name(new_key).upper()} is already used by '{label}'"
            )
        else:
            self.conflict_message = ""
            # If we're in a remap-all session, advance to the next action.
            if self._remap_queue:
                self._advance_remap_queue()
            else:
                self._pending_action = None
            # Auto-save after each successful remap.
            self.save()
        return True

    def reset_to_defaults(self) -> None:
        """Restore every binding to its original default value."""
        self._keys = dict(DEFAULT_BINDINGS)
        self._pending_action = None
        self._remap_queue = []
        self.conflict_message = ""
        self.save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write current bindings to keybindings.json."""
        data = {action: key for action, key in self._keys.items()}
        try:
            with open(_BINDINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # Silently ignore write failures.

    def load(self) -> None:
        """Load bindings from keybindings.json if it exists."""
        if not os.path.exists(_BINDINGS_FILE):
            return
        try:
            with open(_BINDINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for action in ACTION_ORDER:
                if action in data and isinstance(data[action], int):
                    self._keys[action] = data[action]
        except (OSError, json.JSONDecodeError, TypeError):
            pass  # Silently ignore read failures; keep defaults.

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_key(self, action: str, key: int) -> bool:
        """
        Bind *key* to *action*.

        Returns False without making any change if *key* is already
        claimed by a different action.
        """
        owner = self._owner_of(key)
        if owner is not None and owner != action:
            return False
        self._keys[action] = key
        return True

    def _owner_of(self, key: int) -> str | None:
        """Return the action that owns *key*, or None if it is free."""
        for action, bound_key in self._keys.items():
            if bound_key == key:
                return action
        return None


# Module-level singleton shared by all other modules.
bindings = KeyBindings()
bindings.load()  # Restore saved bindings on startup.