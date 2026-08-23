# -*- coding: utf-8 -*-
"""
EVİM - Ev Eşya Envanteri Uygulaması (v2 - Genişletilmiş)
Sade Kivy ile yazılmıştır (KivyMD / kamera / QR / NFC gibi ek native
kütüphaneler KULLANILMAZ - APK derlemesinin kararlılığı için).
"""

import os
import csv
import json
import datetime

from kivy.app import App
from kivy.core.window import Window
Window.softinput_mode = "below_target"
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition, RiseInTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.lang import Builder
from kivy.utils import platform, get_color_from_hex
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line

import sqlite3

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

def get_db_path():
    if platform == "android":
        from android.storage import app_storage_path
        base = app_storage_path()
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "evim.db")


def get_settings_path():
    return os.path.join(os.path.dirname(get_db_path()), "ayarlar.txt")


def load_saved_font_scale(default_value):
    try:
        with open(get_settings_path(), "r", encoding="utf-8") as f:
            return float(f.read().strip())
    except Exception:
        return default_value


def save_font_scale(value):
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            f.write(str(value))
    except Exception:
        pass


def get_export_path():
    # Uygulamanın kendi özel (izin istemeyen) klasörüne yazar; Android'de
    # paylaşılan depolamaya yazmak ekstra çalışma zamanı izni gerektirdiği
    # için (ve APK derlemesini karmaşıklaştırmamak için) bilinçli olarak
    # özel depolama kullanılıyor.
    return os.path.dirname(get_db_path())


ROOM_TYPES = {
    "mutfak":   ("Mutfak",          "#FF7043", "MTF"),
    "yatak":    ("Yatak Odası",     "#5C6BC0", "YTK"),
    "salon":    ("Salon",           "#26A69A", "SLN"),
    "banyo":    ("Banyo",           "#29B6F6", "BNY"),
    "calisma":  ("Çalışma Odası",   "#8D6E63", "OFS"),
    "bilgisayar": ("Bilgisayar Odası", "#7E57C2", "BLG"),
    "cocuk":    ("Çocuk Odası",     "#EC407A", "ÇCK"),
    "garaj":    ("Garaj",           "#78909C", "GRJ"),
    "bahce":    ("Bahçe",           "#66BB6A", "BHÇ"),
    "depo":     ("Depo/Kiler",      "#8D8D57", "DPO"),
    "koridor":  ("Koridor",         "#607D8B", "KRD"),
    "misafir":  ("Misafir Odası",   "#26C6DA", "MSF"),
    "camasir":  ("Çamaşır Odası",   "#42A5F5", "ÇMR"),
    "balkon":   ("Balkon/Teras",    "#8BC34A", "BLK"),
    "diger":    ("Diğer",           "#FF6F3C", "DĞR"),
}

ROOM_TYPE_ORDER = ["mutfak", "yatak", "salon", "banyo", "calisma", "bilgisayar",
                   "cocuk", "garaj", "bahce", "depo", "koridor", "misafir",
                   "camasir", "balkon", "diger"]

CATEGORY_INFO = {
    "Elektronik":       ("#3C8DFF", "ELK"),
    "Mobilya":          ("#8D6E63", "MBL"),
    "Giyim":            ("#EC407A", "GYM"),
    "Kitap/Kırtasiye":  ("#7E57C2", "KTP"),
    "Mutfak Eşyası":    ("#FF7043", "MTF"),
    "Dekorasyon":       ("#26A69A", "DKR"),
    "Belge":            ("#607D8B", "BLG"),
    "Diğer":            ("#9E9E9E", "DĞR"),
}
ITEM_CATEGORIES = list(CATEGORY_INFO.keys())

THEMES = {
    "dark": {"bg": "#15131F", "surface": "#211E2E", "surface2": "#2A2640", "text": "#F2F0FA",
             "text_secondary": "#9C97B8", "primary": "#FF7A50", "accent": "#7C6CFF",
             "danger": "#FF6B6B", "warn": "#F2C14E", "ok": "#4FD8A0"},
}


def infer_room_type(name):
    n = name.lower()
    table = [
        ("mutfak", "mutfak"), ("yatak", "yatak"), ("salon", "salon"),
        ("banyo", "banyo"), ("tuvalet", "banyo"), ("çalışma", "calisma"),
        ("ofis", "calisma"), ("bilgisayar", "bilgisayar"), ("oyun", "bilgisayar"),
        ("çocuk", "cocuk"), ("bebek", "cocuk"), ("garaj", "garaj"),
        ("bahçe", "bahce"), ("depo", "depo"),
        ("kiler", "depo"), ("ambar", "depo"), ("koridor", "koridor"),
        ("antre", "koridor"), ("hol", "koridor"), ("misafir", "misafir"),
        ("çamaşır", "camasir"), ("balkon", "balkon"), ("teras", "balkon"),
    ]
    for kw, key in table:
        if kw in n:
            return key
    return "diger"


def hex_rgba(hex_color, alpha=1.0):
    r = get_color_from_hex(hex_color)
    return [r[0], r[1], r[2], alpha]


DEFAULT_FONT_SCALE = 1.3


def fs(base):
    """Metin boyutunu kullanıcının seçtiği 'Yazı Boyutu' ayarına göre
    ölçekler. Uygulamanın her yerinde font_size yerine bu kullanılır."""
    app = App.get_running_app()
    scale = app.font_scale if app else DEFAULT_FONT_SCALE
    return base * scale


def dph(base):
    """Satır/kart/buton yüksekliklerini yazı boyutu ayarına göre büyütür
    (böylece büyük yazı hiçbir zaman kutunun dışına taşmaz/kesilmez)."""
    app = App.get_running_app()
    scale = app.font_scale if app else DEFAULT_FONT_SCALE
    factor = 1 + (scale - 1) * 0.2
    return dp(base * factor)


def now_str():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")


# ---------------------------------------------------------------------------
# Veritabanı
# ---------------------------------------------------------------------------

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(get_db_path())
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._migrate()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_type TEXT DEFAULT 'diger'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            parent_id INTEGER,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'Diğer',
            note TEXT DEFAULT '',
            FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id) REFERENCES items(id) ON DELETE CASCADE
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT,
            item_name TEXT,
            path_text TEXT,
            deleted_at TEXT,
            restore_data TEXT
        )""")
        self.conn.commit()

    def _migrate(self):
        c = self.conn.cursor()
        c.execute("PRAGMA table_info(items)")
        cols = {row[1] for row in c.fetchall()}
        extra_item_cols = {
            "price": "REAL DEFAULT 0",
            "expiry": "TEXT DEFAULT ''",
            "loaned_to": "TEXT DEFAULT ''",
            "qty": "INTEGER DEFAULT 0",
            "qty_min": "INTEGER DEFAULT 0",
            "tags": "TEXT DEFAULT ''",
            "is_favorite": "INTEGER DEFAULT 0",
            "is_sell": "INTEGER DEFAULT 0",
            "is_lost": "INTEGER DEFAULT 0",
            "move_no": "INTEGER DEFAULT 0",
            "code": "TEXT DEFAULT ''",
            "emoji": "TEXT DEFAULT ''",
            "photo_path": "TEXT DEFAULT ''",
        }
        for col, decl in extra_item_cols.items():
            if col not in cols:
                c.execute(f"ALTER TABLE items ADD COLUMN {col} {decl}")

        c.execute("PRAGMA table_info(rooms)")
        rcols = {row[1] for row in c.fetchall()}
        if "room_type" not in rcols:
            c.execute("ALTER TABLE rooms ADD COLUMN room_type TEXT DEFAULT 'diger'")
        if "emoji" not in rcols:
            c.execute("ALTER TABLE rooms ADD COLUMN emoji TEXT DEFAULT ''")
        if "photo_path" not in rcols:
            c.execute("ALTER TABLE rooms ADD COLUMN photo_path TEXT DEFAULT ''")

        c.execute("PRAGMA table_info(history)")
        hcols = {row[1] for row in c.fetchall()}
        if "kind" not in hcols:
            c.execute("ALTER TABLE history ADD COLUMN kind TEXT DEFAULT 'Eşya'")
        if "restore_data" not in hcols:
            c.execute("ALTER TABLE history ADD COLUMN restore_data TEXT DEFAULT ''")
        self.conn.commit()

        c.execute("SELECT id FROM items WHERE code IS NULL OR code=''")
        for (iid,) in c.fetchall():
            c.execute("UPDATE items SET code=? WHERE id=?", (f"K-{iid:04d}", iid))
        self.conn.commit()

    def add_room(self, name, room_type, emoji="", photo_path=""):
        c = self.conn.cursor()
        c.execute("INSERT INTO rooms (name, room_type, emoji, photo_path) VALUES (?,?,?,?)",
                   (name, room_type, emoji, photo_path))
        self.conn.commit()
        return c.lastrowid

    def update_room(self, room_id, name, room_type, emoji="", photo_path=""):
        c = self.conn.cursor()
        c.execute("UPDATE rooms SET name=?, room_type=?, emoji=?, photo_path=? WHERE id=?",
                   (name, room_type, emoji, photo_path, room_id))
        self.conn.commit()

    def get_rooms(self):
        c = self.conn.cursor()
        c.execute("SELECT id, name, room_type, emoji, photo_path FROM rooms ORDER BY id")
        return c.fetchall()

    def get_room(self, room_id):
        c = self.conn.cursor()
        c.execute("SELECT id, name, room_type, emoji, photo_path FROM rooms WHERE id=?", (room_id,))
        return c.fetchone()

    def delete_room(self, room_id):
        c = self.conn.cursor()
        c.execute("SELECT name FROM rooms WHERE id=?", (room_id,))
        row = c.fetchone()
        if row:
            self._log_history("Oda", row[0], row[0], None)
        c.execute("DELETE FROM rooms WHERE id=?", (room_id,))
        self.conn.commit()

    def add_item(self, room_id, parent_id, name, category, note, **kw):
        c = self.conn.cursor()
        c.execute("""INSERT INTO items (room_id, parent_id, name, category, note,
                     price, expiry, loaned_to, qty, qty_min, tags, is_favorite,
                     is_sell, is_lost, move_no, emoji, photo_path)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (room_id, parent_id, name, category, note,
                   kw.get("price", 0), kw.get("expiry", ""), kw.get("loaned_to", ""),
                   kw.get("qty", 0), kw.get("qty_min", 0), kw.get("tags", ""),
                   int(kw.get("is_favorite", False)), int(kw.get("is_sell", False)),
                   int(kw.get("is_lost", False)), kw.get("move_no", 0), kw.get("emoji", ""),
                   kw.get("photo_path", "")))
        new_id = c.lastrowid
        c.execute("UPDATE items SET code=? WHERE id=?", (f"K-{new_id:04d}", new_id))
        self.conn.commit()
        return new_id

    def update_item(self, item_id, name, category, note, **kw):
        c = self.conn.cursor()
        c.execute("""UPDATE items SET name=?, category=?, note=?, price=?, expiry=?,
                     loaned_to=?, qty=?, qty_min=?, tags=?, is_favorite=?, is_sell=?,
                     is_lost=?, move_no=?, emoji=?, photo_path=? WHERE id=?""",
                  (name, category, note, kw.get("price", 0), kw.get("expiry", ""),
                   kw.get("loaned_to", ""), kw.get("qty", 0), kw.get("qty_min", 0),
                   kw.get("tags", ""), int(kw.get("is_favorite", False)),
                   int(kw.get("is_sell", False)), int(kw.get("is_lost", False)),
                   kw.get("move_no", 0), kw.get("emoji", ""), kw.get("photo_path", ""), item_id))
        self.conn.commit()

    def move_item(self, item_id, new_room_id, new_parent_id):
        c = self.conn.cursor()
        c.execute("UPDATE items SET room_id=?, parent_id=? WHERE id=?",
                   (new_room_id, new_parent_id, item_id))
        self.conn.commit()

    def empty_box(self, item_id):
        item = self.get_item(item_id)
        if not item:
            return
        room_id, parent_id = item[15], item[16]
        c = self.conn.cursor()
        c.execute("UPDATE items SET parent_id=? WHERE parent_id=?", (parent_id, item_id))
        self.conn.commit()

    ITEM_COLS = "id,name,category,note,price,expiry,loaned_to,qty,qty_min,tags,is_favorite,is_sell,is_lost,move_no,code,room_id,parent_id,emoji,photo_path"

    def get_items(self, room_id, parent_id):
        c = self.conn.cursor()
        if parent_id is None:
            c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE room_id=? AND parent_id IS NULL ORDER BY id", (room_id,))
        else:
            c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE parent_id=? ORDER BY id", (parent_id,))
        return c.fetchall()

    def count_children(self, item_id):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM items WHERE parent_id=?", (item_id,))
        return c.fetchone()[0]

    def get_item(self, item_id):
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE id=?", (item_id,))
        return c.fetchone()

    def item_value_sum(self, room_id, parent_id):
        items = self.get_items(room_id, parent_id)
        return sum((row[4] or 0) for row in items)

    def delete_item(self, item_id, path_text):
        item = self.get_item(item_id)
        if item:
            data = {
                "name": item[1], "category": item[2], "note": item[3],
                "price": item[4], "expiry": item[5], "loaned_to": item[6],
                "qty": item[7], "qty_min": item[8], "tags": item[9],
                "is_favorite": item[10], "is_sell": item[11], "is_lost": item[12],
                "move_no": item[13], "room_id": item[15], "parent_id": item[16],
            }
            self._log_history("Eşya", item[1], path_text, data)
        c = self.conn.cursor()
        c.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def restore_history(self, history_id):
        c = self.conn.cursor()
        c.execute("SELECT kind, restore_data FROM history WHERE id=?", (history_id,))
        row = c.fetchone()
        if not row or not row[1]:
            return False
        data = json.loads(row[1])
        self.add_item(data["room_id"], data["parent_id"], data["name"], data["category"],
                      data["note"], price=data["price"], expiry=data["expiry"],
                      loaned_to=data["loaned_to"], qty=data["qty"], qty_min=data["qty_min"],
                      tags=data["tags"], is_favorite=data["is_favorite"],
                      is_sell=data["is_sell"], is_lost=data["is_lost"], move_no=data["move_no"])
        c.execute("DELETE FROM history WHERE id=?", (history_id,))
        self.conn.commit()
        return True

    def _log_history(self, kind, name, path_text, restore_data):
        c = self.conn.cursor()
        c.execute("INSERT INTO history (kind, item_name, path_text, deleted_at, restore_data) VALUES (?,?,?,?,?)",
                   (kind, name, path_text, now_str(),
                    json.dumps(restore_data) if restore_data else ""))
        self.conn.commit()

    def get_history(self):
        c = self.conn.cursor()
        c.execute("SELECT id, kind, item_name, path_text, deleted_at, restore_data FROM history ORDER BY id DESC LIMIT 200")
        return c.fetchall()

    def search(self, query):
        q = f"%{query.lower()}%"
        c = self.conn.cursor()
        c.execute("""SELECT id, name, category, room_id, parent_id, tags FROM items
                     WHERE lower(name) LIKE ? OR lower(tags) LIKE ? OR lower(note) LIKE ?
                     ORDER BY id LIMIT 60""", (q, q, q))
        return c.fetchall()

    def get_path(self, item_id):
        chain = []
        c = self.conn.cursor()
        current = item_id
        while current is not None:
            c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE id=?", (current,))
            row = c.fetchone()
            if not row:
                break
            chain.append(row)
            current = row[16]
        chain.reverse()
        return chain

    def flagged_items(self, field):
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE {field}=1 ORDER BY id")
        return c.fetchall()

    def export_csv(self):
        rooms = {r[0]: r[1] for r in self.get_rooms()}
        path = os.path.join(get_export_path(), "evim_envanter.csv")
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items ORDER BY room_id, id")
        rows = c.fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Oda", "Eşya", "Kategori", "Not", "Fiyat", "Miktar", "Etiketler", "Kod"])
            for row in rows:
                room_name = rooms.get(row[15], "?")
                w.writerow([room_name, row[1], row[2], row[3], row[4], row[7], row[9], row[14]])
        return path


DB = Database()

KV = """
#:import dp kivy.metrics.dp

<RoundedCard>:
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]

<TopBar>:
    size_hint_y: None
    padding: dp(10), 0
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: root.bar_color
        Rectangle:
            pos: self.pos
            size: self.size
"""

Builder.load_string(KV)


class RoundedCard(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 1])


class ClickableCard(ButtonBehavior, RoundedCard):
    pass


class ClickableImage(ButtonBehavior, Image):
    pass


class ClickableLabel(ButtonBehavior, Label):
    pass


def _star_points(cx, cy, r_outer, r_inner, rotation=90):
    import math
    pts = []
    for i in range(10):
        angle = math.radians(rotation + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append(cx + r * math.cos(angle))
        pts.append(cy + r * math.sin(angle))
    return pts


class RoomIcon(Widget):
    """Oda türüne göre elle çizilmiş vektör simge (yazı tipine bağlı
    değildir, bu yüzden hiçbir cihazda bozulmaz/taşmaz)."""
    bg_color = ListProperty([1, 1, 1, 1])
    icon_key = StringProperty("diger")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw,
                  bg_color=self._redraw, icon_key=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.before.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if w <= 0 or h <= 0:
            return
        with self.canvas.before:
            Color(rgba=self.bg_color)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(18), dp(18), 0, 0])

        # simge, kenarlara asla değmeyecek şekilde ortalanmış KARE bir
        # kutu içinde çizilir (dikdörtgen kutu kullanılırsa simge yanlara
        # doğru gerilmiş görünüyordu, bu yüzden kare sabitlendi)
        box_size = min(w, h) * 0.62
        bx = x + (w - box_size) / 2
        by = y + (h - box_size) / 2
        bw = bh = box_size
        lw = max(dp(2.2), bh * 0.06)
        key = self.icon_key
        with self.canvas.before:
            Color(1, 1, 1, 0.95)
            if key == "mutfak":
                RoundedRectangle(pos=(bx, by), size=(bw, bh * 0.55), radius=[dp(4)])
                Ellipse(pos=(bx - bw * 0.06, by + bh * 0.30), size=(bw * 0.14, bh * 0.14))
                Ellipse(pos=(bx + bw * 0.92, by + bh * 0.30), size=(bw * 0.14, bh * 0.14))
                Line(points=[bx, by + bh * 0.60, bx + bw, by + bh * 0.60], width=lw)
            elif key == "yatak":
                RoundedRectangle(pos=(bx, by), size=(bw, bh * 0.4), radius=[dp(3)])
                RoundedRectangle(pos=(bx + bw * 0.04, by + bh * 0.4), size=(bw * 0.34, bh * 0.24), radius=[dp(3)])
                Line(points=[bx + bw * 0.02, by, bx + bw * 0.02, by - bh * 0.14], width=lw)
                Line(points=[bx + bw * 0.98, by, bx + bw * 0.98, by - bh * 0.14], width=lw)
            elif key == "salon":
                RoundedRectangle(pos=(bx, by + bh * 0.04), size=(bw, bh * 0.34), radius=[dp(4)])
                RoundedRectangle(pos=(bx + bw * 0.08, by + bh * 0.36), size=(bw * 0.84, bh * 0.5), radius=[dp(4)])
                RoundedRectangle(pos=(bx, by + bh * 0.10), size=(bw * 0.12, bh * 0.5), radius=[dp(3)])
                RoundedRectangle(pos=(bx + bw * 0.88, by + bh * 0.10), size=(bw * 0.12, bh * 0.5), radius=[dp(3)])
            elif key == "banyo":
                Line(points=[bx + bw * 0.5, by + bh, bx + bw * 0.16, by + bh * 0.42,
                             bx + bw * 0.84, by + bh * 0.42], width=lw, close=True)
                Ellipse(pos=(bx + bw * 0.16, by), size=(bw * 0.68, bh * 0.5))
            elif key in ("calisma", "bilgisayar"):
                RoundedRectangle(pos=(bx, by + bh * 0.28), size=(bw, bh * 0.55), radius=[dp(3)])
                RoundedRectangle(pos=(bx + bw * 0.38, by), size=(bw * 0.24, bh * 0.2), radius=[dp(2)])
                Line(points=[bx, by, bx + bw, by], width=lw)
                if key == "bilgisayar":
                    Ellipse(pos=(bx + bw * 0.80, by + bh * 0.70), size=(bw * 0.14, bh * 0.14))
            elif key == "cocuk":
                Line(points=_star_points(bx + bw / 2, by + bh / 2, min(bw, bh) * 0.52, min(bw, bh) * 0.22),
                     width=lw, close=True)
            elif key == "garaj":
                RoundedRectangle(pos=(bx, by + bh * 0.34), size=(bw, bh * 0.4), radius=[dp(8)])
                Ellipse(pos=(bx + bw * 0.04, by + bh * 0.04), size=(bw * 0.24, bh * 0.24))
                Ellipse(pos=(bx + bw * 0.72, by + bh * 0.04), size=(bw * 0.24, bh * 0.24))
            elif key == "bahce":
                Line(points=[bx + bw * 0.5, by + bh, bx + bw * 0.14, by + bh * 0.5,
                             bx + bw * 0.86, by + bh * 0.5], width=lw, close=True)
                Line(points=[bx + bw * 0.46, by, bx + bw * 0.46, by + bh * 0.4,
                             bx + bw * 0.54, by + bh * 0.4, bx + bw * 0.54, by], width=lw, close=True)
            elif key == "depo":
                Line(points=[bx, by, bx + bw, by, bx + bw, by + bh, bx, by + bh], width=lw, close=True)
                Line(points=[bx, by, bx + bw, by + bh], width=lw)
                Line(points=[bx, by + bh, bx + bw, by], width=lw)
            else:
                Line(points=[bx + bw * 0.5, by + bh, bx, by + bh * 0.42, bx + bw, by + bh * 0.42],
                     width=lw, close=True)
                RoundedRectangle(pos=(bx + bw * 0.12, by), size=(bw * 0.76, bh * 0.42), radius=[dp(2)])


class ColorDot(Widget):
    """Kategoriyi belirten küçük renk noktası (büyük, ortada yüzen daire
    rozetinin yerine geçti)."""
    dot_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw, dot_color=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.before.clear()
        if self.width <= 0:
            return
        with self.canvas.before:
            Color(rgba=self.dot_color)
            Ellipse(pos=self.pos, size=self.size)


class _ClickableRoomIcon(ButtonBehavior, RoomIcon):
    pass


class _EmojiCover(ButtonBehavior, BoxLayout):
    """Emoji ile gösterilen, tıklanabilir oda kapağı."""
    bg_color = ListProperty([1, 1, 1, 1])
    emoji_text = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._color = Color(rgba=self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18), dp(18), 0, 0])
        self.bind(pos=self._update_rect, size=self._update_rect, bg_color=self._update_color)
        self.add_widget(Label(text=self.emoji_text, font_size=dp(42)))

    def _update_rect(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *a):
        self._color.rgba = self.bg_color


class TopBar(BoxLayout):
    bar_color = ListProperty([1, 1, 1, 1])


class IconBtn(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(42), dp(42)))
        kw.setdefault("font_size", fs(15))
        super().__init__(**kw)


class RoundActionButton(ButtonBehavior, Label):
    """Yuvarlak köşeli, düz Kivy Button'dan daha modern görünen aksiyon
    butonu (Düzenle/Taşı/Sil vb. için)."""
    bg_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        bg = kw.pop("bg_color", [1, 1, 1, 0.15])
        super().__init__(**kw)
        self.bg_color = bg
        with self.canvas.before:
            self._color = Color(rgba=self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update, bg_color=self._update_color)

    def _update(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *a):
        self._color.rgba = self.bg_color


class Badge(Label):
    def __init__(self, bg="#E4573D", **kw):
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("height", dph(15))
        kw.setdefault("font_size", fs(8))
        kw.setdefault("bold", True)
        kw.setdefault("color", (1, 1, 1, 1))
        kw.setdefault("padding", (dp(5), dp(2)))
        super().__init__(**kw)
        self.bind(texture_size=self._resize)
        self._bg = bg
        with self.canvas.before:
            self._color = Color(*hex_rgba(bg))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _resize(self, *a):
        self.width = self.texture_size[0] + dp(16)

    def _update_rect(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size


class HomeScreen(Screen):
    pass


class RoomScreen(Screen):
    pass


class InfoScreen(Screen):
    pass


class EvimApp(App):
    guest_mode = BooleanProperty(False)
    view_mode = StringProperty("grid")
    font_scale = NumericProperty(DEFAULT_FONT_SCALE * 2.5)
    nav_stack = []
    _active_popup = None

    def theme(self):
        return THEMES["dark"]

    def build(self):
        self.title = "Evim"
        self.font_scale = load_saved_font_scale(self.font_scale)
        Window.clearcolor = hex_rgba(self.theme()["bg"])
        Window.bind(on_keyboard=self._on_keyboard)
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(RoomScreen(name="room"))
        self.sm.add_widget(InfoScreen(name="info"))
        self.refresh_home()
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE,
                                     Permission.WRITE_EXTERNAL_STORAGE])
            except Exception:
                pass
        return self.sm

    def _on_keyboard(self, window, key, *args):
        if key == 27:  # Android geri tuşu / ESC
            if self._active_popup is not None:
                try:
                    self._active_popup.dismiss()
                except Exception:
                    pass
                self._active_popup = None
                return True
            if self.sm.current in ("info",) or (self.sm.current == "room" and self.nav_stack):
                self.go_back()
                return True
            if self.sm.current == "home":
                return False
            self.go_back()
            return True
        return False

    def toggle_guest(self):
        self.guest_mode = not self.guest_mode
        self._refresh_current()

    def open_font_size_dialog(self):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(14), padding=dp(18))
        box.add_widget(Label(text="Yazı Boyutu", size_hint_y=None, height=dph(30),
                             bold=True, font_size=fs(16), color=hex_rgba(th["text"])))
        box.add_widget(Label(text="0 = şu anki boyut. Eksiye çekince küçülür, artıya çekince büyür.",
                             size_hint_y=None, height=dph(20), font_size=fs(11),
                             color=hex_rgba(th["text_secondary"])))

        preview = Label(text="Örnek Yazı Aa", size_hint_y=None, height=dph(50),
                        font_size=fs(16), color=hex_rgba(th["text"]))
        box.add_widget(preview)

        current_pct = (self.font_scale / DEFAULT_FONT_SCALE - 1) * 100
        current_pct = max(-100, min(200, current_pct))
        slider = Slider(min=-100, max=200, value=current_pct, step=5, size_hint_y=None, height=dph(40))
        box.add_widget(slider)

        pct_lbl = Label(text=f"{int(current_pct):+d}", size_hint_y=None, height=dph(26),
                        font_size=fs(13), color=hex_rgba(th["text_secondary"]))
        box.add_widget(pct_lbl)

        def pct_to_scale(pct):
            return max(0.8, min(DEFAULT_FONT_SCALE * 3, DEFAULT_FONT_SCALE * (1 + pct / 130)))

        def on_slide(instance, value):
            pct_lbl.text = f"{int(value):+d}"
            preview.font_size = 16 * (pct_to_scale(value) / DEFAULT_FONT_SCALE)
        slider.bind(value=on_slide)

        btn_row = BoxLayout(size_hint_y=None, height=dph(50), spacing=dp(10))
        cancel = Button(text="İPTAL", background_normal="",
                        background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]))
        ok = Button(text="UYGULA", background_normal="", background_color=hex_rgba(th["primary"]),
                   color=(1, 1, 1, 1), bold=True)
        btn_row.add_widget(cancel)
        btn_row.add_widget(ok)

        popup = self.open_auto_popup("", box, buttons_row=btn_row, scrollable=False)

        def apply_and_close(*a):
            self.font_scale = pct_to_scale(slider.value)
            save_font_scale(self.font_scale)
            popup.dismiss()
            self._refresh_current()
        cancel.bind(on_release=lambda *a: popup.dismiss())
        ok.bind(on_release=apply_and_close)

    def toggle_view_mode(self):
        self.view_mode = "list" if self.view_mode == "grid" else "grid"
        if self.sm.current == "room":
            self._render_room()

    def _refresh_current(self):
        cur = self.sm.current
        if cur == "home":
            self.refresh_home()
        elif cur == "room":
            self._render_room()

    def make_topbar(self, title, on_back=None, show_menu=True):
        th = self.theme()
        bar_h = dph(40)
        bar = TopBar(bar_color=hex_rgba(th["primary"]), height=bar_h)
        if on_back:
            back = IconBtn(text="‹", font_size=fs(20), color=(1, 1, 1, 1),
                           size=(dph(30), bar_h))
            back.bind(on_release=lambda *a: on_back())
            bar.add_widget(back)
        lbl = Label(text=title, bold=True, font_size=fs(14), color=(1, 1, 1, 1),
                    halign="left", valign="middle", shorten=True,
                    size_hint_y=None, height=bar_h)
        lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        bar.add_widget(lbl)
        if self.guest_mode:
            bar.add_widget(Label(text="MİSAFİR", font_size=fs(9), color=(1, 1, 1, 0.8),
                                  size_hint=(None, None), size=(dph(56), bar_h)))
        if show_menu:
            menu_btn = IconBtn(text="Menü", font_size=fs(10), bold=True, color=(1, 1, 1, 1),
                               size=(dph(46), bar_h))
            menu_btn.bind(on_release=lambda *a: self.open_main_menu(menu_btn))
            bar.add_widget(menu_btn)
        return bar

    def open_main_menu(self, caller):
        th = self.theme()
        dropdown = DropDown(auto_width=False, width=dph(260))
        entries = [
            ("Ana ekrana dön / Ara", self.go_home),
            ("Silinenler Geçmişi", self.open_history),
            ("Satılık / Bağış Listesi", lambda: self.open_flag_list("is_sell", "Satılık / Bağış Listesi")),
            ("Kayıp Eşyalar", lambda: self.open_flag_list("is_lost", "Kayıp Eşyalar")),
            ("Taşınma Modu", self.open_move_mode),
            ("CSV Dışa Aktar", self.do_export_csv),
            ("Yazı Boyutu Ayarı", self.open_font_size_dialog),
            ("Misafir Modu Aç/Kapat", self.toggle_guest),
        ]
        for label, fn in entries:
            btn = Button(text=label, size_hint_y=None, height=dph(46),
                         background_normal="", background_color=hex_rgba(th["surface"]),
                         color=hex_rgba(th["text"]), font_size=fs(13), halign="left")
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))

            def make_cb(f):
                def cb(*a):
                    dropdown.dismiss()
                    f()
                return cb
            btn.bind(on_release=make_cb(fn))
            dropdown.add_widget(btn)
        dropdown.open(caller)

    def go_home(self):
        self.nav_stack = []
        self.refresh_home()
        self.sm.transition = SlideTransition(direction="right")
        self.sm.current = "home"

    _managed_inputs = []

    def fix_focus(self, text_input):
        """Android'de bazı cihazlarda arka arkaya birden fazla TextInput
        olduğunda ilk dokunuş klavyeyi açmıyor (bilinen Kivy/Android
        zamanlama sorunu). Aynı diyalogdaki DİĞER tüm alanların odağını
        hemen bırakıp, dokunulan alana kısa bir gecikmeyle odaklanarak
        Android'in klavyeyi güvenilir şekilde göstermesini sağlıyoruz."""
        self._managed_inputs.append(text_input)

        def on_touch_down(instance, touch):
            if instance.collide_point(*touch.pos):
                for other in list(self._managed_inputs):
                    if other is not instance:
                        try:
                            other.focus = False
                        except ReferenceError:
                            pass
                Clock.schedule_once(lambda dt: setattr(instance, "focus", True), 0.03)
                Clock.schedule_once(lambda dt: setattr(instance, "focus", True), 0.15)
            return False
        text_input.bind(on_touch_down=on_touch_down)
        return text_input

    def themed_box(self, **kw):
        """Popup içerikleri için tema rengiyle dolu bir kutu.
        Kivy'nin varsayılan Popup zemini tema ile uyuşmayabildiğinden
        (açık modda metnin görünmez olmasına yol açan hata buydu) her
        popup içeriği artık kendi zemin rengini taşıyor."""
        th = self.theme()
        box = BoxLayout(**kw)
        with box.canvas.before:
            Color(rgba=hex_rgba(th["surface"]))
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(14)])

        def _update(inst, *a):
            rect.pos = inst.pos
            rect.size = inst.size
        box.bind(pos=_update, size=_update)
        return box

    def open_auto_popup(self, title, inner_box, buttons_row=None, max_frac=0.94, scrollable=True):
        """Popup'ı İÇERİĞİN gerçek yüksekliğine göre otomatik boyutlandırır.
        Yazı boyutu ayarı büyütülse de küçültülse de pencere her zaman
        içeriğe tam oturur, ekrana sığmayan kısımlar kaydırılabilir olur."""
        th = self.theme()
        inner_box.size_hint_y = None
        inner_box.bind(minimum_height=inner_box.setter("height"))

        outer = self.themed_box(orientation="vertical")
        if scrollable:
            scroll = ScrollView(size_hint=(1, 1), bar_width=dp(3))
            scroll.add_widget(inner_box)
            outer.add_widget(scroll)
        else:
            outer.add_widget(inner_box)
        if buttons_row is not None:
            outer.add_widget(buttons_row)

        popup = Popup(title=title, content=outer, size_hint=(0.92, None),
                      height=dp(200), separator_height=(dp(1) if title else 0),
                      background="", background_color=hex_rgba(th["bg"]),
                      title_color=hex_rgba(th["text"]))
        self._active_popup = popup

        def resize(*a):
            btn_h = buttons_row.height if buttons_row is not None else 0
            title_h = dp(50) if title else 0
            total = inner_box.height + btn_h + title_h + dp(50)
            max_h = Window.height * max_frac
            popup.height = min(total, max_h)
        inner_box.bind(minimum_height=lambda *a: resize())
        if buttons_row is not None and hasattr(buttons_row, "bind"):
            try:
                buttons_row.bind(minimum_height=lambda *a: resize())
            except Exception:
                pass
            buttons_row.bind(height=lambda *a: resize())
        Clock.schedule_once(lambda dt: resize(), 0)
        Clock.schedule_once(lambda dt: resize(), 0.12)
        Clock.schedule_once(lambda dt: resize(), 0.3)

        def on_dismiss(*a):
            if self._active_popup is popup:
                self._active_popup = None
        popup.bind(on_dismiss=on_dismiss)
        popup.open()
        return popup

    def styled_popup_buttons(self, cancel_cb, confirm_cb, confirm_text="KAYDET"):
        th = self.theme()
        row = BoxLayout(size_hint_y=None, height=dph(50), spacing=dp(10), padding=(dp(4), dp(4)))
        cancel = Button(text="İPTAL", background_normal="",
                         background_color=hex_rgba(th["text_secondary"], 0.3),
                         color=hex_rgba(th["text"]), font_size=fs(14))
        cancel.bind(on_release=lambda *a: cancel_cb())
        ok = Button(text=confirm_text, background_normal="",
                    background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1), font_size=fs(14), bold=True)
        ok.bind(on_release=confirm_cb)
        row.add_widget(cancel)
        row.add_widget(ok)
        return row

    def badges_for_item(self, row, th):
        badges = []
        (_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
         is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = row
        if is_fav:
            badges.append(("Favori", th["warn"]))
        if loaned_to:
            badges.append((f"Ödünç: {loaned_to}", th["danger"]))
        if is_sell:
            badges.append(("Satılık", th["ok"]))
        if is_lost:
            badges.append(("Kayıp", th["danger"]))
        if qty_min and qty <= qty_min:
            badges.append(("Stok Azaldı", th["danger"]))
        if expiry:
            try:
                d = datetime.datetime.strptime(expiry, "%d.%m.%Y")
                delta = (d - datetime.datetime.now()).days
                if delta < 0:
                    badges.append(("Süresi Doldu", th["danger"]))
                elif delta <= 7:
                    badges.append((f"{delta}g kaldı", th["warn"]))
            except Exception:
                pass
        return badges

    def refresh_home(self):
        th = self.theme()
        screen = self.sm.get_screen("home")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("EVİM"))

        search_row = BoxLayout(size_hint_y=None, height=dph(34), padding=(dp(10), dp(2)))
        self._search_input = TextInput(hint_text="Eşya ara...", multiline=False,
                                        font_size=fs(11), padding=(dp(8), dp(6)),
                                        background_color=hex_rgba(th["surface2"]),
                                        foreground_color=hex_rgba(th["text"]),
                                        hint_text_color=hex_rgba(th["text_secondary"]),
                                        cursor_color=hex_rgba(th["primary"]))
        self.fix_focus(self._search_input)
        self._search_input.bind(text=self._on_search_text)
        search_row.add_widget(self._search_input)
        root.add_widget(search_row)

        self._results_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self._results_box.bind(minimum_height=self._results_box.setter("height"))
        root.add_widget(self._results_box)

        home_scroll = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter("height"))

        favs = DB.flagged_items("is_favorite")
        if favs:
            fav_title = Label(text="Sık Kullanılanlar", size_hint_y=None, height=dph(22),
                              font_size=fs(12), bold=True, color=hex_rgba(th["text_secondary"]),
                              halign="left", valign="middle")
            fav_title.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(28), w.height)))
            fav_title.padding_x = dp(14)
            content.add_widget(fav_title)
            fav_scroll = ScrollView(size_hint_y=None, height=dph(48), do_scroll_y=False)
            fav_row = BoxLayout(size_hint_x=None, spacing=dp(8), padding=(dp(14), 0))
            fav_row.bind(minimum_width=fav_row.setter("width"))
            for row in favs:
                b = Button(text=row[1], size_hint=(None, None), size=(dph(110), dph(40)),
                           background_normal="", background_color=hex_rgba(th["primary"], 0.15),
                           color=hex_rgba(th["primary"]), font_size=fs(12))
                b.bind(on_release=lambda inst, iid=row[0]: self.jump_to_item(iid))
                fav_row.add_widget(b)
            fav_scroll.add_widget(fav_row)
            content.add_widget(fav_scroll)

        rooms_label_row = BoxLayout(size_hint_y=None, height=dph(30), padding=(dp(14), 0))
        rooms_label_row.add_widget(Label(text="Odalar", font_size=fs(15), bold=True, color=hex_rgba(th["text"])))
        content.add_widget(rooms_label_row)

        grid = GridLayout(cols=2, spacing=dp(14), padding=(dp(14), 0, dp(14), dp(90)), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for rid, name, rtype, remoji, rphoto in DB.get_rooms():
            grid.add_widget(self._make_room_card(rid, name, rtype, remoji, rphoto))
        content.add_widget(grid)

        home_scroll.add_widget(content)
        root.add_widget(home_scroll)
        screen.add_widget(root)

        if not self.guest_mode:
            root_float = FloatLayout()
            fab = Button(text="+ Oda Ekle", font_size=fs(12), bold=True, size_hint=(None, None),
                         size=(dph(112), dph(38)), pos_hint={"right": 0.97, "y": 0.025},
                         background_normal="", background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1))
            fab.bind(on_release=lambda *a: self.open_add_room_dialog())
            root_float.add_widget(fab)
            screen.add_widget(root_float)

        Window.clearcolor = hex_rgba(th["bg"])

    def _on_search_text(self, instance, value):
        self._results_box.clear_widgets()
        value = value.strip()
        if len(value) < 2:
            return
        th = self.theme()
        results = DB.search(value)
        if not results:
            self._results_box.add_widget(Label(text="Sonuç bulunamadı.", size_hint_y=None, height=dph(36),
                                                color=hex_rgba(th["text_secondary"])))
            return
        for item_id, name, category, room_id, parent_id, tags in results:
            path = DB.get_path(item_id)
            crumb = " › ".join([DB.get_room(room_id)[1]] + [p[1] for p in path[:-1]] + [name]) if path else name
            row = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(42),
                         background_normal="", background_color=hex_rgba(th["surface"]),
                         color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            row.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            row.bind(on_release=lambda inst, iid=item_id: self.jump_to_item(iid))
            self._results_box.add_widget(row)

    def jump_to_item(self, item_id):
        path = DB.get_path(item_id)
        if not path:
            return
        room_id = path[0][15]
        room = DB.get_room(room_id)
        room_name = room[1] if room else "?"
        stack = [(room_id, None, room_name, room_name)]
        crumb = room_name
        for row in path:
            crumb = crumb + "  ›  " + row[1]
            stack.append((room_id, row[0], row[1], crumb))
        self.nav_stack = stack
        self._render_room()
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "room"

    def _make_room_card(self, room_id, name, room_type, emoji="", photo_path=""):
        th = self.theme()
        label, color, abbr = ROOM_TYPES.get(room_type, ROOM_TYPES["diger"])
        card = ClickableCard(orientation="vertical", size_hint=(1, None),
                             padding=0, spacing=0, bg_color=hex_rgba(th["surface"]))
        card.bind(minimum_height=card.setter("height"))
        card.bind(on_release=lambda *a: self.open_room_detail(room_id, name, room_type))

        if photo_path and os.path.exists(photo_path):
            cover = ClickableImage(source=photo_path, size_hint_y=None, height=dph(52),
                                   allow_stretch=True, keep_ratio=False)
        elif emoji:
            cover = _EmojiCover(size_hint_y=None, height=dph(52), bg_color=hex_rgba(color), emoji_text=emoji)
        else:
            cover = _ClickableRoomIcon(size_hint_y=None, height=dph(52), bg_color=hex_rgba(color), icon_key=room_type)
        cover.bind(on_release=lambda *a: self.enter_room(room_id, name))
        card.add_widget(cover)

        body = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(8), dp(6)), spacing=dp(2))
        body.bind(minimum_height=body.setter("height"))
        name_lbl = ClickableLabel(text=name, color=hex_rgba(th["text"]), bold=True, font_size=fs(14),
                                  size_hint_y=None, height=dph(20))
        name_lbl.bind(on_release=lambda *a: self.enter_room(room_id, name))
        body.add_widget(name_lbl)
        item_count = len(DB.get_items(room_id, None))
        sub = Label(text=f"{item_count} eşya", font_size=fs(10), color=hex_rgba(th["text_secondary"]),
                    size_hint_y=None, height=dph(14))
        body.add_widget(sub)
        card.add_widget(body)
        return card

    def open_room_detail(self, room_id, name, room_type):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(16))
        box.add_widget(Label(text=name, font_size=fs(18), bold=True, color=hex_rgba(th["text"]),
                             size_hint_y=None, height=dph(30)))
        item_count = len(DB.get_items(room_id, None))
        box.add_widget(Label(text=f"{item_count} eşya  ·  {ROOM_TYPES.get(room_type, ROOM_TYPES['diger'])[0]}",
                             font_size=fs(13), color=hex_rgba(th["text_secondary"]),
                             size_hint_y=None, height=dph(24)))

        actions = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        actions.bind(minimum_height=actions.setter("height"))

        def act_btn(text, color_key, cb):
            b = RoundActionButton(text=text, size_hint_y=None, height=dph(44), font_size=fs(13),
                                  bold=True, bg_color=hex_rgba(th[color_key], 0.18),
                                  color=hex_rgba(th[color_key]))
            b.bind(on_release=cb)
            return b

        actions.add_widget(act_btn("Aç / İçine Gir", "primary", lambda *a: (popup.dismiss(), self.enter_room(room_id, name))))
        if not self.guest_mode:
            actions.add_widget(act_btn("Düzenle", "text_secondary",
                                       lambda *a: (popup.dismiss(), self.open_edit_room_dialog(room_id))))
            actions.add_widget(act_btn("Sil", "danger", lambda *a: (popup.dismiss(), self._confirm_delete_room(room_id, name))))

        popup = self.open_auto_popup("", box, buttons_row=actions)

    def enter_room(self, room_id, name):
        self.nav_stack = [(room_id, None, name, name)]
        self._render_room()
        self.sm.transition = RiseInTransition(duration=0.28)
        self.sm.current = "room"

    def _render_room(self):
        th = self.theme()
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        screen = self.sm.get_screen("room")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar(title, on_back=self.go_back))

        info_row = BoxLayout(size_hint_y=None, height=dph(30), padding=(dp(14), 0), spacing=dp(8))
        crumb = Label(text=breadcrumb, font_size=fs(12), color=hex_rgba(th["text_secondary"]),
                     halign="left", valign="middle", shorten=True)
        crumb.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        info_row.add_widget(crumb)
        total = DB.item_value_sum(room_id, parent_id)
        if total:
            total_lbl = Label(text=f"Toplam: {total:.0f} TL", font_size=fs(12), bold=True,
                              color=hex_rgba(th["primary"]), size_hint_x=None)
            total_lbl.bind(texture_size=lambda w, val: setattr(w, "width", val[0] + dp(8)))
            info_row.add_widget(total_lbl)
        view_btn = IconBtn(text=("#" if self.view_mode == "grid" else "="), font_size=fs(17),
                            color=hex_rgba(th["text_secondary"]))
        view_btn.bind(on_release=lambda *a: self.toggle_view_mode())
        info_row.add_widget(view_btn)
        root.add_widget(info_row)

        scroll = ScrollView()
        cols = 2 if self.view_mode == "grid" else 1
        grid = GridLayout(cols=cols, spacing=dp(14), padding=(dp(14), dp(6), dp(14), dp(90)), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        items = DB.get_items(room_id, parent_id)
        if not items:
            empty = Label(text="Henüz eşya eklenmedi.\nSağ alttaki + ile ekleyin.",
                          color=hex_rgba(th["text_secondary"]), size_hint_y=None, height=dph(80), font_size=fs(14))
            grid.add_widget(empty)
        for row in items:
            grid.add_widget(self._make_item_card(row, list_mode=(self.view_mode == "list")))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        screen.add_widget(root)

        if not self.guest_mode:
            root_float = FloatLayout()
            fab = Button(text="+ Eşya Ekle", font_size=fs(12), bold=True, size_hint=(None, None),
                         size=(dph(118), dph(38)), pos_hint={"right": 0.97, "y": 0.025},
                         background_normal="", background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1))
            fab.bind(on_release=lambda *a: self.open_add_item_dialog())
            root_float.add_widget(fab)
            screen.add_widget(root_float)

    def _make_item_card(self, row, list_mode=False):
        th = self.theme()
        (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
         is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = row
        child_count = DB.count_children(item_id)

        card = ClickableCard(orientation="vertical", size_hint=(1, None),
                             padding=(dp(11), dp(8), dp(8), dp(8)), spacing=dp(4),
                             bg_color=hex_rgba(th["surface"]))
        card.bind(minimum_height=card.setter("height"))
        card.bind(on_release=lambda *a: self.open_item_detail(row))

        cat_color, _cat_abbr = CATEGORY_INFO.get(category, CATEGORY_INFO["Diğer"])
        with card.canvas.after:
            Color(rgba=hex_rgba(cat_color))
            _accent = RoundedRectangle(pos=card.pos, size=(dp(3), card.height), radius=[dp(2)])

        def _update_accent(inst, *a):
            _accent.pos = (inst.x, inst.y)
            _accent.size = (dp(3), inst.height)
        card.bind(pos=_update_accent, size=_update_accent)

        title = name + (f"  ({child_count})" if child_count else "")
        name_row = BoxLayout(size_hint_y=None, height=dph(24), spacing=dp(4))
        name_lbl = ClickableLabel(text=title, color=hex_rgba(th["text"]), font_size=fs(14), bold=True,
                                  halign="left", valign="middle", shorten=True)
        name_lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        name_lbl.bind(on_release=lambda *a: self.enter_item(item_id, name))
        name_row.add_widget(name_lbl)
        info_dot = ClickableLabel(text="?", font_size=fs(11), bold=True, color=hex_rgba(th["text_secondary"]),
                                  size_hint=(None, None), size=(dph(20), dph(20)))
        info_dot.bind(on_release=lambda *a: self.open_item_detail(row))
        with info_dot.canvas.before:
            Color(rgba=hex_rgba(th["surface2"]))
            _dot_rect = Ellipse(pos=info_dot.pos, size=info_dot.size)
        info_dot.bind(pos=lambda w, *a: setattr(_dot_rect, "pos", w.pos),
                      size=lambda w, *a: setattr(_dot_rect, "size", w.size))
        name_row.add_widget(info_dot)
        card.add_widget(name_row)

        # Rozet satırı her zaman aynı yükseklikte ayrılır (boş olsa bile),
        # böylece tüm kartlar içerikten bağımsız aynı boyutta olur. Kaydırılabilir
        # olduğundan rozetler kartın dışına taşmaz.
        badge_scroll = ScrollView(size_hint_y=None, height=dph(18), do_scroll_y=False, bar_width=0)
        badge_row = BoxLayout(size_hint=(None, 1), spacing=dp(4))
        badge_row.bind(minimum_width=badge_row.setter("width"))
        badges = self.badges_for_item(row, th)
        for text, color in badges[:3]:
            badge_row.add_widget(Badge(text=text, bg=color))
        badge_scroll.add_widget(badge_row)
        card.add_widget(badge_scroll)

        return card

    def open_item_detail(self, row):
        th = self.theme()
        (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
         is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = row
        child_count = DB.count_children(item_id)

        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(16))
        box.add_widget(Label(text=name, font_size=fs(18), bold=True, color=hex_rgba(th["text"]),
                             size_hint_y=None, height=dph(30)))

        lbl_hex = "".join(f"{int(c*255):02X}" for c in hex_rgba(th["text_secondary"])[:3])
        val_hex = "".join(f"{int(c*255):02X}" for c in hex_rgba(th["text"])[:3])

        def field_line(label, value):
            return f"[b][color={lbl_hex}]{label}:[/color][/b] [color={val_hex}]{value}[/color]"

        info_lines = [field_line("Kategori", category)]
        if note:
            info_lines.append(field_line("Not", note))
        if price:
            info_lines.append(field_line("Değer", f"{price:.0f} TL"))
        if expiry:
            info_lines.append(field_line("Son kul./garanti", expiry))
        if loaned_to:
            info_lines.append(field_line("Ödünç", loaned_to))
        if qty:
            info_lines.append(field_line("Miktar", f"{qty}" + (f" (min {qty_min})" if qty_min else "")))
        if tags:
            info_lines.append(field_line("Etiketler", tags))
        if move_no:
            info_lines.append(field_line("Koli no", str(move_no)))
        if child_count:
            info_lines.append(field_line("İçindeki öğe sayısı", str(child_count)))
        flags = []
        if is_fav:
            flags.append("Favori")
        if is_sell:
            flags.append("Satılık")
        if is_lost:
            flags.append("Kayıp")
        if qty_min and qty <= qty_min:
            flags.append("Stok Azaldı")
        if flags:
            info_lines.append(field_line("İşaret", ", ".join(flags)))

        info_lbl = Label(text="\n".join(info_lines), font_size=fs(13), markup=True,
                         halign="left", valign="top", size_hint_y=None)
        info_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        info_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(info_lbl)

        actions = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        actions.bind(minimum_height=actions.setter("height"))

        def act_btn(text, color_key, cb):
            b = RoundActionButton(text=text, size_hint_y=None, height=dph(44), font_size=fs(13),
                                  bold=True, bg_color=hex_rgba(th[color_key], 0.18),
                                  color=hex_rgba(th[color_key]))
            b.bind(on_release=cb)
            return b

        enter_btn = act_btn("Aç / İçine Gir", "primary", lambda *a: (popup.dismiss(), self.enter_item(item_id, name)))
        actions.add_widget(enter_btn)

        if not self.guest_mode:
            edit_btn = act_btn("Düzenle", "text_secondary", lambda *a: (popup.dismiss(), self.open_edit_item_dialog(item_id)))
            actions.add_widget(edit_btn)
            move_btn = act_btn("Taşı", "text_secondary", lambda *a: (popup.dismiss(), self.open_move_dialog(item_id)))
            actions.add_widget(move_btn)
            if child_count:
                empty_btn = act_btn(f"Kutuyu Boşalt ({child_count} öğe)", "text_secondary",
                                    lambda *a: (popup.dismiss(), self._confirm_empty_box(item_id, name)))
                actions.add_widget(empty_btn)
            del_btn = act_btn("Sil", "danger", lambda *a: (popup.dismiss(), self._confirm_delete_item(item_id, name)))
            actions.add_widget(del_btn)

        popup = self.open_auto_popup("", box, buttons_row=actions, scrollable=False)

    def enter_item(self, item_id, name):
        room_id, _, _, breadcrumb = self.nav_stack[-1]
        self.nav_stack.append((room_id, item_id, name, breadcrumb + "  ›  " + name))
        self._render_room()
        self.sm.transition = RiseInTransition(duration=0.28)
        self.sm.current = "room"

    def go_back(self):
        if self.sm.current == "info":
            self.sm.transition = SlideTransition(direction="right")
            if self.nav_stack:
                self._render_room()
                self.sm.current = "room"
            else:
                self.refresh_home()
                self.sm.current = "home"
            return
        if self.nav_stack:
            self.nav_stack.pop()
        self.sm.transition = FadeTransition(duration=0.2)
        if self.nav_stack:
            self._render_room()
            self.sm.current = "room"
        else:
            self.refresh_home()
            self.sm.current = "home"

    def open_history(self):
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Silinenler Geçmişi", on_back=self.go_back, show_menu=False))
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.get_history()
        if not rows:
            box.add_widget(Label(text="Henüz silinen bir şey yok.", size_hint_y=None, height=dph(40),
                                  color=hex_rgba(th["text_secondary"])))
        for hid, kind, name, path_text, deleted_at, restore_data in rows:
            row_box = RoundedCard(orientation="horizontal", size_hint_y=None, height=dph(60),
                                  padding=dp(8), spacing=dp(8), bg_color=hex_rgba(th["surface"]))
            txt = Label(text=f"{name}\n{path_text}  ·  {deleted_at}", font_size=fs(11),
                       color=hex_rgba(th["text_secondary"]), halign="left", valign="middle")
            txt.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
            row_box.add_widget(txt)
            if restore_data:
                restore_btn = Button(text="Geri Getir", size_hint=(None, None), size=(dp(90), dp(40)),
                                     background_normal="", background_color=hex_rgba(th["ok"], 0.2),
                                     color=hex_rgba(th["ok"]), font_size=fs(11))
                restore_btn.bind(on_release=lambda inst, i=hid: self._do_restore(i))
                row_box.add_widget(restore_btn)
            box.add_widget(row_box)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def _do_restore(self, history_id):
        DB.restore_history(history_id)
        self.open_history()

    def open_flag_list(self, field, title):
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar(title, on_back=self.go_back, show_menu=False))
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.flagged_items(field)
        if not rows:
            box.add_widget(Label(text="Liste boş.", size_hint_y=None, height=dph(40),
                                  color=hex_rgba(th["text_secondary"])))
        for row in rows:
            item_id, name = row[0], row[1]
            path = DB.get_path(item_id)
            crumb = " › ".join([p[1] for p in path]) if path else name
            btn = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(44),
                        background_normal="", background_color=hex_rgba(th["surface"]),
                        color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: self.jump_to_item(iid))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def open_move_mode(self):
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Taşınma Modu (Koli No)", on_back=self.go_back, show_menu=False))
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(Label(text="Kutuların 'Düzenle' ekranından bir Koli No girin;\nburada numaraya göre listelenir.",
                             size_hint_y=None, height=dph(50), font_size=fs(12),
                             color=hex_rgba(th["text_secondary"])))
        c = DB.conn.cursor()
        c.execute(f"SELECT {DB.ITEM_COLS} FROM items WHERE move_no > 0 ORDER BY move_no")
        rows = c.fetchall()
        if not rows:
            box.add_widget(Label(text="Henüz koli numarası atanmamış.", size_hint_y=None, height=dph(40),
                                 color=hex_rgba(th["text_secondary"])))
        for row in rows:
            item_id, name, move_no = row[0], row[1], row[13]
            btn = Button(text=f"Koli #{move_no} — {name}", size_hint_y=None, height=dph(44),
                        background_normal="", background_color=hex_rgba(th["surface"]),
                        color=hex_rgba(th["text"]), font_size=fs(13), halign="left")
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: self.jump_to_item(iid))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def do_export_csv(self):
        try:
            path = DB.export_csv()
            self._show_message("Dışa Aktarıldı",
                f"Dosya kaydedildi:\n{path}\n\nBu dosya uygulamanın kendi özel "
                f"klasöründe. Bir dosya yöneticisi uygulamasıyla telefonun "
                f"Android/data/{{paket adı}}/files/ altından erişebilirsiniz.")
        except Exception as e:
            self._show_message("Hata", str(e))

    def _show_message(self, title, text):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(16))
        msg = Label(text=text, font_size=fs(13), color=hex_rgba(th["text"]),
                   halign="left", valign="top", size_hint_y=None)
        msg.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        msg.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(msg)
        close = Button(text="TAMAM", size_hint_y=None, height=dph(46), background_normal="",
                      background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1), font_size=fs(14))
        popup = self.open_auto_popup(title, box, buttons_row=close)
        close.bind(on_release=lambda *a: popup.dismiss())


    def open_add_room_dialog(self, edit_room_id=None):
        th = self.theme()
        self._managed_inputs = []
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text="Odayı Düzenle" if edit_room_id else "Yeni Oda Ekle",
                             size_hint_y=None, height=dph(28), bold=True, font_size=fs(16)))
        field = TextInput(hint_text="Oda adı (örn: Salon, Mutfak)", multiline=False,
                          size_hint_y=None, height=dph(46), font_size=fs(15))
        self.fix_focus(field)
        box.add_widget(field)

        self._selected_room_type = "diger"
        type_btn = Button(text=ROOM_TYPES["diger"][0], size_hint_y=None, height=dph(46),
                          background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15),
                          color=hex_rgba(th["text"]), font_size=fs(14))
        dropdown = DropDown()
        for key in ROOM_TYPE_ORDER:
            label, color, abbr = ROOM_TYPES[key]
            item = Button(text=label, size_hint_y=None, height=dph(42),
                         background_normal="", background_color=hex_rgba(th["surface"]),
                         color=hex_rgba(th["text"]), font_size=fs(13))
            item.bind(on_release=lambda btn, k=key, lb=label: dropdown.select((k, lb)))
            dropdown.add_widget(item)

        def on_select(instance, value):
            key, label = value
            self._selected_room_type = key
            type_btn.text = label
        dropdown.bind(on_select=on_select)
        type_btn.bind(on_release=dropdown.open)
        box.add_widget(type_btn)

        def on_field_text(inst, value):
            guess = infer_room_type(value)
            if guess != "diger":
                self._selected_room_type = guess
                type_btn.text = ROOM_TYPES[guess][0]
        field.bind(text=on_field_text)

        if edit_room_id:
            existing = DB.get_room(edit_room_id)
            if existing:
                _rid, rname, rtype, remoji, rphoto = existing
                field.text = rname
                self._selected_room_type = rtype
                type_btn.text = ROOM_TYPES.get(rtype, ROOM_TYPES["diger"])[0]

        btn_row = self.styled_popup_buttons(lambda: popup.dismiss(), lambda *a: save(), "KAYDET" if edit_room_id else "EKLE")
        popup = self.open_auto_popup("", box, buttons_row=btn_row)

        def save(*a):
            name = field.text.strip()
            if not name:
                return
            if edit_room_id:
                DB.update_room(edit_room_id, name, self._selected_room_type)
            else:
                DB.add_room(name, self._selected_room_type)
            popup.dismiss()
            self.refresh_home()

    def open_edit_room_dialog(self, room_id):
        self.open_add_room_dialog(edit_room_id=room_id)

    def _confirm_delete_room(self, room_id, name):
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text=f"'{name}' odası ve içindeki tüm eşyalar silinsin mi?", font_size=fs(14)))

        def do_delete(*a):
            DB.delete_room(room_id)
            popup.dismiss()
            self.refresh_home()

        btn_row = self.styled_popup_buttons(lambda: popup.dismiss(), do_delete, "SİL")
        popup = self.open_auto_popup("Odayı Sil", box, buttons_row=btn_row, scrollable=False)

    def _confirm_empty_box(self, item_id, name):
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text=f"'{name}' içindeki tüm öğeler bir üst seviyeye taşınsın mı?", font_size=fs(14)))

        def do_empty(*a):
            DB.empty_box(item_id)
            popup.dismiss()
            self._render_room()

        btn_row = self.styled_popup_buttons(lambda: popup.dismiss(), do_empty, "BOŞALT")
        popup = self.open_auto_popup("Kutuyu Boşalt", box, buttons_row=btn_row, scrollable=False)

    def open_move_dialog(self, item_id):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(14))
        box.add_widget(Label(text="Hangi odaya taşınsın?", size_hint_y=None, height=dph(28), bold=True,
                             font_size=fs(15), color=hex_rgba(th["text"])))
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        inner.bind(minimum_height=inner.setter("height"))
        popup_holder = {}

        for rid, rname, rtype, remoji, rphoto in DB.get_rooms():
            b = Button(text=rname, size_hint_y=None, height=dph(42),
                      background_normal="", background_color=hex_rgba(th["surface"]),
                      color=hex_rgba(th["text"]), font_size=fs(13))

            def do_move(inst, target_room=rid):
                DB.move_item(item_id, target_room, None)
                popup_holder["p"].dismiss()
                self.nav_stack = [(target_room, None, DB.get_room(target_room)[1], DB.get_room(target_room)[1])]
                self._render_room()

            b.bind(on_release=do_move)
            inner.add_widget(b)
        box.add_widget(inner)
        cancel = Button(text="İPTAL", size_hint_y=None, height=dph(44), background_normal="",
                        background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]),
                        font_size=fs(14))
        popup = self.open_auto_popup("Eşyayı Taşı", box, buttons_row=cancel)
        popup_holder["p"] = popup
        cancel.bind(on_release=lambda *a: popup.dismiss())

    def open_add_item_dialog(self, edit_id=None):
        th = self.theme()
        self._managed_inputs = []
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(14), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        box.add_widget(Label(text="Eşyayı Düzenle" if edit_id else "Yeni Eşya Ekle",
                             size_hint_y=None, height=dph(30), bold=True, font_size=fs(16)))

        def field(hint, h=dp(46)):
            t = TextInput(hint_text=hint, multiline=False, size_hint_y=None, height=h, font_size=fs(14))
            self.fix_focus(t)
            box.add_widget(t)
            return t

        name_field = field("Eşya adı (örn: Kanepe, Kutu)")

        self._selected_category = ITEM_CATEGORIES[-1]
        cat_btn = Button(text=self._selected_category, size_hint_y=None, height=dph(46),
                         background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15),
                         color=hex_rgba(th["text"]), font_size=fs(14))
        dropdown = DropDown()
        for cat in ITEM_CATEGORIES:
            item = Button(text=cat, size_hint_y=None, height=dph(40),
                         background_normal="", background_color=hex_rgba(th["surface"]),
                         color=hex_rgba(th["text"]), font_size=fs(13))
            item.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(item)
        cat_btn.bind(on_release=dropdown.open)

        def on_select(instance, value):
            self._selected_category = value
            cat_btn.text = value
        dropdown.bind(on_select=on_select)
        box.add_widget(cat_btn)

        note_field = field("Not (isteğe bağlı)")
        price_field = field("Fiyat / değer (TL, isteğe bağlı)")
        price_field.input_filter = "float"
        expiry_field = field("Son kullanma / garanti tarihi (GG.AA.YYYY, isteğe bağlı)")
        loaned_field = field("Ödünç verildiyse kime (isteğe bağlı)")
        qty_row = BoxLayout(size_hint_y=None, height=dph(46), spacing=dp(6))
        qty_field = self.fix_focus(TextInput(hint_text="Miktar", multiline=False, font_size=fs(14), input_filter="int"))
        qty_min_field = self.fix_focus(TextInput(hint_text="Min. stok uyarısı", multiline=False, font_size=fs(14), input_filter="int"))
        qty_row.add_widget(qty_field)
        qty_row.add_widget(qty_min_field)
        box.add_widget(qty_row)
        tags_field = field("Etiketler (virgülle, örn: kışlık,kırılacak)")
        move_field = field("Taşınma koli no (isteğe bağlı)")
        move_field.input_filter = "int"

        chk_row = BoxLayout(size_hint_y=None, height=dph(46), spacing=dp(8))

        def make_toggle_chip(label_text, active_color):
            btn = Button(text=label_text, font_size=fs(12), bold=True,
                        background_normal="", color=(1, 1, 1, 1))
            btn.active = False
            inactive_c = hex_rgba(th["text_secondary"], 0.18)
            active_c = hex_rgba(active_color, 0.9)
            btn.background_color = inactive_c

            def apply_visual(inst):
                inst.background_color = active_c if inst.active else inactive_c
                inst.color = (1, 1, 1, 1) if inst.active else hex_rgba(th["text"])

            def toggle(inst):
                inst.active = not inst.active
                apply_visual(inst)
            btn.color = hex_rgba(th["text"])
            btn.bind(on_release=toggle)
            btn.set_active = lambda value, inst=btn: (setattr(inst, "active", value), apply_visual(inst))
            return btn

        fav_chk = make_toggle_chip("Favori", th["warn"])
        sell_chk = make_toggle_chip("Satılık", th["ok"])
        lost_chk = make_toggle_chip("Kayıp", th["danger"])
        chk_row.add_widget(fav_chk)
        chk_row.add_widget(sell_chk)
        chk_row.add_widget(lost_chk)
        box.add_widget(chk_row)

        code_lbl = Label(text="", size_hint_y=None, height=dph(20), font_size=fs(11),
                         color=hex_rgba(th["text_secondary"]))
        box.add_widget(code_lbl)

        if edit_id:
            item = DB.get_item(edit_id)
            if item:
                (_id, nm, cat, note, price, expiry, loaned_to, qty, qty_min, tags,
                 is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = item
                name_field.text = nm
                self._selected_category = cat
                cat_btn.text = cat
                note_field.text = note or ""
                price_field.text = str(price) if price else ""
                expiry_field.text = expiry or ""
                loaned_field.text = loaned_to or ""
                qty_field.text = str(qty) if qty else ""
                qty_min_field.text = str(qty_min) if qty_min else ""
                tags_field.text = tags or ""
                move_field.text = str(move_no) if move_no else ""
                fav_chk.set_active(bool(is_fav))
                sell_chk.set_active(bool(is_sell))
                lost_chk.set_active(bool(is_lost))
                code_lbl.text = f"Kod: {code}"

        def save(*a):
            name = name_field.text.strip()
            if not name:
                return
            room_id, parent_id, _, _ = self.nav_stack[-1]
            kw = dict(
                price=float(price_field.text) if price_field.text.strip() else 0,
                expiry=expiry_field.text.strip(),
                loaned_to=loaned_field.text.strip(),
                qty=int(qty_field.text) if qty_field.text.strip() else 0,
                qty_min=int(qty_min_field.text) if qty_min_field.text.strip() else 0,
                tags=tags_field.text.strip(),
                is_favorite=fav_chk.active,
                is_sell=sell_chk.active,
                is_lost=lost_chk.active,
                move_no=int(move_field.text) if move_field.text.strip() else 0,
            )
            if edit_id:
                DB.update_item(edit_id, name, self._selected_category, note_field.text.strip(), **kw)
            else:
                DB.add_item(room_id, parent_id, name, self._selected_category, note_field.text.strip(), **kw)
            popup.dismiss()
            self._render_room()

        btn_row = self.styled_popup_buttons(lambda: popup.dismiss(), lambda *a: save(), "KAYDET")
        popup = self.open_auto_popup("", box, buttons_row=btn_row)

    def open_edit_item_dialog(self, item_id):
        self.open_add_item_dialog(edit_id=item_id)

    def _confirm_delete_item(self, item_id, name):
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        path = breadcrumb + "  ›  " + name
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text=f"'{name}' silinsin mi?\n(İçindeki eşyalar da silinir, Geçmiş'ten geri getirilebilir)",
                             font_size=fs(13)))

        def do_delete(*a):
            DB.delete_item(item_id, path)
            popup.dismiss()
            self._render_room()

        btn_row = self.styled_popup_buttons(lambda: popup.dismiss(), do_delete, "SİL")
        popup = self.open_auto_popup("Eşyayı Sil", box, buttons_row=btn_row, scrollable=False)


if __name__ == "__main__":
    EvimApp().run()
