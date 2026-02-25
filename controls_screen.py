"""
controls_screen.py – In-game "Controls" / key-remapping screen.

``show_controls_screen(screen, clock)`` blocks until the player closes
the screen, then returns.  The screen lets the player:

* See every remappable action alongside its currently bound key.
* Click a row (or navigate with UP / DOWN + ENTER) to rebind that action.
* Press the highlighted key to capture a new binding.
* Press ESC during capture to cancel without changing anything.
* Click / activate the "Remap All" button to walk through every action
  in sequence (one key press per action).
* Click / activate the "Reset to Defaults" button to restore every
  binding at once.
* Click / activate the "Back" button (or press ESC outside capture mode)
  to leave the screen.

Visual states
-------------
Normal row        – white label, grey key name
Selected row      – red border drawn around the row rectangle
Awaiting input    – the selected row's key cell is filled yellow and its
                    text reads "Press a key…"
Conflict message  – shown in red below the table for one remap cycle
"""

import pygame
from classes.constants import WIDTH, HEIGHT, BLACK, WHITE, RED, YELLOW
from key_bindings import bindings, ACTION_ORDER, ACTION_LABELS


# Layout constants
_ROW_HEIGHT = 54
_TABLE_TOP = 160
_TABLE_LEFT = WIDTH // 2 - 280
_TABLE_WIDTH = 560
_LABEL_COL_W = 320   # width of the action-name column
_KEY_COL_W = 240     # width of the bound-key column
_FONT_LARGE = None   # initialised lazily inside show_controls_screen
_FONT_MED = None
_FONT_SMALL = None


def _ensure_fonts() -> None:
    global _FONT_LARGE, _FONT_MED, _FONT_SMALL
    if _FONT_LARGE is None:
        _FONT_LARGE = pygame.font.SysFont("Comic Sans MS", 44)
        _FONT_MED = pygame.font.SysFont("Comic Sans MS", 30)
        _FONT_SMALL = pygame.font.SysFont("Comic Sans MS", 22)


def _row_rect(index: int) -> pygame.Rect:
    """Return the full-width rect for the table row at *index*."""
    return pygame.Rect(
        _TABLE_LEFT,
        _TABLE_TOP + index * _ROW_HEIGHT,
        _TABLE_WIDTH,
        _ROW_HEIGHT - 4,
    )


def _key_cell_rect(index: int) -> pygame.Rect:
    """Return the rect for the key column of the row at *index*."""
    r = _row_rect(index)
    return pygame.Rect(r.left + _LABEL_COL_W, r.top, _KEY_COL_W, r.height)


def show_controls_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """
    Display the controls / remapping screen and block until the player
    exits it.  Modifies ``key_bindings.bindings`` in-place.
    """
    _ensure_fonts()

    n_actions = len(ACTION_ORDER)

    # Y position immediately below the last table row.
    table_bottom = _TABLE_TOP + n_actions * _ROW_HEIGHT + 10

    # Button row 1: "Remap All"
    remap_all_btn = pygame.Rect(WIDTH // 2 - 100, table_bottom + 20, 200, 44)
    # Button row 2: "Reset to Defaults" and "Back"
    reset_btn = pygame.Rect(WIDTH // 2 - 210, table_bottom + 74, 200, 44)
    back_btn = pygame.Rect(WIDTH // 2 + 10, table_bottom + 74, 200, 44)

    # Keyboard navigation indices:
    #   0..(n_actions-1) = table rows
    #   -1 = Remap All
    #   -2 = Reset Defaults
    #   -3 = Back
    selected_row: int = 0

    running = True
    while running:
        # ----------------------------------------------------------------
        # Event processing
        # ----------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            # Let the bindings system consume the event first when a
            # capture is in progress.
            if bindings.process_event(event):
                # During remap-all, advance the visual selection to track
                # the current action being captured.
                if bindings.is_waiting and bindings.waiting_for in ACTION_ORDER:
                    selected_row = ACTION_ORDER.index(bindings.waiting_for)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_UP:
                    if selected_row == -3:        # Back → Reset
                        selected_row = -2
                    elif selected_row == -2:      # Reset → Remap All
                        selected_row = -1
                    elif selected_row == -1:      # Remap All → last action row
                        selected_row = n_actions - 1
                    elif selected_row > 0:
                        selected_row -= 1
                    else:                         # first row → Back
                        selected_row = -3

                elif event.key == pygame.K_DOWN:
                    if selected_row == -1:        # Remap All → Reset
                        selected_row = -2
                    elif selected_row == -2:      # Reset → Back
                        selected_row = -3
                    elif selected_row == -3:      # Back → first action row
                        selected_row = 0
                    elif selected_row < n_actions - 1:
                        selected_row += 1
                    else:                         # last row → Remap All
                        selected_row = -1

                elif event.key == pygame.K_RETURN:
                    if selected_row == -1:
                        bindings.start_remap_all()
                        selected_row = 0  # visual selection follows the capture
                    elif selected_row == -2:
                        bindings.reset_to_defaults()
                    elif selected_row == -3:
                        running = False
                    else:
                        action = ACTION_ORDER[selected_row]
                        bindings.start_remap(action)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Check table rows.
                clicked_row = None
                for i in range(n_actions):
                    if _row_rect(i).collidepoint(mx, my):
                        clicked_row = i
                        break

                if clicked_row is not None:
                    selected_row = clicked_row
                    action = ACTION_ORDER[clicked_row]
                    bindings.start_remap(action)
                elif remap_all_btn.collidepoint(mx, my):
                    bindings.start_remap_all()
                    selected_row = 0
                elif reset_btn.collidepoint(mx, my):
                    bindings.reset_to_defaults()
                elif back_btn.collidepoint(mx, my):
                    running = False

        # ----------------------------------------------------------------
        # Drawing
        # ----------------------------------------------------------------
        screen.fill((10, 10, 30))

        # Title
        title_surf = _FONT_LARGE.render("CONTROLS", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(centerx=WIDTH // 2, y=60))

        # Subtitle / hint
        if bindings.is_waiting:
            hint = f"Press a key for  '{ACTION_LABELS[bindings.waiting_for]}'  (ESC to cancel)"
            hint_color = YELLOW
        else:
            hint = "Click a row or press ENTER to rebind  |  ESC = back"
            hint_color = (180, 180, 180)
        hint_surf = _FONT_SMALL.render(hint, True, hint_color)
        screen.blit(hint_surf, hint_surf.get_rect(centerx=WIDTH // 2, y=115))

        # Table rows
        for i, action in enumerate(ACTION_ORDER):
            row_r = _row_rect(i)
            key_r = _key_cell_rect(i)
            is_selected = (selected_row == i)
            is_awaiting = bindings.is_waiting and bindings.waiting_for == action

            # Row background
            row_bg_color = (30, 30, 60) if i % 2 == 0 else (20, 20, 50)
            pygame.draw.rect(screen, row_bg_color, row_r, border_radius=6)

            # Key cell highlight when awaiting input
            if is_awaiting:
                pygame.draw.rect(screen, YELLOW, key_r, border_radius=6)

            # Red border for the currently selected row
            if is_selected:
                pygame.draw.rect(screen, RED, row_r, width=3, border_radius=6)

            # Action label
            label_surf = _FONT_MED.render(ACTION_LABELS[action], True, WHITE)
            label_rect = label_surf.get_rect(
                midleft=(row_r.left + 12, row_r.centery)
            )
            screen.blit(label_surf, label_rect)

            # Key name
            if is_awaiting:
                key_text = "Press a key…"
                key_color = BLACK
            else:
                key_text = pygame.key.name(bindings.get(action)).upper()
                key_color = (220, 220, 100)
            key_surf = _FONT_MED.render(key_text, True, key_color)
            key_rect = key_surf.get_rect(center=key_r.center)
            screen.blit(key_surf, key_rect)

        # Conflict message
        if bindings.conflict_message:
            conflict_surf = _FONT_SMALL.render(
                bindings.conflict_message, True, RED
            )
            screen.blit(
                conflict_surf,
                conflict_surf.get_rect(centerx=WIDTH // 2, y=table_bottom - 2),
            )

        # Remap All button
        remap_all_color = (50, 50, 80) if selected_row != -1 else (70, 40, 90)
        pygame.draw.rect(screen, remap_all_color, remap_all_btn, border_radius=8)
        if selected_row == -1:
            pygame.draw.rect(screen, RED, remap_all_btn, width=3, border_radius=8)
        remap_all_surf = _FONT_MED.render("Remap All", True, WHITE)
        screen.blit(remap_all_surf, remap_all_surf.get_rect(center=remap_all_btn.center))

        # Reset button
        reset_color = (60, 60, 60) if selected_row != -2 else (80, 30, 30)
        pygame.draw.rect(screen, reset_color, reset_btn, border_radius=8)
        if selected_row == -2:
            pygame.draw.rect(screen, RED, reset_btn, width=3, border_radius=8)
        reset_surf = _FONT_MED.render("Reset Defaults", True, WHITE)
        screen.blit(reset_surf, reset_surf.get_rect(center=reset_btn.center))

        # Back button
        back_color = (30, 60, 30) if selected_row != -3 else (20, 80, 20)
        pygame.draw.rect(screen, back_color, back_btn, border_radius=8)
        if selected_row == -3:
            pygame.draw.rect(screen, RED, back_btn, width=3, border_radius=8)
        back_surf = _FONT_MED.render("Back", True, WHITE)
        screen.blit(back_surf, back_surf.get_rect(center=back_btn.center))

        pygame.display.flip()
        clock.tick(60)