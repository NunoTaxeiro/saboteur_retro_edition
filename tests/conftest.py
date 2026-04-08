"""
conftest.py – stub out pygame (and its sub-modules) so that the
game-logic portions of saboteur.py can be imported and tested
without a display or audio hardware.
"""

import sys
import types

# ---------------------------------------------------------------------------
# Build a minimal pygame stub that satisfies every attribute/call used at
# module-import time inside saboteur.py.
# ---------------------------------------------------------------------------

def _make_pygame_stub():
    pygame = types.ModuleType("pygame")

    # Basic constants used at module level
    pygame.QUIT = 256
    pygame.KEYDOWN = 768
    pygame.MOUSEBUTTONDOWN = 1025
    pygame.MOUSEBUTTONUP = 1026
    pygame.MOUSEMOTION = 1024
    pygame.K_ESCAPE = 27
    pygame.K_RETURN = 13
    pygame.K_SPACE = 32
    pygame.K_LEFT = 276
    pygame.K_RIGHT = 275
    pygame.K_UP = 273
    pygame.K_DOWN = 274
    pygame.SRCALPHA = 0x00010000
    pygame.RESIZABLE = 0

    # Sentinel objects returned by pygame calls
    class _Surf:
        def __init__(self, *a, **kw):
            self.size = (0, 0)
        def get_size(self):
            return self.size
        def get_width(self):
            return self.size[0]
        def get_height(self):
            return self.size[1]
        def fill(self, *a, **kw): pass
        def blit(self, *a, **kw): pass
        def set_alpha(self, *a, **kw): pass
        def convert(self, *a, **kw): return self
        def convert_alpha(self, *a, **kw): return self
        def get_rect(self, **kw): return _Rect(0, 0, 0, 0)

    class _Rect:
        def __init__(self, x=0, y=0, w=0, h=0):
            self.x = x; self.y = y
            self.width = w; self.height = h
            self.left = x; self.right = x + w
            self.top = y; self.bottom = y + h
            self.centerx = x + w // 2
            self.centery = y + h // 2
        def collidepoint(self, *a): return False
        def inflate(self, *a): return self
        def move(self, *a): return self

    class _Font:
        def render(self, text, aa, color, bg=None):
            return _Surf()
        def size(self, text):
            return (len(text) * 8, 16)

    class _Clock:
        def tick(self, fps=30): return 33

    class _Sound:
        def play(self, *a, **kw): pass
        def stop(self, *a, **kw): pass
        def set_volume(self, *a): pass

    class _Mixer:
        Sound = _Sound
        def get_init(self): return True
        def init(self, **kw): pass
        def stop(self): pass
        music = types.SimpleNamespace(
            load=lambda *a, **kw: None,
            play=lambda *a, **kw: None,
            stop=lambda *a, **kw: None,
            set_volume=lambda *a: None,
        )

    class _Display:
        def set_mode(self, *a, **kw): return _Surf()
        def set_caption(self, *a): pass
        def flip(self): pass
        def get_surface(self): return _Surf()

    class _Draw:
        def rect(self, *a, **kw): pass
        def circle(self, *a, **kw): pass
        def line(self, *a, **kw): pass
        def polygon(self, *a, **kw): pass
        def aaline(self, *a, **kw): pass

    class _Event:
        def get(self): return []

    class _Transform:
        def scale(self, surf, size): return surf
        def smoothscale(self, surf, size): return surf

    pygame.Surface = _Surf
    pygame.Rect = _Rect
    pygame.Clock = _Clock

    pygame.mixer = _Mixer()
    # pygame.mixer.Sound must be accessible as a class
    pygame.mixer.Sound = _Sound

    pygame.display = _Display()
    pygame.draw = _Draw()
    pygame.event = _Event()
    pygame.transform = _Transform()

    pygame.font = types.SimpleNamespace(
        init=lambda: None,
        SysFont=lambda *a, **kw: _Font(),
        Font=lambda *a, **kw: _Font(),
    )

    pygame.time = types.SimpleNamespace(
        Clock=_Clock,
        get_ticks=lambda: 0,
        delay=lambda ms: None,
    )

    pygame.init = lambda: (0, 0)
    pygame.quit = lambda: None

    def sndarray_make_sound(arr):
        return _Sound()

    pygame.sndarray = types.SimpleNamespace(make_sound=sndarray_make_sound)

    # Sub-modules that may be imported elsewhere
    for sub in ("locals", "sprite", "image", "key", "mouse", "cursors"):
        mod = types.ModuleType(f"pygame.{sub}")
        sys.modules[f"pygame.{sub}"] = mod
        setattr(pygame, sub, mod)

    pygame.key = types.SimpleNamespace(
        get_pressed=lambda: {},
        get_mods=lambda: 0,
    )
    pygame.mouse = types.SimpleNamespace(
        get_pos=lambda: (0, 0),
        get_pressed=lambda: (False, False, False),
    )

    return pygame


# Register the stub before any test module imports saboteur
if "pygame" not in sys.modules:
    sys.modules["pygame"] = _make_pygame_stub()
