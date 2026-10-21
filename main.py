"""
MOTO RIDER GO  -  UA Software Technology
Created By Usman Arshad

Install:  pip install pygame
Run:      python moto_rider_go.py

Flow:  Intro animation -> Main menu (Settings / Play) -> Mode (Easy / Medium / Difficult,
       Garage, Season) -> Level select (1-200) -> Game
"""
import pygame, random, math, sys, os, json
from array import array

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
W, H = 900, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Moto Rider GO - UA Software Technology")
clock = pygame.time.Clock()
FPS = 60

ROAD_X, LANE_W, LANES = 250, 100, 4
ROAD_W = LANE_W * LANES
ROAD_R = ROAD_X + ROAD_W
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")
MAX_LEVEL = 200


def lane_cx(i):
    return ROAD_X + LANE_W * i + LANE_W // 2


def font(size, bold=True):
    return pygame.font.SysFont("arial", size, bold=bold)


F_HUGE, F_BIG, F_MID, F_SM, F_XS = font(72), font(48), font(30), font(22), font(16)

# ====================================================================== DATA
KEYS_DEFAULT = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "accel": pygame.K_UP,
                "brake": pygame.K_DOWN, "nitro": pygame.K_SPACE}
KEY_LABELS = [("left", "Move Left"), ("right", "Move Right"), ("accel", "Accelerate"),
              ("brake", "Brake"), ("nitro", "Nitro Boost")]


def default_data():
    return {"coins": 0, "owned": [0], "bike": 0, "colors": [0] * 6, "season": "summer",
            "done": {"easy": 0, "medium": 0, "hard": 0}, "best": 0,
            "sfx": True, "music": True, "keys": dict(KEYS_DEFAULT)}


def load_data():
    d = default_data()
    try:
        with open(SAVE) as f:
            raw = json.load(f)
        for k, v in raw.items():
            if k in d:
                if isinstance(d[k], dict) and isinstance(v, dict):
                    d[k].update(v)
                else:
                    d[k] = v
    except Exception:
        pass
    if len(d["colors"]) < 6:
        d["colors"] += [0] * (6 - len(d["colors"]))
    return d


def save_data():
    try:
        with open(SAVE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


data = load_data()

DIFFS = {
    "easy": {"name": "EASY", "mult": 0.78, "dens": 0.8, "color": (40, 170, 90), "desc": "Slow speed - relaxed ride"},
    "medium": {"name": "MEDIUM", "mult": 1.0, "dens": 1.0, "color": (230, 150, 30), "desc": "Faster speed"},
    "hard": {"name": "DIFFICULT", "mult": 1.3, "dens": 1.2, "color": (210, 50, 60), "desc": "Very high speed!"},
}
DIFF_KEYS = ["easy", "medium", "hard"]


def level_len(l):
    return 15000 + l * 350


def level_reward(l):
    return 10 + (l - 1) * 2


BIKES = [
    {"name": "Rookie", "price": 0, "speed": 1.00, "handling": 1.00, "nitro": 1.0, "fw": 12, "extra": ""},
    {"name": "Scout", "price": 150, "speed": 1.02, "handling": 1.10, "nitro": 1.0, "fw": 10, "extra": "stripe"},
    {"name": "Thunder", "price": 400, "speed": 1.05, "handling": 1.15, "nitro": 1.2, "fw": 14, "extra": "wings"},
    {"name": "Phantom", "price": 800, "speed": 1.07, "handling": 1.25, "nitro": 1.3, "fw": 11, "extra": "stripe"},
    {"name": "Inferno", "price": 1500, "speed": 1.10, "handling": 1.30, "nitro": 1.5, "fw": 14, "extra": "twin"},
    {"name": "Apex GP", "price": 3000, "speed": 1.12, "handling": 1.45, "nitro": 1.8, "fw": 15, "extra": "wings twin"},
]
PALETTES = [((200, 25, 40), (25, 90, 190)), ((30, 100, 220), (240, 240, 245)),
            ((30, 170, 80), (40, 40, 48)), ((255, 130, 30), (30, 30, 40)),
            ((140, 60, 210), (255, 100, 200)), ((35, 35, 42), (240, 190, 50))]

SEASONS = {
    "summer": {"name": "Summer", "grass": ((34, 120, 52), (38, 130, 57)), "road": (52, 54, 60),
               "tint": (255, 200, 90, 20), "night": 0.40, "grip": 1.0,
               "trees": [(30, 130, 60), (40, 150, 70), (25, 110, 55)],
               "sky": ((80, 160, 235), (190, 230, 255)), "icon": "sun"},
    "winter": {"name": "Winter", "grass": ((222, 230, 240), (210, 220, 236)), "road": (70, 74, 86),
               "tint": (190, 210, 255, 36), "night": 0.55, "grip": 0.78,
               "trees": [(30, 90, 60), (35, 100, 66), (28, 80, 55)],
               "sky": ((150, 170, 200), (225, 232, 246)), "icon": "snow"},
    "rain": {"name": "Rain", "grass": ((22, 88, 44), (26, 96, 48)), "road": (34, 36, 44),
             "tint": (20, 30, 55, 90), "night": 0.45, "grip": 0.86,
             "trees": [(20, 90, 48), (24, 100, 54), (18, 78, 44)],
             "sky": ((60, 70, 92), (120, 130, 152)), "icon": "cloud"},
    "autumn": {"name": "Autumn", "grass": ((140, 112, 46), (150, 120, 50)), "road": (58, 56, 58),
               "tint": (255, 140, 40, 26), "night": 0.50, "grip": 0.94,
               "trees": [(210, 100, 30), (190, 50, 30), (230, 170, 40)],
               "sky": ((225, 140, 75), (250, 215, 150)), "icon": "leaf"},
}
SEASON_KEYS = ["summer", "winter", "rain", "autumn"]


# ====================================================================== AUDIO
SOUND_OK = False
SR, CH = 22050, 1
SFX, ENGINE, MUSIC = {}, [], {}
ENG_CH = MUS_CH = None
_eng_br = -1
_music_name = None


def init_audio():
    global SOUND_OK, SR, CH, ENG_CH, MUS_CH
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(22050, -16, 1, 512)
        f, fmt, ch = pygame.mixer.get_init()
        if fmt != -16:
            return
        SR, CH = f, ch
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(2)
        ENG_CH, MUS_CH = pygame.mixer.Channel(0), pygame.mixer.Channel(1)
        SOUND_OK = True
    except Exception:
        SOUND_OK = False


def to_sound(buf, vol=1.0):
    a = array("h")
    for s in buf:
        v = int(max(-1.0, min(1.0, s)) * 30000)
        for _ in range(CH):
            a.append(v)
    snd = pygame.mixer.Sound(buffer=a.tobytes())
    snd.set_volume(vol)
    return snd


def osc(kind, ph):
    x = ph % 1.0
    if kind == "sine":
        return math.sin(x * math.tau)
    if kind == "square":
        return 1.0 if x < 0.5 else -1.0
    if kind == "saw":
        return 2 * x - 1
    return 4 * abs(x - 0.5) - 1  # triangle


def tone(freq, dur, kind="sine", vol=0.5, decay=3.0, slide=0.0):
    n = int(SR * dur)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        ph += (freq + slide * t) / SR
        env = min(1.0, t / 0.004) * math.exp(-decay * t / dur)
        out.append(osc(kind, ph) * vol * env)
    return out


def noise(dur, vol=0.5, decay=4.0, smooth=0.0, rise=False):
    n = int(SR * dur)
    out, y = [], 0.0
    a = 1.0 - smooth
    for i in range(n):
        y += (random.uniform(-1, 1) - y) * a
        k = i / n
        env = (k ** 1.5) * (1 - k) * 4 if rise else math.exp(-decay * k)
        out.append(y * vol * env)
    return out


def mix_into(dst, src, start, gain=1.0):
    end = min(len(dst), start + len(src))
    for i in range(start, end):
        dst[i] += src[i - start] * gain


def seq(*parts):
    out = []
    for p in parts:
        out += p
    return out


def engine_loop(cycles, dur=0.3):
    n = int(SR * dur)
    out = []
    for i in range(n):
        p = cycles * i / n
        s = 0.0
        for k in range(1, 6):
            s += math.sin(math.tau * k * p) / k
        am = 1 + 0.25 * math.sin(math.tau * 7 * i / n)
        out.append(s * 0.3 * am)
    return out


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


CHORDS = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [60, 64, 67]), (43, [55, 59, 62])]


def make_song(bpm, style):
    beat = 60.0 / bpm
    bar = beat * 4
    total = int(SR * bar * len(CHORDS))
    buf = [0.0] * total
    game = style == "game"
    for ci, (root, tri) in enumerate(CHORDS):
        base = int(SR * bar * ci)
        if game:
            for k in range(8):
                note = midi(root - 12 + (12 if k % 4 == 3 else 0))
                mix_into(buf, tone(note, beat / 2 * 0.9, "square", 0.16, 2.5), base + int(SR * beat / 2 * k))
            for k in range(16):
                note = midi(tri[(0, 1, 2, 1)[k % 4]] + 12)
                mix_into(buf, tone(note, beat / 4 * 0.9, "square", 0.07, 3), base + int(SR * beat / 4 * k))
            for k in range(4):
                mix_into(buf, tone(120, 0.18, "sine", 0.55, 6, -280), base + int(SR * beat * k))
                mix_into(buf, noise(0.05, 0.14, 6), base + int(SR * (beat * k + beat / 2)))
        else:
            for k in range(2):
                mix_into(buf, tone(midi(root - 12), beat * 1.9, "tri", 0.3, 1.2), base + int(SR * beat * 2 * k))
            for k in range(8):
                note = midi(tri[(0, 1, 2, 1, 2, 1, 0, 1)[k]] + 12)
                mix_into(buf, tone(note, beat / 2 * 1.4, "tri", 0.16, 2.5), base + int(SR * beat / 2 * k))
    return [s * 0.8 for s in buf]


def build_audio():
    if not SOUND_OK:
        return
    SFX["coin"] = to_sound(seq(tone(988, 0.06, "square", 0.22, 2), tone(1319, 0.2, "square", 0.22, 4)), 0.5)
    crash = noise(0.9, 0.9, 4, 0.6)
    mix_into(crash, tone(90, 0.5, "sine", 0.9, 5, -60), 0)
    SFX["crash"] = to_sound(crash, 0.8)
    SFX["nitro"] = to_sound(noise(0.6, 0.55, smooth=0.85, rise=True), 0.6)
    SFX["close"] = to_sound(noise(0.25, 0.5, smooth=0.7, rise=True), 0.45)
    SFX["click"] = to_sound(tone(700, 0.05, "square", 0.2, 3), 0.5)
    SFX["error"] = to_sound(tone(150, 0.22, "square", 0.3, 2), 0.5)
    SFX["buy"] = to_sound(seq(tone(784, 0.1, "tri", 0.4, 2), tone(988, 0.1, "tri", 0.4, 2), tone(1319, 0.3, "tri", 0.4, 3)), 0.6)
    win = seq(tone(523, 0.14, "square", 0.2, 2), tone(659, 0.14, "square", 0.2, 2),
              tone(784, 0.14, "square", 0.2, 2), tone(1047, 0.5, "tri", 0.4, 3))
    SFX["win"] = to_sound(win, 0.6)
    SFX["intro"] = to_sound(seq(tone(262, 0.2, "tri", 0.4, 2), tone(330, 0.2, "tri", 0.4, 2),
                                tone(392, 0.2, "tri", 0.4, 2), tone(523, 0.7, "tri", 0.45, 3)), 0.6)
    for c in (14, 22, 32):
        ENGINE.append(to_sound(engine_loop(c), 1.0))
    MUSIC["menu"] = to_sound(make_song(92, "menu"), 1.0)
    MUSIC["game"] = to_sound(make_song(138, "game"), 1.0)


def sfx(name):
    if SOUND_OK and data["sfx"] and name in SFX:
        SFX[name].play()


def play_music(name):
    global _music_name
    if not SOUND_OK or name not in MUSIC:
        return
    if not data["music"]:
        MUS_CH.stop()
        _music_name = None
        return
    if _music_name == name and MUS_CH.get_busy():
        return
    MUS_CH.play(MUSIC[name], loops=-1)
    MUS_CH.set_volume(0.4)
    _music_name = name


def engine_set(br, vol):
    global _eng_br
    if not SOUND_OK or not ENGINE:
        return
    if not data["sfx"]:
        ENG_CH.stop()
        _eng_br = -1
        return
    if br != _eng_br or not ENG_CH.get_busy():
        ENG_CH.play(ENGINE[br], loops=-1)
        _eng_br = br
    ENG_CH.set_volume(vol)


def engine_stop():
    global _eng_br
    if SOUND_OK and ENG_CH:
        ENG_CH.stop()
    _eng_br = -1


# ====================================================================== HELPERS
_glow_cache = {}


def glow(surf, pos, radius, color, strength=1.0):
    strength = round(strength, 1)
    key = (radius, color, strength)
    if key not in _glow_cache:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            a = (1 - r / radius) ** 2 * strength
            c = (min(255, int(color[0] * a)), min(255, int(color[1] * a)), min(255, int(color[2] * a)))
            pygame.draw.circle(s, c, (radius, radius), r)
        _glow_cache[key] = s.convert()
    surf.blit(_glow_cache[key], (int(pos[0]) - radius, int(pos[1]) - radius),
              special_flags=pygame.BLEND_RGB_ADD)


def text(surf, s, f, color, pos, center=True, alpha=255, shadow=True):
    img = f.render(s, True, color)
    img.set_alpha(alpha)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if shadow:
        sh = f.render(s, True, (0, 0, 0))
        sh.set_alpha(alpha // 2)
        surf.blit(sh, (r.x + 2, r.y + 3))
    surf.blit(img, r)
    return r


_grad_cache = {}


def vgradient(w, h, top, bottom):
    key = (w, h, top, bottom)
    if key not in _grad_cache:
        s = pygame.Surface((w, h))
        for y in range(h):
            t = y / max(1, h)
            s.fill([int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)], (0, y, w, 1))
        _grad_cache[key] = s
    return _grad_cache[key]


def tint(c, d):
    return tuple(max(0, min(255, v + d)) for v in c[:3])


_ov_cache = {}


def overlay(surf, color):
    if color[3] <= 0:
        return
    if color not in _ov_cache:
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill(color)
        _ov_cache[color] = s
    surf.blit(_ov_cache[color], (0, 0))


def quit_check(events):
    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def draw_icon(surf, kind, c, s, col=(255, 255, 255)):
    x, y = c
    if kind == "play":
        pygame.draw.polygon(surf, col, [(x - s * .32, y - s * .5), (x - s * .32, y + s * .5), (x + s * .5, y)])
    elif kind == "gear":
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, col, (x + math.cos(a) * s * .3, y + math.sin(a) * s * .3),
                             (x + math.cos(a) * s * .52, y + math.sin(a) * s * .52), max(3, int(s * .16)))
        pygame.draw.circle(surf, col, (int(x), int(y)), int(s * .38), max(2, int(s * .13)))
        pygame.draw.circle(surf, col, (int(x), int(y)), max(2, int(s * .1)))
    elif kind in ("left", "back"):
        pygame.draw.polygon(surf, col, [(x + s * .3, y - s * .5), (x + s * .3, y + s * .5), (x - s * .4, y)])
    elif kind == "right":
        pygame.draw.polygon(surf, col, [(x - s * .3, y - s * .5), (x - s * .3, y + s * .5), (x + s * .4, y)])
    elif kind == "coin":
        pygame.draw.circle(surf, (255, 205, 50), (int(x), int(y)), int(s * .5))
        pygame.draw.circle(surf, (200, 140, 10), (int(x), int(y)), int(s * .5), max(2, int(s * .1)))
        pygame.draw.circle(surf, (255, 240, 150), (int(x), int(y)), int(s * .22), 2)
    elif kind == "lock":
        pygame.draw.rect(surf, col, (x - s * .35, y - s * .05, s * .7, s * .5), border_radius=3)
        pygame.draw.arc(surf, col, (x - s * .22, y - s * .5, s * .44, s * .9), 0, math.pi, 3)
    elif kind == "bike":
        r = int(s * .2)
        pygame.draw.circle(surf, col, (int(x - s * .36), int(y + s * .15)), r, 3)
        pygame.draw.circle(surf, col, (int(x + s * .36), int(y + s * .15)), r, 3)
        pygame.draw.lines(surf, col, False, [(x - s * .36, y + s * .15), (x - s * .05, y - s * .15),
                                              (x + s * .25, y - s * .15), (x + s * .36, y + s * .15)], 3)
        pygame.draw.line(surf, col, (x + s * .25, y - s * .15), (x + s * .2, y - s * .4), 3)
    elif kind == "leaf":
        pygame.draw.polygon(surf, col, [(x - s * .45, y + s * .45), (x - s * .35, y - s * .15), (x, y - s * .45),
                                        (x + s * .45, y - s * .45), (x + s * .4, y), (x, y + s * .35)])
        pygame.draw.line(surf, (90, 60, 20), (x - s * .45, y + s * .45), (x + s * .2, y - s * .2), 2)
    elif kind == "check":
        pygame.draw.lines(surf, col, False, [(x - s * .4, y), (x - s * .1, y + s * .3), (x + s * .4, y - s * .3)], max(3, int(s * .15)))
    elif kind == "sun":
        pygame.draw.circle(surf, (255, 215, 60), (int(x), int(y)), int(s * .25))
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surf, (255, 215, 60), (x + math.cos(a) * s * .35, y + math.sin(a) * s * .35),
                             (x + math.cos(a) * s * .5, y + math.sin(a) * s * .5), 4)
    elif kind == "snow":
        for i in range(3):
            a = i * math.pi / 3
            pygame.draw.line(surf, (235, 245, 255), (x - math.cos(a) * s * .5, y - math.sin(a) * s * .5),
                             (x + math.cos(a) * s * .5, y + math.sin(a) * s * .5), 4)
    elif kind == "cloud":
        pygame.draw.circle(surf, (225, 232, 245), (int(x - s * .22), int(y)), int(s * .22))
        pygame.draw.circle(surf, (225, 232, 245), (int(x + s * .05), int(y - s * .12)), int(s * .27))
        pygame.draw.circle(surf, (225, 232, 245), (int(x + s * .3), int(y + s * .02)), int(s * .2))
        pygame.draw.rect(surf, (225, 232, 245), (x - s * .22, y, s * .74, s * .22))
        for i in range(3):
            pygame.draw.line(surf, (120, 170, 255), (x - s * .25 + i * s * .25, y + s * .32),
                             (x - s * .32 + i * s * .25, y + s * .5), 3)
    elif kind == "sound":
        pygame.draw.polygon(surf, col, [(x - s * .45, y - s * .15), (x - s * .2, y - s * .15), (x + s * .05, y - s * .4),
                                        (x + s * .05, y + s * .4), (x - s * .2, y + s * .15), (x - s * .45, y + s * .15)])
        pygame.draw.arc(surf, col, (x - s * .1, y - s * .3, s * .6, s * .6), -0.9, 0.9, 3)
    elif kind == "music":
        pygame.draw.circle(surf, col, (int(x - s * .2), int(y + s * .3)), int(s * .18))
        pygame.draw.line(surf, col, (x - s * .04, y + s * .3), (x - s * .04, y - s * .4), 3)
        pygame.draw.line(surf, col, (x - s * .04, y - s * .4), (x + s * .35, y - s * .25), 4)


class Button:
    def __init__(self, rect, label, icon=None, color=(50, 110, 210), bid=None, f=None, sub=None):
        self.rect = pygame.Rect(rect)
        self.label, self.icon, self.color, self.id = label, icon, color, bid
        self.font = f or F_MID
        self.sub = sub
        self.hover = 0.0
        self.enabled = True

    def draw(self, surf, focus=False):
        t = max(self.hover, 1.0 if focus else 0.0)
        r = self.rect.inflate(int(12 * t), int(6 * t))
        base = self.color if self.enabled else (70, 74, 88)
        top, bot = tint(base, 30 + int(30 * t)), tint(base, -45)
        pygame.draw.rect(surf, (0, 0, 0), r.move(0, 5), border_radius=18)
        pygame.draw.rect(surf, bot, r, border_radius=18)
        pygame.draw.rect(surf, top, (r.x, r.y, r.w, int(r.h * 0.58)),
                         border_top_left_radius=18, border_top_right_radius=18)
        pygame.draw.rect(surf, (255, 255, 255) if t > 0.5 else tint(base, 70), r, 2, border_radius=18)
        col = (255, 255, 255) if self.enabled else (150, 155, 170)
        has_text = bool(self.label)
        if self.icon:
            ix = r.x + 38 if has_text else r.centerx
            draw_icon(surf, self.icon, (ix, r.centery), min(34, r.h * 0.5), col)
        tx = r.centerx + (18 if (self.icon and has_text) else 0)
        if has_text:
            if self.sub:
                text(surf, self.label, self.font, col, (tx, r.centery - 12))
                text(surf, self.sub, F_XS, (235, 240, 255), (tx, r.centery + 22), shadow=False)
            else:
                text(surf, self.label, self.font, col, (tx, r.centery))


def ui_step(buttons, focus, events):
    clicked = None
    mp = pygame.mouse.get_pos()
    n = len(buttons)
    for e in events:
        if e.type == pygame.MOUSEMOTION:
            for i, b in enumerate(buttons):
                if b.enabled and b.rect.collidepoint(e.pos):
                    focus = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, b in enumerate(buttons):
                if b.enabled and b.rect.collidepoint(e.pos):
                    focus, clicked = i, b
        elif e.type == pygame.KEYDOWN and n:
            if e.key == pygame.K_DOWN:
                focus = (focus + 1) % n
            elif e.key == pygame.K_UP:
                focus = (focus - 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and buttons[focus].enabled:
                clicked = buttons[focus]
    for i, b in enumerate(buttons):
        target = 1.0 if (i == focus or (b.enabled and b.rect.collidepoint(mp))) else 0.0
        b.hover += (target - b.hover) * 0.25
    return clicked, focus


def coin_hud(surf):
    s = str(data["coins"])
    img = F_SM.render(s, True, (255, 230, 120))
    w = img.get_width() + 62
    r = pygame.Rect(W - w - 20, 14, w, 40)
    pygame.draw.rect(surf, (15, 18, 34), r, border_radius=20)
    pygame.draw.rect(surf, (255, 205, 50), r, 2, border_radius=20)
    draw_icon(surf, "coin", (r.x + 24, r.centery), 26)
    surf.blit(img, (r.x + 46, r.centery - img.get_height() // 2))


# ====================================================================== SPRITES
def make_car(color, w=60, h=112):
    s = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
    ox, oy = 8, 8
    pygame.draw.ellipse(s, (0, 0, 0, 90), (ox - 2, oy + 6, w + 4, h))
    dark, light = tint(color, -60), tint(color, 50)
    pygame.draw.rect(s, dark, (ox, oy, w, h), border_radius=18)
    pygame.draw.rect(s, color, (ox + 2, oy + 2, w - 4, h - 8), border_radius=16)
    pygame.draw.rect(s, light, (ox + 8, oy + 8, w - 16, 14), border_radius=8)
    pygame.draw.rect(s, (30, 45, 70), (ox + 8, oy + 30, w - 16, 20), border_radius=6)
    pygame.draw.rect(s, light, (ox + 9, oy + 50, w - 18, 26), border_radius=6)
    pygame.draw.rect(s, (30, 45, 70), (ox + 9, oy + 77, w - 18, 14), border_radius=5)
    pygame.draw.line(s, (120, 170, 220), (ox + 12, oy + 34), (ox + 24, oy + 34), 2)
    pygame.draw.ellipse(s, dark, (ox - 5, oy + 38, 9, 12))
    pygame.draw.ellipse(s, dark, (ox + w - 4, oy + 38, 9, 12))
    pygame.draw.rect(s, (255, 245, 170), (ox + 5, oy + 2, 14, 8), border_radius=4)
    pygame.draw.rect(s, (255, 245, 170), (ox + w - 19, oy + 2, 14, 8), border_radius=4)
    pygame.draw.rect(s, (220, 20, 30), (ox + 5, oy + h - 9, 14, 7), border_radius=3)
    pygame.draw.rect(s, (220, 20, 30), (ox + w - 19, oy + h - 9, 14, 7), border_radius=3)
    return s


def make_truck(color, w=70, h=180):
    s = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
    ox, oy = 8, 8
    pygame.draw.ellipse(s, (0, 0, 0, 90), (ox - 2, oy + 6, w + 4, h))
    pygame.draw.rect(s, (40, 40, 48), (ox, oy, w, 52), border_radius=12)
    pygame.draw.rect(s, color, (ox + 3, oy + 3, w - 6, 46), border_radius=10)
    pygame.draw.rect(s, (30, 45, 70), (ox + 8, oy + 14, w - 16, 16), border_radius=5)
    pygame.draw.rect(s, (90, 90, 100), (ox + 1, oy + 54, w - 2, h - 54), border_radius=6)
    pygame.draw.rect(s, (225, 228, 235), (ox + 4, oy + 56, w - 8, h - 62), border_radius=5)
    for i in range(4):
        y = oy + 72 + i * 28
        pygame.draw.line(s, (180, 184, 195), (ox + 8, y), (ox + w - 8, y), 2)
    pygame.draw.rect(s, color, (ox + 4, oy + 56, w - 8, 10))
    pygame.draw.rect(s, (255, 245, 170), (ox + 6, oy + 2, 14, 7), border_radius=3)
    pygame.draw.rect(s, (255, 245, 170), (ox + w - 20, oy + 2, 14, 7), border_radius=3)
    pygame.draw.rect(s, (220, 20, 30), (ox + 6, oy + h - 8, 16, 6), border_radius=3)
    pygame.draw.rect(s, (220, 20, 30), (ox + w - 22, oy + h - 8, 16, 6), border_radius=3)
    return s


def make_bike(body, accent, fw, extra):
    s = pygame.Surface((80, 140), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 100), (22, 14, 42, 118))
    pygame.draw.rect(s, (15, 15, 18), (33, 6, 14, 38), border_radius=7)
    pygame.draw.rect(s, (15, 15, 18), (32, 96, 16, 40), border_radius=8)
    pygame.draw.rect(s, (60, 60, 66), (37, 10, 6, 30), border_radius=3)
    if "wings" in extra:
        for sgn in (-1, 1):
            pygame.draw.polygon(s, accent, [(40 + sgn * fw, 48), (40 + sgn * (fw + 11), 58), (40 + sgn * fw, 64)])
    pygame.draw.polygon(s, tint(body, -35), [(40, 22), (40 + fw, 44), (42 + fw, 100), (40, 118), (38 - fw, 100), (40 - fw, 44)])
    pygame.draw.polygon(s, tint(body, 25), [(40, 28), (40 + fw - 4, 46), (40 + fw - 3, 70), (40, 74), (43 - fw, 70), (44 - fw, 46)])
    if "stripe" in extra:
        pygame.draw.rect(s, accent, (37, 30, 3, 80))
        pygame.draw.rect(s, accent, (42, 30, 3, 80))
    else:
        pygame.draw.rect(s, (235, 235, 240), (38, 30, 4, 80), border_radius=2)
    pygame.draw.line(s, (30, 30, 35), (14, 46), (66, 46), 5)
    pygame.draw.circle(s, (10, 10, 12), (14, 46), 4)
    pygame.draw.circle(s, (10, 10, 12), (66, 46), 4)
    jacket = tint(accent, -20)
    pygame.draw.line(s, jacket, (28, 66), (16, 47), 8)
    pygame.draw.line(s, jacket, (52, 66), (64, 47), 8)
    pygame.draw.ellipse(s, jacket, (24, 58, 32, 44))
    pygame.draw.ellipse(s, tint(accent, 35), (28, 62, 24, 20))
    pygame.draw.circle(s, (240, 240, 245), (40, 64), 11)
    pygame.draw.circle(s, (20, 20, 25), (40, 60), 7)
    pygame.draw.arc(s, body, (30, 54, 20, 20), 0.3, 2.8, 3)
    pygame.draw.circle(s, (255, 250, 190), (40, 14), 5)
    if "twin" in extra:
        pygame.draw.rect(s, (255, 120, 30), (30, 126, 7, 6), border_radius=2)
        pygame.draw.rect(s, (255, 120, 30), (43, 126, 7, 6), border_radius=2)
    pygame.draw.rect(s, (255, 30, 40), (35, 128, 10, 5), border_radius=2)
    return s


_bike_cache = {}


def get_bike_img(idx, cidx):
    key = (idx, cidx)
    if key not in _bike_cache:
        b = BIKES[idx]
        body, accent = PALETTES[cidx % len(PALETTES)]
        _bike_cache[key] = make_bike(body, accent, b["fw"], b["extra"])
    return _bike_cache[key]


CAR_COLORS = [(230, 60, 60), (60, 140, 235), (245, 190, 40), (70, 200, 120),
              (190, 90, 220), (240, 240, 245), (255, 130, 40), (40, 200, 210)]
CARS = [make_car(c) for c in CAR_COLORS]
CARS_ONC = [pygame.transform.rotate(c, 180) for c in CARS]
TRUCKS = [make_truck(c) for c in [(200, 50, 50), (50, 110, 200), (230, 160, 30)]]
TRUCKS_ONC = [pygame.transform.rotate(t, 180) for t in TRUCKS]


# ====================================================================== WORLD
class Scenery:
    def __init__(self, season):
        self.season = season
        self.items = []
        for side in (0, 1):
            for _ in range(14):
                self.items.append(self.new(side, random.randint(-60, H)))

    def new(self, side, y):
        x = random.randint(20, ROAD_X - 50) if side == 0 else random.randint(ROAD_R + 50, W - 20)
        return [side, x, y, random.randint(18, 34), random.randint(0, 2)]

    def update(self, speed):
        for it in self.items:
            it[2] += speed
            if it[2] > H + 60:
                it[:] = self.new(it[0], -random.randint(40, 120))

    def draw(self, surf):
        S = SEASONS[self.season]
        for _, x, y, r, k in self.items:
            pygame.draw.ellipse(surf, (10, 40, 15) if self.season != "winter" else (170, 180, 200),
                                (x - r + 8, y + 4, r * 2, r))
            pygame.draw.rect(surf, (80, 52, 30), (x - 4, y - 4, 8, 16))
            col = S["trees"][k]
            if self.season == "winter":
                for j in range(3):
                    w = r * (1.5 - 0.35 * j)
                    yy = y - 10 - j * r * 0.5
                    pygame.draw.polygon(surf, col, [(x - w, yy + r * .5), (x + w, yy + r * .5), (x, yy - r * .6)])
                    pygame.draw.polygon(surf, (250, 252, 255), [(x, yy - r * .6), (x - w * .5, yy - r * .6 + r * .55),
                                                                (x + w * .5, yy - r * .6 + r * .55)])
            else:
                pygame.draw.circle(surf, col, (x, y - 6), r)
                pygame.draw.circle(surf, tint(col, 35), (x - r // 4, y - 6 - r // 4), r // 2)


class Weather:
    def __init__(self, season):
        self.season = season
        self.flash = 0
        self.items = []
        n = {"rain": 170, "winter": 120, "autumn": 34}.get(season, 0)
        for _ in range(n):
            self.items.append(self._new(True))

    def _new(self, anywhere=False):
        x = random.randint(-40, W + 40)
        y = random.randint(-60, H) if anywhere else random.randint(-80, -5)
        if self.season == "rain":
            return [x, y, random.uniform(20, 28), random.randint(12, 22)]
        if self.season == "winter":
            return [x, y, random.uniform(1.5, 3.5), random.uniform(0, 6.28), random.randint(2, 4)]
        return [x, y, random.uniform(1.5, 3.2), random.uniform(0, 6.28),
                random.choice([(210, 100, 30), (190, 50, 30), (230, 170, 40)])]

    def update(self, speed):
        s = self.season
        for it in self.items:
            if s == "rain":
                it[1] += it[2]
                it[0] -= 2
            elif s == "winter":
                it[3] += 0.05
                it[0] += math.sin(it[3]) * 0.8
                it[1] += it[2] + speed * 0.15
            else:
                it[3] += 0.07
                it[0] += math.sin(it[3]) * 1.6
                it[1] += it[2] + speed * 0.2
            if it[1] > H + 20 or it[0] < -60 or it[0] > W + 60:
                it[:] = self._new()
        if s == "rain":
            if self.flash > 0:
                self.flash -= 1
            elif random.random() < 0.0025:
                self.flash = 10

    def draw(self, surf):
        s = self.season
        for it in self.items:
            x, y = int(it[0]), int(it[1])
            if s == "rain":
                pygame.draw.line(surf, (160, 180, 225), (x, y), (x + 2, y - it[3]), 1)
            elif s == "winter":
                pygame.draw.circle(surf, (255, 255, 255), (x, y), it[4] // 2 + 1)
            elif s == "autumn":
                pygame.draw.ellipse(surf, it[4], (x, y, 8, 4))
        if self.flash > 0:
            overlay(surf, (220, 230, 255, self.flash * 14))


def draw_road(surf, off, S):
    g0, g1 = S["grass"]
    for i in range(-1, H // 70 + 2):
        y = int(i * 70 + off % 70)
        pygame.draw.rect(surf, g0 if i % 2 == 0 else g1, (0, y, W, 70))
    for i in range(-1, H // 40 + 2):
        y = int(i * 40 + off % 40)
        c = (225, 40, 40) if i % 2 == 0 else (240, 240, 240)
        pygame.draw.rect(surf, c, (ROAD_X - 14, y, 14, 40))
        pygame.draw.rect(surf, c, (ROAD_R, y, 14, 40))
    pygame.draw.rect(surf, S["road"], (ROAD_X, 0, ROAD_W, H))
    band = tint(S["road"], 5)
    for i in range(0, ROAD_W, 20):
        pygame.draw.rect(surf, band, (ROAD_X + i, 0, 10, H))
    pygame.draw.rect(surf, (240, 240, 240), (ROAD_X + 4, 0, 4, H))
    pygame.draw.rect(surf, (240, 240, 240), (ROAD_R - 8, 0, 4, H))
    cx = ROAD_X + LANE_W * 2
    pygame.draw.rect(surf, (245, 200, 30), (cx - 5, 0, 3, H))
    pygame.draw.rect(surf, (245, 200, 30), (cx + 2, 0, 3, H))
    for lane in (1, 3):
        x = ROAD_X + LANE_W * lane
        for i in range(-1, H // 100 + 2):
            y = int(i * 100 + off % 100)
            pygame.draw.rect(surf, (225, 225, 225), (x - 2, y, 4, 50))


class Backdrop:
    """Animated season road used behind all menus."""

    def __init__(self):
        self.off = 0
        self.t = 0
        self._build()

    def _build(self):
        self.season = data["season"]
        self.scen = Scenery(self.season)
        self.weather = Weather(self.season)

    def draw(self, surf, dim=110):
        if self.season != data["season"]:
            self._build()
        S = SEASONS[self.season]
        self.off += 6
        self.t += 1
        self.scen.update(6)
        self.weather.update(6)
        draw_road(surf, self.off, S)
        self.scen.draw(surf)
        overlay(surf, S["tint"])
        self.weather.draw(surf)
        overlay(surf, (0, 0, 20, dim))


particles = []


def add_particles(x, y, n, color, spd=4, life=30, size=4, vy=0):
    for _ in range(n):
        a = random.uniform(0, math.tau)
        v = random.uniform(0.3, 1) * spd
        particles.append([x, y, math.cos(a) * v, math.sin(a) * v + vy,
                          random.randint(life // 2, life), life, color, random.randint(2, size)])


def update_particles(surf, scroll=0):
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3] + scroll
        p[4] -= 1
        if p[4] <= 0:
            particles.remove(p)
            continue
        k = p[4] / p[5]
        c = (int(p[6][0] * k), int(p[6][1] * k), int(p[6][2] * k))
        pygame.draw.circle(surf, c, (int(p[0]), int(p[1])), max(1, int(p[7] * k)))


# ====================================================================== INTRO
def intro():
    stars = [[random.randint(0, W), random.randint(0, H), random.uniform(0.3, 2)] for _ in range(110)]
    bg = vgradient(W, H, (4, 6, 20), (14, 10, 40))
    t0 = pygame.time.get_ticks()
    TOTAL = 7.5
    name = "UA SOFTWARE TECHNOLOGY"
    ring_pts = 90
    bike = pygame.transform.rotate(get_bike_img(0, 0), -90)
    bike = pygame.transform.smoothscale(bike, (110, 63))
    jingle = False
    while True:
        events = pygame.event.get()
        quit_check(events)
        for e in events:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        t = (pygame.time.get_ticks() - t0) / 1000
        if t > TOTAL:
            return
        if t > 1.0 and not jingle:
            jingle = True
            sfx("intro")
        screen.blit(bg, (0, 0))
        for s in stars:
            s[0] -= s[2] * 2
            if s[0] < 0:
                s[0], s[1] = W, random.randint(0, H)
            b = int(80 + 120 * (s[2] / 2))
            pygame.draw.circle(screen, (b, b, min(255, b + 40)), (int(s[0]), int(s[1])), 1 if s[2] < 1.2 else 2)
        cx, cy = W // 2, 250
        prog = min(1, t / 1.8)
        n = int(ring_pts * prog)
        for i in range(n):
            a = -math.pi / 2 + i / ring_pts * math.tau
            pygame.draw.circle(screen, (0, 200 + int(55 * i / ring_pts), 255),
                               (int(cx + math.cos(a) * 90), int(cy + math.sin(a) * 90)), 5)
        if prog > 0.05:
            glow(screen, (cx, cy), 160, (0, 90, 190), min(1, prog))
        if t > 1.0:
            a = min(1, (t - 1.0) / 0.8)
            sc = 0.6 + 0.4 * a
            img = F_HUGE.render("UA", True, (255, 255, 255))
            img = pygame.transform.smoothscale(img, (int(img.get_width() * sc * 1.3), int(img.get_height() * sc * 1.3)))
            img.set_alpha(int(255 * a))
            screen.blit(img, img.get_rect(center=(cx, cy)))
        if t > 1.8:
            a = t * 3
            glow(screen, (int(cx + math.cos(a) * 90), int(cy + math.sin(a) * 90)), 30, (255, 255, 255), 1)
        if t > 2.0:
            k = int((t - 2.0) / 1.4 * len(name))
            s = name[:min(k, len(name))]
            if s:
                glow(screen, (cx, 430), 150, (0, 70, 140), 0.6)
                text(screen, s, F_BIG if len(s) < 40 else F_MID, (255, 255, 255), (cx, 430))
        if t > 3.8:
            text(screen, "Created By", F_SM, (150, 170, 210), (cx, 490), alpha=min(255, int((t - 3.8) / 0.8 * 255)))
        if t > 4.3:
            a = min(255, int((t - 4.3) / 0.9 * 255))
            glow(screen, (cx, 535), 140, (200, 120, 0), 0.5 * a / 255)
            text(screen, "Usman Arshad", F_BIG, (255, 205, 80), (cx, 535), alpha=a)
        if t > 4.8:
            k = (t - 4.8) / (TOTAL - 4.8)
            bx = -150 + k * (W + 300)
            pygame.draw.rect(screen, (30, 32, 40), (0, 628, W, 6))
            for i in range(0, W, 80):
                pygame.draw.rect(screen, (70, 72, 85), ((i - int(t * 400)) % (W + 80) - 40, 650, 40, 4))
            glow(screen, (int(bx + 130), 612), 90, (255, 235, 150), 0.9)
            screen.blit(bike, (bx, 580))
            if random.random() < 0.7:
                add_particles(bx + 4, 620, 1, (255, 150, 40), 3, 18, 3)
        update_particles(screen)
        bw = 360
        pygame.draw.rect(screen, (30, 34, 55), (cx - bw // 2, 672, bw, 8), border_radius=4)
        pygame.draw.rect(screen, (0, 200, 255), (cx - bw // 2, 672, int(bw * t / TOTAL), 8), border_radius=4)
        fade = 0
        if t < 0.6:
            fade = int(255 * (1 - t / 0.6))
        elif t > TOTAL - 0.6:
            fade = int(255 * (t - (TOTAL - 0.6)) / 0.6)
        if fade > 0:
            f = pygame.Surface((W, H))
            f.set_alpha(fade)
            screen.blit(f, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


# ====================================================================== SCREENS
def main_screen(bd):
    t = 0
    b_set = Button((W // 2 - 170, 330, 340, 70), "SETTINGS", "gear", (60, 90, 160), "settings")
    b_play = Button((W // 2 - 190, 420, 380, 90), "PLAY", "play", (220, 50, 60), "play", F_BIG)
    buttons, focus = [b_set, b_play], 1
    while True:
        events = pygame.event.get()
        quit_check(events)
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        clicked, focus = ui_step(buttons, focus, events)
        t += 1
        bd.draw(screen, 120)
        pul = 1 + math.sin(t * 0.08) * 0.04
        title = F_HUGE.render("MOTO RIDER", True, (255, 255, 255))
        title = pygame.transform.smoothscale(title, (int(title.get_width() * pul), int(title.get_height() * pul)))
        glow(screen, (W // 2, 130), 260, (200, 30, 40), 0.7)
        screen.blit(title, title.get_rect(center=(W // 2, 120)))
        text(screen, "GO", F_HUGE, (255, 200, 40), (W // 2, 195))
        coin_hud(screen)
        for i, b in enumerate(buttons):
            b.draw(screen, i == focus)
        bx = W // 2 + math.sin(t * 0.03) * 110
        img = get_bike_img(data["bike"], data["colors"][data["bike"]])
        rot = pygame.transform.rotate(img, -math.cos(t * 0.03) * 12)
        glow(screen, (int(bx), 530), 70, (255, 240, 170), 0.5)
        screen.blit(rot, rot.get_rect(center=(int(bx), 605)))
        text(screen, "UA Software Technology  |  Created By Usman Arshad", F_XS, (170, 185, 220), (W // 2, 686))
        pygame.display.flip()
        clock.tick(FPS)
        if clicked:
            sfx("click")
            return clicked.id


def settings_screen(bd):
    listening = None
    b_sfx = Button((W // 2 - 190, 108, 380, 50), "", "sound", (50, 110, 210), "sfx", F_SM)
    b_mus = Button((W // 2 - 190, 168, 380, 50), "", "music", (50, 110, 210), "music", F_SM)
    key_btns = [Button((W // 2 + 20, 268 + i * 50, 210, 42), "", None, (70, 80, 120), act, F_SM)
                for i, (act, _) in enumerate(KEY_LABELS)]
    b_reset = Button((W // 2 - 290, 590, 270, 56), "RESET KEYS", None, (160, 90, 40), "reset", F_SM)
    b_back = Button((W // 2 + 20, 590, 270, 56), "BACK", "back", (60, 90, 160), "back", F_SM)
    buttons = [b_sfx, b_mus] + key_btns + [b_reset, b_back]
    focus = 0
    while True:
        events = pygame.event.get()
        quit_check(events)
        if listening:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        listening = None
                    elif e.key == pygame.K_p:
                        sfx("error")
                    else:
                        old = data["keys"][listening]
                        for a, k in data["keys"].items():
                            if a != listening and k == e.key:
                                data["keys"][a] = old
                        data["keys"][listening] = e.key
                        listening = None
                        save_data()
                        sfx("click")
            clicked, focus = ui_step(buttons, focus, [])
        else:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    return
            clicked, focus = ui_step(buttons, focus, events)
        b_sfx.label = "SOUND EFFECTS:  " + ("ON" if data["sfx"] else "OFF")
        b_sfx.color = (40, 160, 90) if data["sfx"] else (160, 60, 60)
        b_mus.label = "MUSIC:  " + ("ON" if data["music"] else "OFF")
        b_mus.color = (40, 160, 90) if data["music"] else (160, 60, 60)
        for kb in key_btns:
            if listening == kb.id:
                kb.label, kb.color = "Press a key...", (200, 140, 30)
            else:
                kb.label, kb.color = pygame.key.name(data["keys"][kb.id]).upper(), (70, 80, 120)

        bd.draw(screen, 150)
        panel = pygame.Surface((760, 640), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 12, 28, 215), (0, 0, 760, 640), border_radius=24)
        pygame.draw.rect(panel, (90, 120, 200, 255), (0, 0, 760, 640), 2, border_radius=24)
        screen.blit(panel, (70, 30))
        text(screen, "SETTINGS", F_BIG, (255, 255, 255), (W // 2, 70))
        text(screen, "CONTROLS", F_SM, (255, 205, 80), (W // 2, 245))
        for i, (_, lab) in enumerate(KEY_LABELS):
            text(screen, lab, F_SM, (225, 230, 245), (W // 2 - 230, 268 + i * 50 + 10), center=False)
        text(screen, "Click a key box, then press the new key.  P = Pause,  ESC = Cancel/Back",
             F_XS, (170, 185, 220), (W // 2, 545))
        coin_hud(screen)
        for i, b in enumerate(buttons):
            b.draw(screen, i == focus)
        pygame.display.flip()
        clock.tick(FPS)
        if clicked and not listening:
            sfx("click")
            if clicked.id == "sfx":
                data["sfx"] = not data["sfx"]
                save_data()
                sfx("click")
            elif clicked.id == "music":
                data["music"] = not data["music"]
                save_data()
                play_music("menu")
            elif clicked.id == "reset":
                data["keys"] = dict(KEYS_DEFAULT)
                save_data()
            elif clicked.id == "back":
                return
            else:
                listening = clicked.id


def mode_screen(bd):
    buttons = []
    for i, k in enumerate(DIFF_KEYS):
        D = DIFFS[k]
        done = data["done"][k]
        sub = f"{D['desc']}   |   Level {min(MAX_LEVEL, done + 1)} / {MAX_LEVEL}"
        buttons.append(Button((W // 2 - 260, 175 + i * 100, 520, 86), D["name"], "play", D["color"], k, F_MID, sub))
    buttons.append(Button((W // 2 - 260, 490, 250, 70), "GARAGE", "bike", (60, 90, 160), "garage", F_SM))
    buttons.append(Button((W // 2 + 10, 490, 250, 70), "SEASON", "leaf", (60, 130, 110), "season", F_SM))
    buttons.append(Button((W // 2 - 110, 590, 220, 56), "BACK", "back", (90, 90, 110), "back", F_SM))
    focus = 1
    while True:
        events = pygame.event.get()
        quit_check(events)
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "back"
        clicked, focus = ui_step(buttons, focus, events)
        bd.draw(screen, 130)
        text(screen, "SELECT MODE", F_BIG, (255, 255, 255), (W // 2, 70))
        text(screen, f"Season: {SEASONS[data['season']]['name']}   |   Bike: {BIKES[data['bike']]['name']}",
             F_SM, (255, 220, 140), (W // 2, 128))
        coin_hud(screen)
        for i, b in enumerate(buttons):
            b.draw(screen, i == focus)
        pygame.display.flip()
        clock.tick(FPS)
        if clicked:
            sfx("click")
            return clicked.id


def level_screen(bd, diff):
    D = DIFFS[diff]
    done = data["done"][diff]
    unlocked = min(MAX_LEVEL, done + 1)
    lvl = unlocked
    b_l = Button((W // 2 - 200, 290, 80, 80), "", "left", (60, 90, 160), "l")
    b_r = Button((W // 2 + 120, 290, 80, 80), "", "right", (60, 90, 160), "r")
    b_m = Button((W // 2 - 310, 305, 90, 50), "-10", None, (60, 90, 160), "m10", F_SM)
    b_p = Button((W // 2 + 220, 305, 90, 50), "+10", None, (60, 90, 160), "p10", F_SM)
    b_go = Button((W // 2 - 170, 480, 340, 80), "START", "play", D["color"], "go", F_MID)
    b_bk = Button((W // 2 - 110, 590, 220, 56), "BACK", "back", (90, 90, 110), "back", F_SM)
    buttons = [b_go, b_l, b_r, b_m, b_p, b_bk]
    focus = 0
    while True:
        events = pygame.event.get()
        quit_check(events)
        step = 0
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_LEFT:
                    step = -1
                if e.key == pygame.K_RIGHT:
                    step = 1
        clicked, focus = ui_step(buttons, focus, events)
        if clicked:
            sfx("click")
            if clicked.id == "go":
                return lvl
            if clicked.id == "back":
                return None
            step = {"l": -1, "r": 1, "m10": -10, "p10": 10}.get(clicked.id, 0)
        if step:
            lvl = max(1, min(unlocked, lvl + step))
        bd.draw(screen, 140)
        text(screen, D["name"], F_BIG, D["color"], (W // 2, 70))
        text(screen, "SELECT LEVEL", F_SM, (200, 210, 240), (W // 2, 118))
        text(screen, "LEVEL", F_SM, (170, 185, 220), (W // 2, 270))
        glow(screen, (W // 2, 330), 120, tuple(c // 2 for c in D["color"]), 0.8)
        text(screen, str(lvl), F_HUGE, (255, 255, 255), (W // 2, 332))
        text(screen, f"Distance: {level_len(lvl) // 10} m", F_SM, (225, 230, 245), (W // 2, 395))
        if lvl <= done:
            text(screen, f"Cleared!  Replay reward: +{max(2, level_reward(lvl) // 4)} coins", F_SM, (140, 255, 170), (W // 2, 425))
        else:
            text(screen, f"Reward: +{level_reward(lvl)} coins", F_SM, (255, 220, 100), (W // 2, 425))
        bw = 420
        pygame.draw.rect(screen, (25, 30, 50), (W // 2 - bw // 2, 455, bw, 10), border_radius=5)
        pygame.draw.rect(screen, D["color"], (W // 2 - bw // 2, 455, int(bw * done / MAX_LEVEL), 10), border_radius=5)
        text(screen, f"Progress {done} / {MAX_LEVEL}", F_XS, (170, 185, 220), (W // 2, 472), shadow=False)
        coin_hud(screen)
        for i, b in enumerate(buttons):
            b.draw(screen, i == focus)
        pygame.display.flip()
        clock.tick(FPS)


def draw_stat(surf, label, val, vmax, x, y):
    text(surf, label, F_XS, (200, 210, 235), (x, y), center=False, shadow=False)
    pygame.draw.rect(surf, (25, 30, 50), (x + 100, y + 2, 200, 14), border_radius=7)
    pygame.draw.rect(surf, (80, 200, 255), (x + 100, y + 2, int(200 * max(0.05, min(1, val / vmax))), 14), border_radius=7)


def garage_screen(bd):
    idx = data["bike"]
    b_l = Button((70, 300, 80, 80), "", "left", (60, 90, 160), "l")
    b_r = Button((W - 150, 300, 80, 80), "", "right", (60, 90, 160), "r")
    b_act = Button((W // 2 - 190, 590, 380, 66), "", None, (230, 150, 30), "act", F_MID)
    b_bk = Button((20, 20, 150, 50), "BACK", "back", (90, 90, 110), "back", F_SM)
    buttons = [b_act, b_l, b_r, b_bk]
    focus = 0
    msg, msg_t, t = "", 0, 0
    while True:
        events = pygame.event.get()
        quit_check(events)
        step = 0
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return
                if e.key == pygame.K_LEFT:
                    step = -1
                if e.key == pygame.K_RIGHT:
                    step = 1
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for ci in range(len(PALETTES)):
                    sx = W // 2 - 150 + ci * 60
                    if (e.pos[0] - sx) ** 2 + (e.pos[1] - 445) ** 2 < 24 ** 2:
                        data["colors"][idx] = ci
                        save_data()
                        sfx("click")
        clicked, focus = ui_step(buttons, focus, events)
        bike = BIKES[idx]
        owned = idx in data["owned"]
        if clicked:
            if clicked.id == "back":
                sfx("click")
                return
            if clicked.id in ("l", "r"):
                step = -1 if clicked.id == "l" else 1
                sfx("click")
            elif clicked.id == "act":
                if owned:
                    data["bike"] = idx
                    save_data()
                    sfx("click")
                elif data["coins"] >= bike["price"]:
                    data["coins"] -= bike["price"]
                    data["owned"].append(idx)
                    data["bike"] = idx
                    save_data()
                    sfx("buy")
                    msg, msg_t = f"{bike['name']} unlocked!", 120
                else:
                    sfx("error")
                    msg, msg_t = f"Need {bike['price'] - data['coins']} more coins", 120
        if step:
            idx = (idx + step) % len(BIKES)
            bike = BIKES[idx]
            owned = idx in data["owned"]
        if owned and data["bike"] == idx:
            b_act.label, b_act.color, b_act.icon, b_act.enabled = "SELECTED", (40, 150, 90), "check", False
        elif owned:
            b_act.label, b_act.color, b_act.icon, b_act.enabled = "SELECT", (50, 110, 210), None, True
        else:
            b_act.label, b_act.color, b_act.icon, b_act.enabled = f"BUY   {bike['price']}", (230, 150, 30), "coin", True

        t += 1
        bd.draw(screen, 170)
        text(screen, "GARAGE", F_BIG, (255, 255, 255), (W // 2, 45))
        text(screen, bike["name"].upper(), F_MID, (255, 220, 120), (W // 2, 100))
        glow(screen, (W // 2, 300), 170, (40, 90, 170), 0.8)
        pygame.draw.ellipse(screen, (20, 24, 40), (W // 2 - 110, 372, 220, 40))
        pygame.draw.ellipse(screen, (90, 130, 220), (W // 2 - 110, 372, 220, 40), 3)
        img = get_bike_img(idx, data["colors"][idx])
        big = pygame.transform.smoothscale(img, (144, 252))
        screen.blit(big, big.get_rect(center=(W // 2, 262 + int(math.sin(t * 0.05) * 4))))
        if not owned:
            draw_icon(screen, "lock", (W // 2, 180), 44, (255, 255, 255))
        for ci, (body, acc) in enumerate(PALETTES):
            sx = W // 2 - 150 + ci * 60
            pygame.draw.circle(screen, (15, 18, 34), (sx, 445), 25)
            pygame.draw.circle(screen, body, (sx, 445), 20)
            pygame.draw.circle(screen, acc, (sx, 445), 9)
            if ci == data["colors"][idx]:
                pygame.draw.circle(screen, (255, 255, 255), (sx, 445), 25, 3)
        sx0 = W // 2 - 190
        draw_stat(screen, "SPEED", bike["speed"] - 0.95, 0.2, sx0, 488)
        draw_stat(screen, "HANDLING", bike["handling"] - 0.8, 0.7, sx0, 515)
        draw_stat(screen, "NITRO", bike["nitro"] - 0.8, 1.1, sx0, 542)
        text(screen, f"{idx + 1} / {len(BIKES)}", F_XS, (170, 185, 220), (W // 2, 575), shadow=False)
        coin_hud(screen)
        for i, b in enumerate(buttons):
            b.draw(screen, i == focus)
        if msg_t > 0:
            msg_t -= 1
            text(screen, msg, F_SM, (255, 240, 160), (W // 2, 672), alpha=min(255, msg_t * 8))
        pygame.display.flip()
        clock.tick(FPS)


def draw_season_card(surf, r, key, selected, t):
    S = SEASONS[key]
    gh = int(r.h * 0.62)
    surf.set_clip(r)
    surf.blit(vgradient(r.w, gh, S["sky"][0], S["sky"][1]), (r.x, r.y))
    pygame.draw.rect(surf, S["grass"][0], (r.x, r.y + gh, r.w, r.h - gh))
    pygame.draw.polygon(surf, S["road"], [(r.centerx - 18, r.y + gh), (r.centerx + 18, r.y + gh),
                                          (r.centerx + 70, r.bottom), (r.centerx - 70, r.bottom)])
    for tx in (r.x + 32, r.right - 32):
        pygame.draw.rect(surf, (80, 52, 30), (tx - 3, r.y + gh + 10, 6, 14))
        if key == "winter":
            pygame.draw.polygon(surf, S["trees"][0], [(tx - 18, r.y + gh + 14), (tx + 18, r.y + gh + 14), (tx, r.y + gh - 34)])
            pygame.draw.polygon(surf, (250, 252, 255), [(tx, r.y + gh - 34), (tx - 9, r.y + gh - 14), (tx + 9, r.y + gh - 14)])
        else:
            pygame.draw.circle(surf, S["trees"][0], (tx, r.y + gh - 2), 22)
    for j in range(14):
        x = r.x + (j * 37 + int(t * (1 + j % 3))) % r.w
        y = r.y + (j * 53 + int(t * (2 + j % 2))) % gh
        if key == "winter":
            pygame.draw.circle(surf, (255, 255, 255), (x, y), 2)
        elif key == "rain":
            pygame.draw.line(surf, (170, 190, 235), (x, y), (x + 2, y - 10), 1)
        elif key == "autumn":
            pygame.draw.ellipse(surf, S["trees"][j % 3], (x, y, 8, 4))
    draw_icon(surf, S["icon"], (r.centerx, r.y + 70), 80)
    surf.set_clip(None)
    pygame.draw.rect(surf, (255, 205, 50) if selected else (20, 24, 40), r, 4 if selected else 2)
    text(surf, S["name"], F_MID, (255, 255, 255), (r.centerx, r.bottom - 54))
    text(surf, "SELECTED" if selected else "Tap to select", F_XS,
         (255, 220, 100) if selected else (225, 230, 245), (r.centerx, r.bottom - 22), shadow=False)


def season_screen(bd):
    cards = [pygame.Rect(40 + i * 210, 160, 190, 330) for i in range(4)]
    b_bk = Button((W // 2 - 110, 590, 220, 56), "BACK", "back", (90, 90, 110), "back", F_SM)
    t = 0
    while True:
        events = pygame.event.get()
        quit_check(events)
        cur = SEASON_KEYS.index(data["season"])
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    sfx("click")
                    return
                if e.key == pygame.K_LEFT:
                    data["season"] = SEASON_KEYS[(cur - 1) % 4]
                    save_data()
                    sfx("click")
                if e.key == pygame.K_RIGHT:
                    data["season"] = SEASON_KEYS[(cur + 1) % 4]
                    save_data()
                    sfx("click")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(cards):
                    if r.collidepoint(e.pos):
                        data["season"] = SEASON_KEYS[i]
                        save_data()
                        sfx("click")
        clicked, _ = ui_step([b_bk], 0, events)
        if clicked:
            sfx("click")
            return
        t += 1
        bd.draw(screen, 150)
        text(screen, "SELECT SEASON", F_BIG, (255, 255, 255), (W // 2, 70))
        text(screen, "Winter & Rain are slippery - be careful!", F_SM, (255, 220, 140), (W // 2, 120))
        for i, r in enumerate(cards):
            draw_season_card(screen, r, SEASON_KEYS[i], SEASON_KEYS[i] == data["season"], t)
        coin_hud(screen)
        b_bk.draw(screen, True)
        pygame.display.flip()
        clock.tick(FPS)


# ====================================================================== GAME
def play(diff, level):
    D = DIFFS[diff]
    S = SEASONS[data["season"]]
    bike = BIKES[data["bike"]]
    bimg = get_bike_img(data["bike"], data["colors"][data["bike"]])
    K = data["keys"]
    world = pygame.Surface((W, H))
    scen = Scenery(data["season"])
    weather = Weather(data["season"])
    traffic, coins, popups = [], [], []
    particles.clear()
    px, vx, py = lane_cx(3), 0.0, H - 150
    speed, distance, off = 8.0, 0.0, 0.0
    total = level_len(level)
    nitro_max = 100.0 * bike["nitro"]
    nitro = nitro_max
    score_bonus, coin_n = 0, 0
    spawn_t, coin_t, frame = 0, 0, 0
    crashed = won = False
    end_t, shake = 0, 0
    reward = 0
    endbtns, endfocus = [], 0
    paused, was_boost = False, False
    base_speed = (9 + min(level * 0.035, 5.0)) * D["mult"] * bike["speed"]
    grip = S["grip"]

    def make_end_buttons():
        if won:
            return [Button((200, 440, 240, 60), "CONTINUE", "play", (40, 160, 90), "levels", F_SM),
                    Button((460, 440, 240, 60), "MENU", "back", (90, 90, 110), "menu", F_SM)]
        return [Button((200, 440, 240, 60), "RETRY", "play", (210, 60, 60), "retry", F_SM),
                Button((460, 440, 240, 60), "MENU", "back", (90, 90, 110), "menu", F_SM)]

    while True:
        events = pygame.event.get()
        quit_check(events)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    save_data()
                    engine_stop()
                    return "menu"
                if e.key == pygame.K_p and not (crashed or won):
                    paused = not paused
                    engine_stop()
        if paused:
            text(screen, "PAUSED", F_BIG, (255, 255, 255), (W // 2, H // 2 - 20))
            text(screen, "Press P to resume   |   ESC for menu", F_SM, (220, 225, 240), (W // 2, H // 2 + 30))
            pygame.display.flip()
            clock.tick(15)
            continue

        keys = pygame.key.get_pressed()
        frame += 1
        score = int(distance / 12) + score_bonus

        if not crashed:
            ax = 0
            if not won:
                if keys[K["left"]]:
                    ax -= 1
                if keys[K["right"]]:
                    ax += 1
            vx += ax * 1.1 * bike["handling"]
            vx *= 0.82 + (1 - grip) * 0.12
            px = max(ROAD_X + 28, min(ROAD_R - 28, px + vx))
            target = base_speed
            boosting = False
            if won:
                target = 0.0
            else:
                if keys[K["accel"]]:
                    target += 4 * D["mult"]
                if keys[K["brake"]]:
                    target = 7.0
                if keys[K["nitro"]] and nitro > 0:
                    target += 8
                    nitro -= 0.9
                    boosting = True
                else:
                    nitro = min(nitro_max, nitro + 0.08)
            if boosting and not was_boost:
                sfx("nitro")
            was_boost = boosting
            speed += (target - speed) * (0.04 if not won else 0.05)
            distance += speed
            off += speed
            if boosting:
                add_particles(px - 6, py + 70, 2, (255, 140, 30), 3, 14, 4, vy=4)
                add_particles(px + 6, py + 70, 2, (255, 200, 60), 3, 14, 4, vy=4)

            remaining = total - distance
            if not won and remaining > 900:
                spawn_t -= 1
                if spawn_t <= 0:
                    spawn_t = max(14, int((60 - speed * 1.5) / D["dens"]) - int(level * 0.1)) + random.randint(0, 18)
                    lane = random.randrange(LANES)
                    onc = lane < 2
                    truck = random.random() < 0.18
                    hh = 180 if truck else 112
                    y = -hh - random.randint(0, 60)
                    if all(not (c["lane"] == lane and abs(c["y"] - y) < 280) for c in traffic):
                        img = random.choice((TRUCKS_ONC if onc else TRUCKS) if truck else (CARS_ONC if onc else CARS))
                        traffic.append({"lane": lane, "x": lane_cx(lane), "y": y, "v": random.uniform(3, 6.5),
                                        "onc": onc, "img": img, "near": False})
                coin_t -= 1
                if coin_t <= 0:
                    coin_t = random.randint(40, 90)
                    lane = random.randrange(LANES)
                    for k in range(random.randint(3, 6)):
                        coins.append([lane_cx(lane), -30 - k * 55, random.random() * 6])

            prect = pygame.Rect(0, 0, 24, 96)
            prect.center = (int(px), py + 10)
            for c in traffic[:]:
                dy = (speed + c["v"]) if c["onc"] else (speed - c["v"])
                c["y"] += dy
                if c["y"] > H + 220 or c["y"] < -600:
                    traffic.remove(c)
                    continue
                if won:
                    continue
                w_, h_ = c["img"].get_size()
                r = pygame.Rect(0, 0, w_ - 30, h_ - 36)
                r.center = (int(c["x"]), int(c["y"]))
                if prect.colliderect(r):
                    crashed, shake = True, 28
                    add_particles(px, py, 70, (255, 170, 40), 9, 50, 6)
                    add_particles(px, py, 40, (255, 70, 40), 7, 40, 7)
                    add_particles(px, py, 30, (200, 200, 200), 5, 60, 6)
                    sfx("crash")
                    engine_stop()
                    if score > data["best"]:
                        data["best"] = score
                    save_data()
                    break
                if not c["near"] and r.inflate(40, 0).colliderect(prect):
                    c["near"] = True
                    score_bonus += 25
                    sfx("close")
                    popups.append(["CLOSE CALL +25", px, py - 70, 60, (120, 230, 255)])
            for c in coins[:]:
                c[1] += speed
                c[2] += 0.15
                if c[1] > H + 40:
                    coins.remove(c)
                    continue
                if not crashed and abs(c[0] - px) < 30 and abs(c[1] - py) < 55:
                    coins.remove(c)
                    coin_n += 1
                    data["coins"] += 1
                    score_bonus += 10
                    sfx("coin")
                    add_particles(c[0], c[1], 10, (255, 220, 60), 4, 20, 3)

            if not crashed and not won and distance >= total:
                won = True
                first = level > data["done"][diff]
                reward = level_reward(level) if first else max(2, level_reward(level) // 4)
                if first:
                    data["done"][diff] = level
                data["coins"] += reward
                if score > data["best"]:
                    data["best"] = score
                save_data()
                sfx("win")
                for c in traffic:
                    c["v"] = 0
                for _ in range(8):
                    add_particles(random.randint(250, 650), random.randint(100, 300), 14,
                                  random.choice([(255, 80, 80), (80, 200, 255), (255, 220, 60), (120, 255, 140)]),
                                  6, 70, 6, vy=1)
        else:
            speed *= 0.93
            off += speed
            for c in traffic:
                c["y"] += (speed + c["v"]) if c["onc"] else (speed - c["v"])
        if crashed or won:
            end_t += 1

        scen.update(speed)
        weather.update(speed)
        if won and speed < 1.0:
            engine_stop()
        elif not crashed:
            br = 0 if speed < 10 else (1 if speed < 16 else 2)
            engine_set(br, 0.10 + 0.12 * min(1, speed / 25))

        # ----------------------------------------------------------- draw
        draw_road(world, off, S)
        scen.draw(world)
        glows = []
        fy = py - (total - distance) - 10
        if -40 < fy < H + 40:
            for i in range(ROAD_W // 20):
                for j in range(2):
                    col = (255, 255, 255) if (i + j) % 2 == 0 else (20, 20, 20)
                    pygame.draw.rect(world, col, (ROAD_X + i * 20, int(fy) + j * 15, 20, 15))
            text(world, "FINISH", F_MID, (255, 255, 255), (W // 2, int(fy) - 24))
        for c in coins:
            wdt = max(3, int(abs(math.cos(c[2])) * 24))
            pygame.draw.ellipse(world, (200, 140, 10), (c[0] - wdt // 2, c[1] - 12 + 3, wdt, 24))
            pygame.draw.ellipse(world, (255, 215, 50), (c[0] - wdt // 2, c[1] - 12, wdt, 24))
            if wdt > 10:
                pygame.draw.ellipse(world, (255, 245, 150), (c[0] - wdt // 4, c[1] - 6, wdt // 2, 12), 2)
            glows.append((c[0], c[1], 28, (120, 90, 0)))
        for c in traffic:
            world.blit(c["img"], c["img"].get_rect(center=(int(c["x"]), int(c["y"]))))
            hh = c["img"].get_height() // 2 - 12
            if c["onc"]:
                glows += [(c["x"] - 18, c["y"] + hh, 46, (150, 140, 80)), (c["x"] + 18, c["y"] + hh, 46, (150, 140, 80))]
            else:
                glows += [(c["x"] - 18, c["y"] + hh, 30, (150, 10, 15)), (c["x"] + 18, c["y"] + hh, 30, (150, 10, 15))]
        if not crashed:
            rot = pygame.transform.rotate(bimg, -vx * 2.2)
            world.blit(rot, rot.get_rect(center=(int(px), int(py))))
            glows.append((px, py - 90, 90, (200, 190, 120)))
            glows.append((px, py + 66, 24, (160, 10, 15)))
        if speed > 15:
            for _ in range(int((speed - 15) * 1.5)):
                x = random.randint(ROAD_X, ROAD_R)
                y = random.randint(0, H)
                pygame.draw.line(world, (150, 150, 165), (x, y), (x, y + int(speed * 2.5)), 1)
        update_particles(world, speed * 0.4)

        overlay(world, S["tint"])
        day = (math.sin(frame * 0.0025 - 1) + 1) / 2
        night = day * S["night"]
        overlay(world, (4, 8, 40, int(night * 255)))
        for gx, gy, gr, gc in glows:
            glow(world, (int(gx), int(gy)), gr, gc, 0.5 + night)
        weather.draw(world)

        ox = oy = 0
        if shake > 0:
            shake -= 1
            ox, oy = random.randint(-shake, shake), random.randint(-shake, shake)
        screen.blit(world, (ox, oy))

        # ----------------------------------------------------------- HUD
        hud = pygame.Surface((W, 76), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 130))
        screen.blit(hud, (0, 0))
        text(screen, f"LEVEL {level}", F_SM, D["color"], (24, 8), center=False)
        text(screen, f"{D['name']}   |   {S['name']}", F_XS, (170, 185, 220), (24, 34), center=False, shadow=False)
        text(screen, f"SCORE {score}", F_SM, (255, 255, 255), (24, 50), center=False)
        pct = max(0.0, min(1.0, distance / total))
        bw = 300
        pygame.draw.rect(screen, (30, 34, 50), (W // 2 - bw // 2, 16, bw, 14), border_radius=7)
        pygame.draw.rect(screen, D["color"], (W // 2 - bw // 2, 16, int(bw * pct), 14), border_radius=7)
        pygame.draw.circle(screen, (255, 255, 255), (W // 2 - bw // 2 + int(bw * pct), 23), 8)
        text(screen, f"{int(pct * 100)}%", F_XS, (255, 255, 255), (W // 2 + bw // 2 + 30, 23), shadow=False)
        draw_icon(screen, "coin", (W // 2 - 20, 56), 18)
        text(screen, str(coin_n), F_XS, (255, 220, 100), (W // 2 - 4, 48), center=False, shadow=False)
        kmh = int(speed * 9)
        text(screen, f"{kmh}", F_BIG, (255, 255, 255), (W - 110, 34))
        text(screen, "km/h", F_XS, (170, 185, 220), (W - 50, 44), shadow=False)
        pygame.draw.rect(screen, (30, 34, 50), (W - 330, 22, 120, 14), border_radius=7)
        pygame.draw.rect(screen, (255, 140, 30) if nitro > 15 else (200, 40, 40),
                         (W - 330, 22, int(120 * nitro / nitro_max), 14), border_radius=7)
        text(screen, "NITRO", F_XS, (170, 185, 220), (W - 330, 42), center=False, shadow=False)

        for p in popups[:]:
            p[3] -= 1
            p[2] -= 1
            if p[3] <= 0:
                popups.remove(p)
                continue
            text(screen, p[0], F_SM, p[4], (p[1], p[2]), alpha=min(255, p[3] * 8))

        if (crashed or won) and end_t > 60:
            if not endbtns:
                endbtns = make_end_buttons()
                endfocus = 0
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_r and crashed:
                        return "retry"
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and won:
                        save_data()
                        engine_stop()
                        return "levels"
            clicked, endfocus = ui_step(endbtns, endfocus, events)
            panel = pygame.Surface((560, 360), pygame.SRCALPHA)
            edge = (90, 230, 140) if won else (255, 70, 70)
            pygame.draw.rect(panel, (10, 14, 30, 230), (0, 0, 560, 360), border_radius=24)
            pygame.draw.rect(panel, edge, (0, 0, 560, 360), 3, border_radius=24)
            screen.blit(panel, (170, 170))
            if won:
                text(screen, "LEVEL COMPLETE!", F_BIG, (110, 255, 160), (W // 2, 225))
                if level >= MAX_LEVEL:
                    text(screen, "You finished all 200 levels!", F_SM, (255, 255, 255), (W // 2, 285))
                else:
                    text(screen, f"Level {level} cleared!  Level {level + 1} unlocked", F_SM, (255, 255, 255), (W // 2, 285))
                draw_icon(screen, "coin", (W // 2 - 110, 335), 34)
                text(screen, f"Reward: +{reward} coins", F_MID, (255, 220, 100), (W // 2 + 15, 335))
                text(screen, f"Collected on road: +{coin_n}   |   Score: {score}", F_SM, (200, 210, 235), (W // 2, 385))
                if level < MAX_LEVEL:
                    text(screen, "Open the next level yourself from the level screen", F_XS, (170, 185, 220), (W // 2, 412), shadow=False)
            else:
                text(screen, "CRASHED!", F_BIG, (255, 80, 80), (W // 2, 225))
                text(screen, f"Score: {score}", F_MID, (255, 255, 255), (W // 2, 290))
                text(screen, f"Coins collected: {coin_n}     Best: {max(data['best'], score)}", F_SM, (255, 220, 120), (W // 2, 340))
                text(screen, "Press R to retry", F_XS, (170, 185, 220), (W // 2, 385), shadow=False)
            for i, b in enumerate(endbtns):
                b.draw(screen, i == endfocus)
            if clicked:
                sfx("click")
                save_data()
                engine_stop()
                return clicked.id
        pygame.display.flip()
        clock.tick(FPS)


# ====================================================================== MAIN
def main():
    screen.fill((6, 8, 20))
    text(screen, "Loading...", F_MID, (200, 210, 240), (W // 2, H // 2))
    pygame.display.flip()
    pygame.event.pump()
    init_audio()
    build_audio()
    intro()
    bd = Backdrop()
    while True:
        play_music("menu")
        r = main_screen(bd)
        if r == "settings":
            settings_screen(bd)
            continue
        while True:  # Play -> mode screen
            r = mode_screen(bd)
            if r == "back":
                break
            if r == "garage":
                garage_screen(bd)
                continue
            if r == "season":
                season_screen(bd)
                continue
            diff = r
            while True:  # level select <-> game
                lvl = level_screen(bd, diff)
                if lvl is None:
                    break
                play_music("game")
                while True:
                    out = play(diff, lvl)
                    if out != "retry":
                        break
                engine_stop()
                play_music("menu")
                if out == "menu":
                    break


if __name__ == "__main__":
    main()
