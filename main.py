# -*- coding: utf-8 -*-
"""
EVİM - Ev Eşya Envanteri Uygulaması (Tam Stabil & Çökme Korumalı)
"""

import os
import csv
import json
import datetime
import shutil
import math
import uuid

from kivy.app import App
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
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
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.utils import platform, get_color_from_hex
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line, PushMatrix, PopMatrix, Rotate

import sqlite3

try:
    from plyer import camera
except Exception:
    camera = None

try:
    from PIL import Image as PILImage, ExifTags
except ImportError:
    PILImage = None

# ---------------------------------------------------------------------------
# Sabitler & Yollar
# ---------------------------------------------------------------------------

def get_evim_dir():
    """Ana Evim klasörünü oluşturur, izin hatası olursa Download içine açar."""
    if platform == "android":
        base = "/storage/emulated/0/Evim"
        try:
            if not os.path.exists(base):
                os.makedirs(base)
            return base
        except Exception:
            fallback = "/storage/emulated/0/Download/Evim"
            if not os.path.exists(fallback):
                try: os.makedirs(fallback)
                except: pass
            return fallback
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Evim")
        if not os.path.exists(base):
            try: os.makedirs(base)
            except: pass
        return base

def get_photo_dir():
    """Fotograflari tutacagimiz klasor (Evim/Fotograflar)"""
    p_dir = os.path.join(get_evim_dir(), "Fotograflar")
    if not os.path.exists(p_dir):
        try: os.makedirs(p_dir)
        except: pass
    return p_dir

def get_db_path():
    """Veritabanı çalışma yolu (Eski yerinde kalması veri güvenliği için şarttır, yedekler Evim klasörüne alınır)"""
    if platform == "android":
        from android.storage import app_storage_path
        base = app_storage_path()
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "evim.db")

def get_settings_path():
    return os.path.join(os.path.dirname(get_db_path()), "ayarlar.txt")

def get_download_path():
    return get_evim_dir()

def fix_image_orientation(image_path):
    """Görüntünün EXIF verisine bakar ve yan/ters çekilmişse fiziksel olarak düzeltir."""
    if not PILImage:
        return
    try:
        with PILImage.open(image_path) as img:
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                orientation = None
                for k, v in ExifTags.TAGS.items():
                    if v == 'Orientation':
                        orientation = k
                        break
                if orientation is not None and orientation in exif:
                    o_val = exif[orientation]
                    if o_val in (3, 6, 8):
                        if o_val == 3:
                            img = img.rotate(180, expand=True)
                        elif o_val == 6:
                            img = img.rotate(270, expand=True)
                        elif o_val == 8:
                            img = img.rotate(90, expand=True)
                        img.save(image_path)
    except Exception:
        pass

def migrate_old_photos():
    """Önceki sürümlerde eklenen eski fotoğrafları yeni Evim/Fotograflar klasörüne güvenle taşır."""
    try:
        if platform == "android":
            from android.storage import app_storage_path
            old_p_dir = os.path.join(app_storage_path(), "photos")
        else:
            old_p_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")
        
        new_p_dir = get_photo_dir()
        if os.path.exists(old_p_dir):
            for f in os.listdir(old_p_dir):
                old_f = os.path.join(old_p_dir, f)
                new_f = os.path.join(new_p_dir, f)
                if not os.path.exists(new_f):
                    shutil.move(old_f, new_f)
    except Exception:
        pass

def load_settings():
    try:
        with open(get_settings_path(), "r", encoding="utf-8") as f:
            data = f.read().strip()
            if data.startswith('{'):
                return json.loads(data)
            else:
                return {"font_scale": float(data), "theme": "orijinal"}
    except Exception:
        return {"font_scale": 3.25, "theme": "orijinal"}

def save_settings(font_scale, theme):
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            json.dump({"font_scale": font_scale, "theme": theme}, f)
    except Exception:
        pass


ROOM_TYPES = {
    "mutfak":     ("Mutfak",            "#FF7043", "MTF"),
    "yatak":      ("Yatak Odası",       "#5C6BC0", "YTK"),
    "salon":      ("Salon",             "#26A69A", "SLN"),
    "banyo":      ("Banyo",             "#29B6F6", "BNY"),
    "calisma":    ("Çalışma Odası",     "#8D6E63", "OFS"),
    "bilgisayar": ("Bilgisayar Odası",  "#7E57C2", "BLG"),
    "cocuk":      ("Çocuk Odası",       "#EC407A", "ÇCK"),
    "garaj":      ("Garaj",             "#78909C", "GRJ"),
    "bahce":      ("Bahçe",             "#66BB6A", "BHÇ"),
    "depo":       ("Depo/Kiler",        "#8D8D57", "DPO"),
    "koridor":    ("Koridor",           "#607D8B", "KRD"),
    "misafir":    ("Misafir Odası",     "#26C6DA", "MSF"),
    "camasir":    ("Çamaşır Odası",     "#42A5F5", "ÇMR"),
    "balkon":     ("Balkon/Teras",      "#8BC34A", "BLK"),
    "diger":      ("Diğer",             "#FF6F3C", "DĞR"),
}

ROOM_TYPE_ORDER = list(ROOM_TYPES.keys())

CATEGORY_INFO = {
    "Elektronik":       ("#4A90E2", "ELK"),
    "Mobilya":          ("#A88771", "MBL"),
    "Giyim":            ("#E85D8D", "GYM"),
    "Kitap/Kırtasiye":  ("#8E6CD4", "KTP"),
    "Mutfak Eşyası":    ("#F27B55", "MTF"),
    "Dekorasyon":       ("#39B5A8", "DKR"),
    "Belge":            ("#748A96", "BLG"),
    "Diğer":            ("#A3A3A3", "DĞR"),
}
ITEM_CATEGORIES = list(CATEGORY_INFO.keys())
UNIT_TYPES = ["Adet", "Kutu", "Kg", "Litre", "Paket", "Çuval", "Şişe"]

THEMES = {
    "orijinal": {
        "name": "Orijinal Turuncu",
        "bg": "#15131F", "surface": "#211E2E", "surface2": "#2A2640", "text": "#F2F0FA",
        "text_secondary": "#9C97B8", "primary": "#FF7A50", "accent": "#7C6CFF",
        "danger": "#FF6B6B", "warn": "#F2C14E", "ok": "#4FD8A0"
    },
    "gece_mavisi": {
        "name": "Gece Mavisi",
        "bg": "#12111A", "surface": "#1E1C29", "surface2": "#2C2A3D", "text": "#FDFCFE",
        "text_secondary": "#9C97B8", "primary": "#6B5B95", "accent": "#B8A9C9",
        "danger": "#D9534F", "warn": "#F0AD4E", "ok": "#5CB85C"
    },
    "zumrut": {
        "name": "Zümrüt Yeşili",
        "bg": "#0D1A15", "surface": "#162A22", "surface2": "#234034", "text": "#F0F5F2",
        "text_secondary": "#8EA69B", "primary": "#20B27A", "accent": "#45D49E",
        "danger": "#E05A5A", "warn": "#F5B041", "ok": "#4CAF50"
    },
    "okyanus": {
        "name": "Okyanus",
        "bg": "#0B1521", "surface": "#13253A", "surface2": "#1C3754", "text": "#E8F0F8",
        "text_secondary": "#829AB1", "primary": "#3A86FF", "accent": "#6FB1FF",
        "danger": "#FF5A5F", "warn": "#FFCA3A", "ok": "#8AC926"
    },
    "yakut": {
        "name": "Yakut Kırmızısı",
        "bg": "#1A0B0F", "surface": "#291319", "surface2": "#3D1D26", "text": "#F8E8EB",
        "text_secondary": "#B1828D", "primary": "#D92546", "accent": "#F55C7A",
        "danger": "#FF4D4D", "warn": "#F9C80E", "ok": "#8CB369"
    },
    "ametist": {
        "name": "Ametist (Mor)",
        "bg": "#140D1A", "surface": "#23162E", "surface2": "#342245", "text": "#F4E8FA",
        "text_secondary": "#A88EBF", "primary": "#9D4EDD", "accent": "#C77DFF",
        "danger": "#EF476F", "warn": "#FFD166", "ok": "#06D6A0"
    },
    "gunbatimi": {
        "name": "Gün Batımı",
        "bg": "#1A1311", "surface": "#2E201B", "surface2": "#453028", "text": "#FAEEEA",
        "text_secondary": "#BFA59C", "primary": "#F4A261", "accent": "#E76F51",
        "danger": "#E63946", "warn": "#E9C46A", "ok": "#2A9D8F"
    },
    "orman": {
        "name": "Orman",
        "bg": "#111713", "surface": "#1A241D", "surface2": "#26362B", "text": "#EBF2EC",
        "text_secondary": "#91A696", "primary": "#4C956C", "accent": "#2C6E49",
        "danger": "#D62828", "warn": "#F77F00", "ok": "#606C38"
    },
    "kahve": {
        "name": "Kahve / Krem",
        "bg": "#171412", "surface": "#26211D", "surface2": "#3B332E", "text": "#F2EBE6",
        "text_secondary": "#B3A298", "primary": "#A98467", "accent": "#6C584C",
        "danger": "#BC4749", "warn": "#E9C46A", "ok": "#386641"
    },
    "minimal": {
        "name": "Minimal Siyah",
        "bg": "#0D0D0D", "surface": "#1A1A1A", "surface2": "#262626", "text": "#F2F2F2",
        "text_secondary": "#808080", "primary": "#999999", "accent": "#FFFFFF",
        "danger": "#FF6666", "warn": "#FFCC66", "ok": "#99CC99"
    },
    "lavanta": {
        "name": "Lavanta",
        "bg": "#1D1929", "surface": "#2B263B", "surface2": "#3B3552", "text": "#F4EEFF",
        "text_secondary": "#B5A8D1", "primary": "#A071E5", "accent": "#B892FF",
        "danger": "#F15BB5", "warn": "#FEE440", "ok": "#00BBF9"
    },
    "karanlik_orman": {
        "name": "Karanlık Orman",
        "bg": "#0B120C", "surface": "#121E15", "surface2": "#1A2E20", "text": "#E8F0E9",
        "text_secondary": "#7D9984", "primary": "#2D6A4F", "accent": "#40916C",
        "danger": "#D90429", "warn": "#F4A261", "ok": "#52B788"
    },
    "pastel_gul": {
        "name": "Pastel Gül",
        "bg": "#211618", "surface": "#332226", "surface2": "#4A3238", "text": "#FFE8ED",
        "text_secondary": "#D4A5AF", "primary": "#E56B6F", "accent": "#F59295",
        "danger": "#C9184A", "warn": "#FFB703", "ok": "#8CB369"
    },
    "buzul": {
        "name": "Buzul",
        "bg": "#0A1118", "surface": "#12202E", "surface2": "#1D3247", "text": "#EBF4FA",
        "text_secondary": "#8FA9C2", "primary": "#48CAE4", "accent": "#90E0EF",
        "danger": "#FF4D6D", "warn": "#FFC300", "ok": "#06D6A0"
    },
    "altin_gece": {
        "name": "Altın Gece",
        "bg": "#121212", "surface": "#1E1E1E", "surface2": "#2C2C2C", "text": "#F5F5F5",
        "text_secondary": "#A1A1A1", "primary": "#D4AF37", "accent": "#FFD700",
        "danger": "#D62828", "warn": "#F77F00", "ok": "#2A9D8F"
    },
    "kizil_kum": {
        "name": "Kızıl Kum",
        "bg": "#17100E", "surface": "#291B17", "surface2": "#3D2A24", "text": "#F7EBE8",
        "text_secondary": "#C4A79D", "primary": "#D95D39", "accent": "#F07B58",
        "danger": "#C42021", "warn": "#F2A65A", "ok": "#5B8E7D"
    },
    "nane": {
        "name": "Nane Ferahlığı",
        "bg": "#0F1A1B", "surface": "#182B2D", "surface2": "#234042", "text": "#EBF5F6",
        "text_secondary": "#8DABB0", "primary": "#2A9D8F", "accent": "#48B8A9",
        "danger": "#E76F51", "warn": "#F4A261", "ok": "#2DC653"
    },
    "gece_yarisi": {
        "name": "Gece Yarısı",
        "bg": "#050505", "surface": "#111111", "surface2": "#1A1A1A", "text": "#FFFFFF",
        "text_secondary": "#666666", "primary": "#4A4A4A", "accent": "#808080",
        "danger": "#FF3333", "warn": "#FF9933", "ok": "#33CC33"
    },
    "retro_neon": {
        "name": "Retro Neon",
        "bg": "#120B29", "surface": "#201347", "surface2": "#2D1D63", "text": "#F0EBFF",
        "text_secondary": "#A999D6", "primary": "#F72585", "accent": "#B5179E",
        "danger": "#EF476F", "warn": "#FFD166", "ok": "#06D6A0"
    },
    "mavi_celik": {
        "name": "Mavi Çelik",
        "bg": "#0B1014", "surface": "#151F26", "surface2": "#21303B", "text": "#E2EDF8",
        "text_secondary": "#7A93A6", "primary": "#3A506B", "accent": "#5C7A99",
        "danger": "#E63946", "warn": "#F4A261", "ok": "#2A9D8F"
    }
}

def infer_room_type(name):
    n = name.lower()
    table = [
        ("mutfak", "mutfak"), ("yatak", "yatak"), ("salon", "salon"),
        ("banyo", "banyo"), ("tuvalet", "banyo"), ("çalışma", "calisma"),
        ("ofis", "calisma"), ("bilgisayar", "bilgisayar"), ("oyun", "bilgisayar"),
        ("çocuk", "cocuk"), ("bebek", "cocuk"), ("garaj", "garaj"),
        ("bahçe", "bahce"), ("depo", "depo"), ("kiler", "depo"), ("ambar", "depo"),
        ("koridor", "koridor"), ("antre", "koridor"), ("hol", "koridor"),
        ("misafir", "misafir"), ("çamaşır", "camasir"), ("balkon", "balkon"), ("teras", "balkon"),
    ]
    for kw, key in table:
        if kw in n:
            return key
    return "diger"

def hex_rgba(hex_color, alpha=1.0):
    r = get_color_from_hex(hex_color)
    return [r[0], r[1], r[2], alpha]

DEFAULT_FONT_SCALE = 3.25

def fs(base):
    app = App.get_running_app()
    scale = app.font_scale if app else DEFAULT_FONT_SCALE
    return base * scale

def dph(base):
    app = App.get_running_app()
    scale = app.font_scale if app else DEFAULT_FONT_SCALE
    factor = scale / DEFAULT_FONT_SCALE
    return dp(base * max(0.8, factor))

def now_str():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

# ---------------------------------------------------------------------------
# Veritabanı Katmanı
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
            "unit": "TEXT DEFAULT 'Adet'",
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
                     is_sell, is_lost, move_no, emoji, photo_path, unit)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (room_id, parent_id, name, category, note,
                   kw.get("price", 0), kw.get("expiry", ""), kw.get("loaned_to", ""),
                   kw.get("qty", 0), kw.get("qty_min", 0), kw.get("tags", ""),
                   int(kw.get("is_favorite", False)), int(kw.get("is_sell", False)),
                   int(kw.get("is_lost", False)), kw.get("move_no", 0), kw.get("emoji", ""),
                   kw.get("photo_path", ""), kw.get("unit", "Adet")))
        new_id = c.lastrowid
        c.execute("UPDATE items SET code=? WHERE id=?", (f"K-{new_id:04d}", new_id))
        self.conn.commit()
        return new_id

    def update_item(self, item_id, name, category, note, **kw):
        c = self.conn.cursor()
        c.execute("""UPDATE items SET name=?, category=?, note=?, price=?, expiry=?,
                     loaned_to=?, qty=?, qty_min=?, tags=?, is_favorite=?, is_sell=?,
                     is_lost=?, move_no=?, emoji=?, photo_path=?, unit=? WHERE id=?""",
                  (name, category, note, kw.get("price", 0), kw.get("expiry", ""),
                   kw.get("loaned_to", ""), kw.get("qty", 0), kw.get("qty_min", 0),
                   kw.get("tags", ""), int(kw.get("is_favorite", False)),
                   int(kw.get("is_sell", False)), int(kw.get("is_lost", False)),
                   kw.get("move_no", 0), kw.get("emoji", ""), kw.get("photo_path", ""), 
                   kw.get("unit", "Adet"), item_id))
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
        parent_id = item[16]
        c = self.conn.cursor()
        c.execute("UPDATE items SET parent_id=? WHERE parent_id=?", (parent_id, item_id))
        self.conn.commit()

    ITEM_COLS = "id,name,category,note,price,expiry,loaned_to,qty,qty_min,tags,is_favorite,is_sell,is_lost,move_no,code,room_id,parent_id,emoji,photo_path,unit"

    def get_items(self, room_id, parent_id, sort_order="id ASC", search_query=""):
        c = self.conn.cursor()
        query = f"SELECT {self.ITEM_COLS} FROM items WHERE room_id=?"
        params = [room_id]
        
        if parent_id is None:
            query += " AND parent_id IS NULL"
        else:
            query = f"SELECT {self.ITEM_COLS} FROM items WHERE parent_id=?"
            params = [parent_id]
            
        if search_query:
            query += " AND (lower(name) LIKE ? OR lower(tags) LIKE ?)"
            sq = f"%{search_query.lower()}%"
            params.extend([sq, sq])
            
        query += f" ORDER BY {sort_order}"
        c.execute(query, params)
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
                "unit": item[19] if len(item) > 19 else "Adet"
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
                      is_sell=data["is_sell"], is_lost=data["is_lost"], move_no=data["move_no"],
                      unit=data.get("unit", "Adet"))
        c.execute("DELETE FROM history WHERE id=?", (history_id,))
        self.conn.commit()
        return True

    def _log_history(self, kind, name, path_text, restore_data):
        c = self.conn.cursor()
        c.execute("INSERT INTO history (kind, item_name, path_text, deleted_at, restore_data) VALUES (?,?,?,?,?)",
                  (kind, name, path_text, now_str(), json.dumps(restore_data) if restore_data else ""))
        self.conn.commit()

    def get_history(self):
        c = self.conn.cursor()
        c.execute("SELECT id, kind, item_name, path_text, deleted_at, restore_data FROM history ORDER BY id DESC LIMIT 200")
        return c.fetchall()

    def empty_history(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM history")
        self.conn.commit()

    def search(self, query):
        q = f"%{query.lower()}%"
        c = self.conn.cursor()
        c.execute(f"""SELECT {self.ITEM_COLS} FROM items
                     WHERE lower(name) LIKE ? OR lower(tags) LIKE ? OR lower(note) LIKE ?
                     ORDER BY id LIMIT 60""", (q, q, q))
        return c.fetchall()
        
    def filter_by_category(self, category):
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE category=? ORDER BY id DESC", (category,))
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

    def get_low_stock_items(self):
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items WHERE qty_min > 0 AND qty <= qty_min ORDER BY id")
        return c.fetchall()

    def export_csv(self):
        rooms = {r[0]: r[1] for r in self.get_rooms()}
        dl_dir = get_download_path()
        path = os.path.join(dl_dir, "evim_envanter.csv")
        c = self.conn.cursor()
        c.execute(f"SELECT {self.ITEM_COLS} FROM items ORDER BY room_id, id")
        rows = c.fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Oda", "Eşya", "Kategori", "Not", "Fiyat", "Miktar", "Birim", "Min Stok", "Etiketler", "Kod"])
            for row in rows:
                room_name = rooms.get(row[15], "?")
                unit_val = row[19] if len(row) > 19 else "Adet"
                w.writerow([room_name, row[1], row[2], row[3], row[4], row[7], unit_val, row[8], row[9], row[14]])
        return path

DB = Database()

# ---------------------------------------------------------------------------
# Özel Görsel Bileşenler (Custom Widgets)
# ---------------------------------------------------------------------------

class TrackedDropDown(DropDown):
    def open(self, widget):
        app = App.get_running_app()
        if app:
            if getattr(app, '_active_dropdowns', None) is None:
                app._active_dropdowns = []
            if self not in app._active_dropdowns:
                app._active_dropdowns.append(self)
        super().open(widget)

    def dismiss(self, *largs, **kwargs):
        app = App.get_running_app()
        if app and getattr(app, '_active_dropdowns', None) is not None:
            if self in app._active_dropdowns:
                app._active_dropdowns.remove(self)
        super().dismiss(*largs, **kwargs)

class CustomSpinner(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.scale = 1
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=0, origin=self.center)
            Color(*hex_rgba(THEMES["orijinal"]["primary"]))
            self.line = Line(circle=(self.center_x, self.center_y, dp(24), 0, 270), width=dp(3))
        with self.canvas.after:
            PopMatrix()
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_interval(self.animate, 1/60)

    def update_canvas(self, *args):
        self.rot.origin = self.center
        self.line.circle = (self.center_x, self.center_y, dp(24) * self.scale, 0, 270)

    def animate(self, dt):
        self.angle = (self.angle - 6) % 360
        self.rot.angle = self.angle
        self.scale = 1 + 0.1 * math.sin(math.radians(self.angle * 2))
        self.update_canvas()

class SoftShadowCard(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, 0, 0.15)
            self._shadow_dark = RoundedRectangle(radius=[dp(16)])
            Color(1, 1, 1, 0.02)
            self._shadow_light = RoundedRectangle(radius=[dp(16)])
            self._main_color = Color(rgba=self.bg_color)
            self._rect = RoundedRectangle(radius=[dp(16)])
            
        self.bind(pos=self._update_rect, size=self._update_rect, bg_color=self._update_color)

    def _update_rect(self, *a):
        self._shadow_dark.pos = (self.x - dp(1), self.y - dp(2))
        self._shadow_dark.size = (self.width + dp(2), self.height + dp(3))
        self._shadow_light.pos = (self.x + dp(1), self.y + dp(1))
        self._shadow_light.size = (self.width - dp(1), self.height - dp(1))
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *a):
        self._main_color.rgba = self.bg_color

class ClickableCard(ButtonBehavior, SoftShadowCard):
    pass

class ClickableLabel(ButtonBehavior, Label):
    pass

def _star_points(cx, cy, r_outer, r_inner, rotation=90):
    pts = []
    for i in range(10):
        angle = math.radians(rotation + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append(cx + r * math.cos(angle))
        pts.append(cy + r * math.sin(angle))
    return pts

class RoomIcon(RelativeLayout):
    bg_color = ListProperty([1, 1, 1, 1])
    icon_key = StringProperty("diger")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, bg_color=self._redraw, icon_key=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        w, h = self.width, self.height
        if w <= 0 or h <= 0:
            return
        
        with self.canvas:
            Color(rgba=self.bg_color)
            RoundedRectangle(pos=(0, 0), size=(w, h), radius=[dp(16), dp(16), 0, 0])
            box_size = min(w, h) * 0.62
            bx = (w - box_size) / 2
            by = (h - box_size) / 2
            bw = bh = box_size
            lw = max(dp(2.2), bh * 0.06)
            key = self.icon_key
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

class _ClickableRoomIcon(ButtonBehavior, RoomIcon):
    pass

class TopBar(BoxLayout):
    bar_color = ListProperty([1, 1, 1, 1])
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.padding = (dp(14), 0)
        self.spacing = dp(6)
        with self.canvas.before:
            self._color = Color(rgba=self.bar_color)
            self._rect = RoundedRectangle(radius=[0, 0, dp(12), dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect, bar_color=self._update_color)

    def _update_rect(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *a):
        self._color.rgba = self.bar_color

class IconBtn(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        kw.setdefault("size_hint", (None, 1))
        kw.setdefault("valign", "middle")
        kw.setdefault("halign", "left")
        super().__init__(**kw)
        self.font_size = fs(15)
        self.bind(size=lambda w, *a: setattr(w, "text_size", w.size))

class RoundActionButton(ButtonBehavior, Label):
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
        kw.setdefault("height", dph(18))
        kw.setdefault("font_size", fs(9))
        kw.setdefault("bold", True)
        kw.setdefault("color", (1, 1, 1, 1))
        kw.setdefault("padding", (dp(6), dp(2)))
        super().__init__(**kw)
        self.bind(texture_size=self._resize)
        self._bg = bg
        with self.canvas.before:
            self._color = Color(*hex_rgba(bg))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _resize(self, *a):
        self.width = self.texture_size[0] + dp(12)
    def _update_rect(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

class FAB(ButtonBehavior, Label):
    bg_color = ListProperty([1, 1, 1, 1])
    def __init__(self, **kw):
        bg = kw.pop("bg_color", [1,1,1,1])
        super().__init__(**kw)
        self.bg_color = bg
        with self.canvas.before:
            self._color = Color(rgba=self.bg_color)
            self._ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update, bg_color=self._update_color)
        self.bind(size=lambda w, *a: setattr(w, "text_size", w.size))

    def _update(self, *a):
        self._ellipse.pos = self.pos
        self._ellipse.size = self.size
    def _update_color(self, *a):
        self._color.rgba = self.bg_color

class LoadingScreen(Screen):
    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'home'), 1.0)

class HomeScreen(Screen): pass
class RoomScreen(Screen): pass
class InfoScreen(Screen): pass

class EvimApp(App):
    guest_mode = BooleanProperty(False)
    font_scale = NumericProperty(DEFAULT_FONT_SCALE)
    current_theme = StringProperty("orijinal")
    nav_stack = []
    _active_popup = None
    
    multi_select_mode = BooleanProperty(False)
    selected_items = set()
    current_room_sort = "id ASC"
    current_room_search = ""

    def theme(self):
        return THEMES.get(self.current_theme, THEMES["orijinal"])

    def build(self):
        self.title = "Evim"
        self._active_dropdowns = []
        
        migrate_old_photos()
        
        settings = load_settings()
        self.font_scale = settings["font_scale"]
        self.current_theme = settings["theme"]
        
        Window.clearcolor = hex_rgba(self.theme()["bg"])
        Window.bind(on_keyboard=self._on_keyboard)
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        
        ls = LoadingScreen(name="loading")
        fl = FloatLayout()
        fl.add_widget(CustomSpinner(pos_hint={'center_x': 0.5, 'center_y': 0.5}))
        ls.add_widget(fl)
        self.sm.add_widget(ls)
        
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(RoomScreen(name="room"))
        self.sm.add_widget(InfoScreen(name="info"))
        self.refresh_home()
        
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES, Permission.CAMERA])
            except Exception:
                pass
            
            try:
                from jnius import autoclass
                StrictMode = autoclass('android.os.StrictMode')
                builder = autoclass('android.os.StrictMode$VmPolicy$Builder')()
                StrictMode.setVmPolicy(builder.build())
            except Exception:
                pass

        self.sm.current = "loading"
        return self.sm

    def open_photo_chooser(self, callback):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(10))
        
        start_path = "/storage/emulated/0"
        if platform == "android":
            dcim_path = "/storage/emulated/0/DCIM"
            if os.path.exists(dcim_path):
                start_path = dcim_path
        else:
            start_path = os.path.expanduser("~")
            
        fc = FileChooserListView(path=start_path, filters=["*.png", "*.jpg", "*.jpeg", "*.webp"])
        box.add_widget(fc)
        
        btn_row = BoxLayout(size_hint_y=None, height=dph(46), spacing=dp(10))
        cancel = Button(text="İPTAL", background_normal="", background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]), font_size=fs(14))
        select = Button(text="SEÇ", background_normal="", background_color=hex_rgba(th["primary"]), color=(1,1,1,1), font_size=fs(14), bold=True)
        
        btn_row.add_widget(cancel)
        btn_row.add_widget(select)
        box.add_widget(btn_row)
        
        popup = Popup(title="Dosya Seç", content=box, size_hint=(0.95, 0.95), background="", background_color=hex_rgba(th["bg"]), title_color=hex_rgba(th["text"]))
        
        def on_select(*a):
            if fc.selection:
                callback(fc.selection[0])
                popup.dismiss()
            else:
                self._show_message("Uyarı", "Lütfen listeden bir fotoğraf seçip 'SEÇ'e basın.")
                
        select.bind(on_release=on_select)
        cancel.bind(on_release=lambda *a: popup.dismiss())
        
        popup.open()

    def close_popup(self, *args):
        if getattr(self, '_active_popup', None):
            try:
                self._active_popup.dismiss()
            except Exception:
                pass
            self._active_popup = None

    def _on_keyboard(self, window, key, *args):
        if key == 27:
            if getattr(self.sm.transition, 'is_active', False):
                return True
            if getattr(self, '_active_dropdowns', None):
                for dd in list(self._active_dropdowns):
                    try: dd.dismiss()
                    except: pass
                self._active_dropdowns = []
                return True
            if getattr(self, '_active_popup', None):
                self.close_popup()
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
        title_lbl = Label(text="Yazı Boyutu", size_hint_y=None, bold=True, font_size=fs(16), color=hex_rgba(th["text"]))
        title_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        title_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(title_lbl)
        desc_lbl = Label(text="0 = varsayılan boyut. Eksi küçültür, artı büyütür.", size_hint_y=None, font_size=fs(11), color=hex_rgba(th["text_secondary"]))
        desc_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        desc_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(desc_lbl)
        preview = Label(text="Örnek Yazı Aa", size_hint_y=None, height=dph(50), font_size=fs(16), color=hex_rgba(th["text"]))
        box.add_widget(preview)
        current_pct = (self.font_scale / DEFAULT_FONT_SCALE - 1.0) * 200.0
        current_pct = max(-100, min(100, current_pct))
        slider = Slider(min=-100, max=100, value=current_pct, step=1, size_hint_y=None, height=dph(40))
        box.add_widget(slider)
        pct_lbl = Label(text=f"{int(round(current_pct)):+d}", size_hint_y=None, height=dph(26), font_size=fs(13), color=hex_rgba(th["text_secondary"]))
        box.add_widget(pct_lbl)
        def pct_to_scale(pct):
            return DEFAULT_FONT_SCALE * (1.0 + (pct / 200.0))
        def on_slide(instance, value):
            pct_lbl.text = f"{int(round(value)):+d}"
            preview.font_size = 16 * (pct_to_scale(value) / DEFAULT_FONT_SCALE)
        slider.bind(value=on_slide)
        btn_row = BoxLayout(size_hint_y=None, height=dph(50), spacing=dp(10))
        cancel = Button(text="İPTAL", background_normal="", background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]))
        ok = Button(text="UYGULA", background_normal="", background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1), bold=True)
        btn_row.add_widget(cancel)
        btn_row.add_widget(ok)
        self.open_auto_popup("", box, buttons_row=btn_row, scrollable=False)
        def apply_and_close(*a):
            self.font_scale = pct_to_scale(slider.value)
            save_settings(self.font_scale, self.current_theme)
            self.close_popup()
            Clock.schedule_once(lambda dt: self._refresh_current(), 0.3)
        cancel.bind(on_release=lambda *a: self.close_popup())
        ok.bind(on_release=apply_and_close)

    def open_theme_dialog(self):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(16))
        lbl = Label(text="Renk Teması Seç", size_hint_y=None, bold=True, font_size=fs(16), color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for t_key, t_data in THEMES.items():
            btn = Button(text=t_data["name"], size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(t_data["surface"]), color=hex_rgba(t_data["primary"]), font_size=fs(12), bold=True)
            def set_theme(inst, k=t_key):
                self.current_theme = k
                save_settings(self.font_scale, self.current_theme)
                self.close_popup()
                Clock.schedule_once(lambda dt: self._refresh_current(), 0.3)
            btn.bind(on_release=set_theme)
            grid.add_widget(btn)
        box.add_widget(grid)
        close = Button(text="İPTAL", size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(14))
        self.open_auto_popup("", box, buttons_row=close)
        close.bind(on_release=lambda *a: self.close_popup())

    def _refresh_current(self):
        Window.clearcolor = hex_rgba(self.theme()["bg"])
        cur = self.sm.current
        if cur == "home":
            self.refresh_home()
        elif cur == "room":
            self._render_room()

    def make_topbar(self, title, on_back=None, show_menu=True):
        th = self.theme()
        bar_h = dph(46)
        bar = TopBar(bar_color=hex_rgba(th["primary"]), height=bar_h)
        if on_back:
            back = IconBtn(text="<", font_size=fs(20), color=(1, 1, 1, 1), size_hint_x=None, width=dph(40))
            back.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: on_back(), 0.1))
            bar.add_widget(back)
        lbl = Label(text=title, bold=True, font_size=fs(15), color=(1, 1, 1, 1), halign="left", valign="middle", shorten=True, size_hint_y=1)
        lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        bar.add_widget(lbl)
        if getattr(self, 'multi_select_mode', False) and self.sm.current == "room":
            sel_btn = Button(text="Vazgeç", size_hint=(None, None), size=(dph(60), bar_h), background_normal="", background_color=(0,0,0,0), color=(1,1,1,1), font_size=fs(11), bold=True)
            sel_btn.bind(on_release=lambda *a: self.toggle_multi_select())
            bar.add_widget(sel_btn)
        if self.guest_mode:
            bar.add_widget(Label(text="MİSAFİR", font_size=fs(9), color=(1, 1, 1, 0.8), size_hint=(None, None), size=(dph(56), bar_h)))
        if show_menu:
            menu_btn = IconBtn(text="Menü", font_size=fs(14), bold=True, color=(1, 1, 1, 1), size_hint_x=None, width=dph(50))
            menu_btn.bind(on_release=lambda *a: self.open_main_menu(menu_btn))
            bar.add_widget(menu_btn)
        return bar

    def open_main_menu(self, caller):
        if getattr(self, '_main_menu_dd', None):
            self._main_menu_dd.dismiss()
        th = self.theme()
        dropdown = TrackedDropDown(auto_width=False, width=dph(260))
        self._main_menu_dd = dropdown
        entries = [
            ("Ana ekrana dön / Ara", self.go_home),
            ("Sık Kullanılanlar", lambda: self.open_flag_list("is_favorite", "Sık Kullanılanlar")),
            ("Alışveriş / Eksik Listesi", self.open_shopping_list),
            ("Satılık / Bağış Listesi", lambda: self.open_flag_list("is_sell", "Satılık / Bağış Listesi")),
            ("Kayıp Eşyalar", lambda: self.open_flag_list("is_lost", "Kayıp Eşyalar")),
            ("Taşınma Modu", self.open_move_mode),
            ("Yedekle / Dışa Aktar", self.open_backup_menu),
            ("Renk Temaları", self.open_theme_dialog),
            ("Silinenler Geçmişi", self.open_history),
            ("Yazı Boyutu Ayarı", self.open_font_size_dialog),
            ("Misafir Modu Aç/Kapat", self.toggle_guest),
        ]
        for label, fn in entries:
            btn = Button(text=label, size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left")
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            def make_cb(f):
                def cb(*a):
                    dropdown.dismiss()
                    Clock.schedule_once(lambda dt: f(), 0.1)
                return cb
            btn.bind(on_release=make_cb(fn))
            dropdown.add_widget(btn)
        dropdown.open(caller)

    def open_backup_menu(self):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(16))
        lbl = Label(text="Yedekleme ve Aktarma", size_hint_y=None, bold=True, font_size=fs(16), color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def act(txt, cb):
            b = RoundActionButton(text=txt, size_hint_y=None, height=dph(44), font_size=fs(13), bold=True, bg_color=hex_rgba(th["primary"], 0.2), color=hex_rgba(th["primary"]))
            b.bind(on_release=lambda *a: (self.close_popup(), Clock.schedule_once(lambda dt: cb(), 0.15)))
            return b
        box.add_widget(act("CSV Olarak Dışa Aktar", self.do_export_csv))
        box.add_widget(act("Tam Veritabanı Yedeği Al (.db)", self.do_backup_db))
        box.add_widget(act("Yedekten Geri Yükle", self.do_restore_db))
        close = Button(text="İPTAL", size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(14))
        self.open_auto_popup("", box, buttons_row=close)
        close.bind(on_release=lambda *a: self.close_popup())

    def do_backup_db(self):
        try:
            dl_dir = get_download_path()
            backup_path = os.path.join(dl_dir, "evim_yedek.db")
            shutil.copy(get_db_path(), backup_path)
            self._show_message("Başarılı", f"Veritabanı yedeği güvenle alındı:\n\n{backup_path}")
        except Exception as e:
            self._show_message("Hata", f"Yedekleme başarısız: {str(e)}")

    def do_restore_db(self):
        dl_dir = get_download_path()
        backup_path = os.path.join(dl_dir, "evim_yedek.db")
        if not os.path.exists(backup_path):
            self._show_message("Hata", f"Yedek dosyası bulunamadı:\n{backup_path}")
            return
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text="Mevcut evim.db silinip, kayıtlı yedek yüklenecek. Onaylıyor musunuz?", font_size=fs(14), size_hint_y=None, color=hex_rgba(self.theme()["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def proceed(*a):
            try:
                shutil.copy(backup_path, get_db_path())
                global DB
                DB = Database()
                self.close_popup()
                Clock.schedule_once(lambda dt: self.go_home(), 0.15)
                self._show_message("Başarılı", "Yedek başarıyla geri yüklendi.")
            except Exception as e:
                self.close_popup()
                self._show_message("Hata", f"Geri yükleme başarısız: {str(e)}")
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), proceed, "YÜKLE")
        self.open_auto_popup("Yedekten Dön", box, buttons_row=btn_row, scrollable=False)

    def go_home(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        self.nav_stack = []
        self.multi_select_mode = False
        self.selected_items = set()
        self.current_room_search = ""
        self.refresh_home()
        self.sm.transition = SlideTransition(direction="right")
        self.sm.current = "home"

    _managed_inputs = []

    def fix_focus(self, text_input):
        text_input.keyboard_suggestions = False
        self._managed_inputs.append(text_input)
        def on_touch_down(instance, touch):
            if instance.collide_point(*touch.pos):
                for other in list(self._managed_inputs):
                    if other is not instance:
                        try: other.focus = False
                        except: pass
                Clock.schedule_once(lambda dt: setattr(instance, "focus", True), 0.03)
                Clock.schedule_once(lambda dt: setattr(instance, "focus", True), 0.15)
            return False
        text_input.bind(on_touch_down=on_touch_down)
        return text_input

    def themed_box(self, **kw):
        th = self.theme()
        box = BoxLayout(**kw)
        with box.canvas.before:
            Color(rgba=hex_rgba(th["surface"]))
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(16)])
        def _update(inst, *a):
            rect.pos = inst.pos
            rect.size = inst.size
        box.bind(pos=_update, size=_update)
        return box

    def open_auto_popup(self, title, inner_box, buttons_row=None, max_frac=0.94, scrollable=True):
        self.close_popup()
        th = self.theme()
        inner_box.size_hint_y = None
        inner_box.bind(minimum_height=inner_box.setter("height"))
        outer = self.themed_box(orientation="vertical")
        if scrollable:
            scroll = ScrollView(size_hint=(1, 1), bar_width=dp(3), do_scroll_x=False, do_scroll_y=True)
            scroll.add_widget(inner_box)
            outer.add_widget(scroll)
        else:
            outer.add_widget(inner_box)
        if buttons_row is not None:
            outer.add_widget(buttons_row)
        popup = Popup(title=title, content=outer, size_hint=(0.92, None), height=dp(200), separator_height=(dp(1) if title else 0), background="", background_color=hex_rgba(th["bg"]), title_color=hex_rgba(th["text"]))
        self._active_popup = popup
        def resize(*a):
            btn_h = buttons_row.height if buttons_row is not None else 0
            title_h = dp(50) if title else 0
            total = inner_box.height + btn_h + title_h + dp(50)
            if self._active_popup:
                self._active_popup.height = min(total, Window.height * max_frac)
        inner_box.bind(minimum_height=lambda *a: resize())
        if buttons_row is not None and hasattr(buttons_row, "bind"):
            try: buttons_row.bind(minimum_height=lambda *a: resize())
            except: pass
            buttons_row.bind(height=lambda *a: resize())
        Clock.schedule_once(lambda dt: resize(), 0)
        Clock.schedule_once(lambda dt: resize(), 0.1)
        def on_dismiss(*a):
            if self._active_popup is popup:
                self._active_popup = None
        popup.bind(on_dismiss=on_dismiss)
        popup.open()
        return popup

    def styled_popup_buttons(self, cancel_cb, confirm_cb, confirm_text="KAYDET"):
        th = self.theme()
        row = BoxLayout(size_hint_y=None, height=dph(50), spacing=dp(10), padding=(dp(4), dp(4)))
        cancel = Button(text="İPTAL", background_normal="", background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]), font_size=fs(14))
        cancel.bind(on_release=lambda *a: cancel_cb())
        ok = Button(text=confirm_text, background_normal="", background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1), font_size=fs(14), bold=True)
        ok.bind(on_release=lambda *a: confirm_cb())
        row.add_widget(cancel)
        row.add_widget(ok)
        return row

    def badges_for_item(self, row, th):
        badges = []
        (_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags, is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo, unit) = row
        if is_fav: badges.append(("Favori", th["warn"]))
        if loaned_to: badges.append((f"Ödünç: {loaned_to}", th["primary"]))
        if is_sell: badges.append(("Satılık", th["ok"]))
        if is_lost: badges.append(("Kayıp", th["danger"]))
        if qty_min and qty <= qty_min: badges.append(("Stok Azaldı", th["danger"]))
        if expiry:
            try:
                try: d = datetime.datetime.strptime(expiry, "%d/%m/%Y")
                except ValueError: d = datetime.datetime.strptime(expiry, "%d.%m.%Y")
                delta = (d - datetime.datetime.now()).days
                if delta < 0: badges.append(("Süresi Doldu", th["danger"]))
                elif delta <= 7: badges.append((f"{delta}g kaldı", th["warn"]))
            except: pass
        return badges

    def add_floating_action_menu(self, root_layout, context="home"):
        th = self.theme()
        fab_container = RelativeLayout(size_hint=(None, None), size=(dph(70), dph(220)), pos_hint={"right": 0.96, "y": 0.03})
        
        btn_opts = []
        if context == "home":
            btn_opts = [("Oda Ekle", self.open_add_room_dialog)]
        else:
            btn_opts = [("Eşya Ekle", self.open_add_item_dialog), ("Kutu Ekle", lambda: self.open_add_item_dialog(is_box=True))]
            
        sub_btns = []
        for i, (txt, cb) in enumerate(btn_opts):
            b = RoundActionButton(text=txt, size_hint=(None, None), size=(dph(90), dph(38)), pos=(dph(-20), dph(10)), opacity=0,
                                  bg_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(11), bold=True)
            def btn_cb(inst, f=cb):
                toggle_fab()
                Clock.schedule_once(lambda dt: f(), 0.1)
            b.bind(on_release=btn_cb)
            sub_btns.append(b)
            fab_container.add_widget(b)

        main_fab = FAB(text="+", size_hint=(None, None), size=(dph(54), dph(54)), pos=(dph(8), 0), bg_color=hex_rgba(th["primary"]))
            
        fab_container.is_expanded = False
        def toggle_fab(*a):
            fab_container.is_expanded = not fab_container.is_expanded
            if fab_container.is_expanded:
                main_fab.text = "×"
                for i, b in enumerate(sub_btns):
                    Animation(y=dph(60 + i*46), opacity=1, d=0.1 + i*0.05, t='out_bounce').start(b)
            else:
                main_fab.text = "+"
                for b in sub_btns:
                    Animation(y=dph(10), opacity=0, d=0.1).start(b)

        main_fab.bind(on_release=toggle_fab)
        fab_container.add_widget(main_fab)
        root_layout.add_widget(fab_container)

    def refresh_home(self):
        th = self.theme()
        screen = self.sm.get_screen("home")
        screen.clear_widgets()
        root = FloatLayout()
        main_col = BoxLayout(orientation="vertical")
        main_col.add_widget(self.make_topbar("EVİM"))
        search_row = BoxLayout(size_hint_y=None, height=dph(40), padding=(dp(14), dp(2)))
        self._search_input = TextInput(hint_text="Eşyalarınızda arayın...", multiline=False, font_size=fs(12), padding=(dp(12), dp(8)),
                                       background_color=hex_rgba(th["surface2"]), foreground_color=hex_rgba(th["text"]),
                                       hint_text_color=hex_rgba(th["text_secondary"]), cursor_color=hex_rgba(th["primary"]), keyboard_suggestions=False)
        self._search_input.bind(text=self._on_search_text)
        search_row.add_widget(self._search_input)
        main_col.add_widget(search_row)
        self._results_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self._results_box.bind(minimum_height=self._results_box.setter("height"))
        main_col.add_widget(self._results_box)
        home_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=(0, dp(6), 0, dp(90)))
        content.bind(minimum_height=content.setter("height"))
        lbl_cat = Label(text="Kategoriler", size_hint_y=None, height=dph(20), font_size=fs(13), bold=True, color=hex_rgba(th["text_secondary"]), halign="left", valign="middle")
        lbl_cat.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(36), None)))
        content.add_widget(lbl_cat)
        cat_grid = GridLayout(cols=4, spacing=dp(6), padding=(dp(14), 0), size_hint_y=None)
        cat_grid.bind(minimum_height=cat_grid.setter("height"))
        for cat in ITEM_CATEGORIES:
            cb = Button(text=cat.replace(" ", "\n").replace("/", "/\n"), size_hint_y=None, height=dph(36), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(10), halign="center", valign="middle")
            cb.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(4), w.height - dp(4))))
            cb.bind(on_release=lambda inst, c=cat: Clock.schedule_once(lambda dt: self.open_category_filter(c), 0.1))
            cat_grid.add_widget(cb)
        content.add_widget(cat_grid)
        lbl_rooms = Label(text="Odalar", size_hint_y=None, height=dph(20), font_size=fs(15), bold=True, color=hex_rgba(th["text"]), halign="left", valign="middle")
        lbl_rooms.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(36), None)))
        content.add_widget(lbl_rooms)
        rooms = DB.get_rooms()
        grid_cols = 1 if len(rooms) == 1 else 2
        grid = GridLayout(cols=grid_cols, spacing=dp(14), padding=(dp(14), 0, dp(14), 0), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for rid, name, rtype, remoji, rphoto in rooms:
            grid.add_widget(self._make_room_card(rid, name, rtype, remoji, rphoto))
        content.add_widget(grid)
        home_scroll.add_widget(content)
        main_col.add_widget(home_scroll)
        root.add_widget(main_col)
        if not self.guest_mode:
            self.add_floating_action_menu(root, context="home")
        screen.add_widget(root)

    def _on_search_text(self, instance, value):
        self._results_box.clear_widgets()
        value = value.strip()
        if len(value) < 2:
            return
        th = self.theme()
        results = DB.search(value)
        if not results:
            self._results_box.add_widget(Label(text="Sonuç bulunamadı.", size_hint_y=None, height=dph(36), color=hex_rgba(th["text_secondary"])))
            return
        for row in results:
            item_id, name = row[0], row[1]
            path = DB.get_path(item_id)
            crumb = " › ".join([DB.get_room(row[15])[1]] + [p[1] for p in path[:-1]] + [name]) if path else name
            b = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(42), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            b.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            b.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            self._results_box.add_widget(b)

    def jump_to_item(self, item_id):
        if getattr(self.sm.transition, 'is_active', False):
            return
        path = DB.get_path(item_id)
        if not path: return
        room_id = path[0][15]
        room = DB.get_room(room_id)
        room_name = room[1] if room else "?"
        stack = [(room_id, None, room_name, room_name)]
        crumb = room_name
        for row in path:
            crumb = crumb + "  ›  " + row[1]
            stack.append((room_id, row[0], row[1], crumb))
        self.nav_stack = stack
        self.current_room_search = ""
        self.multi_select_mode = False
        self.selected_items = set()
        self._render_room()
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "room"

    def _make_room_card(self, room_id, name, room_type, emoji="", photo_path=""):
        th = self.theme()
        label, color, abbr = ROOM_TYPES.get(room_type, ROOM_TYPES["diger"])
        card = ClickableCard(orientation="vertical", size_hint=(1, None), padding=0, spacing=0, bg_color=hex_rgba(th["surface"]))
        card.bind(minimum_height=card.setter("height"))
        card.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.open_room_detail(room_id, name, room_type), 0.1))
        cover = _ClickableRoomIcon(size_hint_y=None, height=dph(60), bg_color=hex_rgba(color), icon_key=room_type)
        cover.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.enter_room(room_id, name), 0.1))
        card.add_widget(cover)
        body = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(8), dp(6)), spacing=dp(2))
        body.bind(minimum_height=body.setter("height"))
        name_lbl = ClickableLabel(text=name, color=hex_rgba(th["text"]), bold=True, font_size=fs(14), size_hint_y=None, height=dph(20), shorten=True, halign="center", valign="middle")
        name_lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        name_lbl.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.enter_room(room_id, name), 0.1))
        body.add_widget(name_lbl)
        item_count = len(DB.get_items(room_id, None))
        sub = Label(text=f"{item_count} eşya", font_size=fs(10), color=hex_rgba(th["text_secondary"]), size_hint_y=None, height=dph(14))
        body.add_widget(sub)
        card.add_widget(body)
        return card

    def open_room_detail(self, room_id, name, room_type):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(16))
        t_lbl = Label(text=name, font_size=fs(18), bold=True, color=hex_rgba(th["text"]), size_hint_y=None)
        t_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        t_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(t_lbl)
        item_count = len(DB.get_items(room_id, None))
        s_lbl = Label(text=f"{item_count} eşya  ·  {ROOM_TYPES.get(room_type, ROOM_TYPES['diger'])[0]}", font_size=fs(13), color=hex_rgba(th["text_secondary"]), size_hint_y=None)
        s_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        s_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(s_lbl)
        actions = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        actions.bind(minimum_height=actions.setter("height"))
        def act_btn(text, color_key, cb):
            b = RoundActionButton(text=text, size_hint_y=None, height=dph(44), font_size=fs(13), bold=True, bg_color=hex_rgba(th[color_key], 0.18), color=hex_rgba(th[color_key]))
            b.bind(on_release=lambda *a: (self.close_popup(), Clock.schedule_once(lambda dt: cb(), 0.15)))
            return b
        actions.add_widget(act_btn("Aç / İçine Gir", "primary", lambda: self.enter_room(room_id, name)))
        if not self.guest_mode:
            actions.add_widget(act_btn("Düzenle", "text_secondary", lambda: self.open_edit_room_dialog(room_id)))
            actions.add_widget(act_btn("Sil", "danger", lambda: self._confirm_delete_room(room_id, name)))
        self.open_auto_popup("", box, buttons_row=actions)

    def enter_room(self, room_id, name):
        if getattr(self.sm.transition, 'is_active', False):
            return
        self.nav_stack = [(room_id, None, name, name)]
        self.current_room_search = ""
        self.current_room_sort = "id ASC"
        self.multi_select_mode = False
        self.selected_items = set()
        self._render_room()
        self.sm.transition = RiseInTransition(duration=0.28)
        self.sm.current = "room"

    def toggle_multi_select(self):
        self.multi_select_mode = not self.multi_select_mode
        self.selected_items = set()
        Clock.schedule_once(lambda dt: self._render_room(), 0.05)

    def do_batch_move(self):
        if not self.selected_items: return
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(14))
        box.add_widget(Label(text=f"{len(self.selected_items)} eşya nereye taşınsın?", size_hint_y=None, height=dph(30), bold=True, color=hex_rgba(th["text"])))
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        inner.bind(minimum_height=inner.setter("height"))
        for rid, rname, rtype, remoji, rphoto in DB.get_rooms():
            b = Button(text=rname, size_hint_y=None, height=dph(42), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]))
            def do_move(inst, target_room=rid):
                for iid in self.selected_items:
                    DB.move_item(iid, target_room, None)
                self.close_popup()
                Clock.schedule_once(lambda dt: self._cleanup_multi_select(), 0.15)
            b.bind(on_release=do_move)
            inner.add_widget(b)
        box.add_widget(inner)
        cancel = Button(text="İPTAL", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]))
        self.open_auto_popup("Toplu Taşı", box, buttons_row=cancel)
        cancel.bind(on_release=lambda *a: self.close_popup())

    def do_batch_delete(self):
        if not self.selected_items: return
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text=f"Seçilen {len(self.selected_items)} eşya tamamen silinecek. Onaylıyor musunuz?", font_size=fs(14), size_hint_y=None, color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def confirm(*a):
            for iid in self.selected_items:
                DB.delete_item(iid, "Toplu Silim")
            self.close_popup()
            Clock.schedule_once(lambda dt: self._cleanup_multi_select(), 0.15)
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), confirm, "SİL")
        self.open_auto_popup("Toplu Sil", box, buttons_row=btn_row, scrollable=False)
        
    def _cleanup_multi_select(self):
        self.multi_select_mode = False
        self.selected_items = set()
        self._render_room()

    def _render_room(self):
        th = self.theme()
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        screen = self.sm.get_screen("room")
        screen.clear_widgets()
        root = FloatLayout()
        
        main_col = BoxLayout(orientation="vertical")
        main_col.add_widget(self.make_topbar(title, on_back=self.go_back))
        info_row = BoxLayout(size_hint_y=None, height=dph(34), padding=(dp(14), 0), spacing=dp(8))
        crumb = Label(text=breadcrumb, font_size=fs(12), color=hex_rgba(th["text_secondary"]), halign="left", valign="middle", shorten=True)
        crumb.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        info_row.add_widget(crumb)
        total = DB.item_value_sum(room_id, parent_id)
        if total:
            total_lbl = Label(text=f"Toplam: {total:.0f} TL", font_size=fs(12), bold=True, color=hex_rgba(th["primary"]), size_hint_x=None)
            total_lbl.bind(texture_size=lambda w, val: setattr(w, "width", val[0] + dp(8)))
            info_row.add_widget(total_lbl)
            
        main_col.add_widget(info_row)
        tools_row = BoxLayout(size_hint_y=None, height=dph(34), padding=(dp(10), dp(2)), spacing=dp(6))
        search_inp = TextInput(text=self.current_room_search, hint_text="Odada ara...", multiline=False, font_size=fs(11), padding=(dp(8), dp(6)),
                               background_color=hex_rgba(th["surface2"]), foreground_color=hex_rgba(th["text"]), hint_text_color=hex_rgba(th["text_secondary"]), keyboard_suggestions=False)
        
        self._search_event = None
        def on_room_search(inst, val):
            self.current_room_search = val.strip()
            if self._search_event: self._search_event.cancel()
            self._search_event = Clock.schedule_once(lambda dt: self._render_room(), 0.3)
        search_inp.bind(text=on_room_search)
        tools_row.add_widget(search_inp)
        
        multi_btn = Button(text="Toplu Seç", size_hint_x=None, width=dph(75), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(11))
        multi_btn.bind(on_release=lambda *a: self.toggle_multi_select())
        tools_row.add_widget(multi_btn)

        sort_btn = Button(text="Sırala", size_hint_x=None, width=dph(55), background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(11))
        sort_dd = TrackedDropDown(auto_width=False, width=dph(180))
        for s_txt, s_val in [("Tarih (Eski-Yeni)", "id ASC"), ("Tarih (Yeni-Eski)", "id DESC"), ("A-Z (İsim)", "name ASC"), ("Fiyat (Yüksek-Düşük)", "price DESC")]:
            b = Button(text=s_txt, size_hint_y=None, height=dph(40), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(11))
            b.bind(on_release=lambda btn, v=s_val: sort_dd.select(v))
            sort_dd.add_widget(b)
        sort_btn.bind(on_release=lambda btn: sort_dd.open(btn))
        def on_sort_select(inst, val):
            self.current_room_sort = val
            Clock.schedule_once(lambda dt: self._render_room(), 0.1)
        sort_dd.bind(on_select=on_sort_select)
        tools_row.add_widget(sort_btn)
        main_col.add_widget(tools_row)

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        items = DB.get_items(room_id, parent_id, sort_order=self.current_room_sort, search_query=self.current_room_search)
        
        grid = GridLayout(cols=2, spacing=dp(14), padding=(dp(14), dp(6), dp(14), dp(130)), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        
        if not items:
            empty = Label(text="Eşya bulunamadı.", color=hex_rgba(th["text_secondary"]), size_hint_y=None, font_size=fs(14))
            empty.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(60)))
            grid.add_widget(empty)
            
        for row in items:
            grid.add_widget(self._make_item_card(row))
        scroll.add_widget(grid)
        main_col.add_widget(scroll)

        if self.multi_select_mode:
            batch_bar = BoxLayout(size_hint_y=None, height=dph(50), padding=dp(8), spacing=dp(10))
            with batch_bar.canvas.before:
                Color(*hex_rgba(th["surface2"]))
                bg_rect = RoundedRectangle(radius=[dp(12)])
            def _update_bg_safe(inst, val):
                bg_rect.pos = inst.pos
                bg_rect.size = inst.size
            batch_bar.bind(pos=_update_bg_safe, size=_update_bg_safe)
            lbl_sel = Label(text=f"{len(self.selected_items)} seçildi", color=hex_rgba(th["text"]), bold=True, font_size=fs(13))
            batch_bar.add_widget(lbl_sel)
            if self.selected_items:
                btn_move = Button(text="Taşı", background_normal="", background_color=hex_rgba(th["primary"]), color=(1,1,1,1), bold=True)
                btn_move.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.do_batch_move(), 0.15))
                btn_del = Button(text="Sil", background_normal="", background_color=hex_rgba(th["danger"]), color=(1,1,1,1), bold=True)
                btn_del.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.do_batch_delete(), 0.15))
                batch_bar.add_widget(btn_move)
                batch_bar.add_widget(btn_del)
            main_col.add_widget(batch_bar)

        root.add_widget(main_col)

        if not self.guest_mode and not self.multi_select_mode:
            self.add_floating_action_menu(root, context="room")

        screen.add_widget(root)

    def _make_item_card(self, row):
        th = self.theme()
        if len(row) > 19:
            (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
             is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo, unit) = row
        else:
            (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
             is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = row
            unit = "Adet"

        child_count = DB.count_children(item_id)

        card = ClickableCard(orientation="vertical", size_hint=(1, None), padding=(dp(12), dp(8), dp(8), dp(8)), spacing=dp(4), bg_color=hex_rgba(th["surface"]))
        card.bind(minimum_height=card.setter("height"))
        cat_color, _cat_abbr = CATEGORY_INFO.get(category, CATEGORY_INFO["Diğer"])
        with card.canvas.after:
            Color(rgba=hex_rgba(cat_color))
            _accent = RoundedRectangle(radius=[dp(16), 0, 0, dp(16)])
        def _update_accent(inst, *a):
            _accent.pos = (inst.x, inst.y)
            _accent.size = (dp(5), inst.height)
        card.bind(pos=_update_accent, size=_update_accent)
        name_row = BoxLayout(size_hint_y=None, height=dph(24), spacing=dp(6))
        
        if self.multi_select_mode:
            chk = CheckBox(size_hint_x=None, width=dph(30), color=hex_rgba(th["primary"]))
            chk.active = item_id in self.selected_items
            def on_chk(inst, val):
                if val: self.selected_items.add(item_id)
                else: self.selected_items.discard(item_id)
                Clock.schedule_once(lambda dt: self._render_room(), 0.05)
            chk.bind(active=on_chk)
            name_row.add_widget(chk)

        title = name + (f" ({child_count})" if child_count else "")
        name_lbl = Button(text=title, color=hex_rgba(th["text"]), font_size=fs(14), bold=True, halign="left", valign="middle", shorten=True, background_normal="", background_color=(0,0,0,0))
        name_lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        
        if child_count > 0 and not self.multi_select_mode:
            expand_btn = IconBtn(text="▼", size_hint=(None, None), size=(dph(24), dph(24)), color=hex_rgba(th["text_secondary"]))
            name_row.add_widget(expand_btn)
            inner_box = BoxLayout(orientation='vertical', size_hint_y=None, height=0, opacity=0, spacing=dp(4), padding=(dp(10), dp(4), 0, 0))
            card.is_expanded = False
            def toggle_accordion(*a):
                if card.is_expanded:
                    Animation(height=0, opacity=0, d=0.15).start(inner_box)
                    expand_btn.text = "▼"
                else:
                    if not inner_box.children:
                        for c_row in DB.get_items(room_id, item_id, sort_order="id ASC", search_query=""):
                            l = Label(text=f"• {c_row[1]}", size_hint_y=None, height=dph(20), font_size=fs(12), color=hex_rgba(th["text_secondary"]), halign="left")
                            l.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
                            inner_box.add_widget(l)
                    target_h = len(inner_box.children) * dph(24) + dp(8)
                    Animation(height=target_h, opacity=1, d=0.15).start(inner_box)
                    expand_btn.text = "▲"
                card.is_expanded = not card.is_expanded
            name_lbl.bind(on_release=toggle_accordion)
            expand_btn.bind(on_release=toggle_accordion)
        else:
            name_lbl.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.enter_item(item_id, name), 0.1) if not self.multi_select_mode else None)
            
        name_row.add_widget(name_lbl)
        info_dot = Button(text="?", font_size=fs(11), bold=True, color=hex_rgba(th["text_secondary"]), size_hint=(None, None), size=(dph(22), dph(22)), background_normal="", background_color=(0,0,0,0))
        info_dot.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.open_item_detail(row), 0.1) if not self.multi_select_mode else None)
        with info_dot.canvas.before:
            Color(rgba=hex_rgba(th["surface2"]))
            _dot_rect = Ellipse(pos=info_dot.pos, size=info_dot.size)
        info_dot.bind(pos=lambda w, *a: setattr(_dot_rect, "pos", w.pos), size=lambda w, *a: setattr(_dot_rect, "size", w.size))
        if not self.multi_select_mode:
            name_row.add_widget(info_dot)
            
        card.add_widget(name_row)
        badge_scroll = ScrollView(size_hint_y=None, height=dph(22), do_scroll_x=True, do_scroll_y=False, bar_width=0)
        badge_row = BoxLayout(size_hint=(None, 1), spacing=dp(4))
        badge_row.bind(minimum_width=badge_row.setter("width"))
        badges = self.badges_for_item(list(row) + ["Adet"] * (20 - len(row)), th)
        for text, color in badges[:3]:
            badge_row.add_widget(Badge(text=text, bg=color))
        badge_scroll.add_widget(badge_row)
        card.add_widget(badge_scroll)
        
        if child_count > 0 and not self.multi_select_mode:
            card.add_widget(inner_box)

        return card

    def open_item_detail(self, row):
        th = self.theme()
        if len(row) > 19:
            (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
             is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo, unit) = row
        else:
            (item_id, name, category, note, price, expiry, loaned_to, qty, qty_min, tags,
             is_fav, is_sell, is_lost, move_no, code, room_id, parent_id, item_emoji, item_photo) = row
            unit = "Adet"
             
        child_count = DB.count_children(item_id)
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(16))
        t_lbl = Label(text=name, font_size=fs(18), bold=True, color=hex_rgba(th["text"]), size_hint_y=None)
        t_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        t_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(t_lbl)

        if item_photo:
            full_path = os.path.join(get_photo_dir(), item_photo)
            if os.path.exists(full_path):
                img_box = BoxLayout(size_hint_y=None, height=dph(180), padding=(0, dp(8)))
                img = Image(source=full_path, allow_stretch=True, keep_ratio=True)
                img_box.add_widget(img)
                box.add_widget(img_box)

        lbl_hex = "".join(f"{int(c*255):02X}" for c in hex_rgba(th["text_secondary"])[:3])
        val_hex = "".join(f"{int(c*255):02X}" for c in hex_rgba(th["text"])[:3])
        def field_line(label, value):
            return f"[b][color={lbl_hex}]{label}:[/color][/b] [color={val_hex}]{value}[/color]"

        info_lines = [field_line("Kategori", category)]
        if note: info_lines.append(field_line("Not", note))
        if price: info_lines.append(field_line("Değer", f"{price:.0f} TL"))
        if expiry: info_lines.append(field_line("Son kul./garanti", expiry))
        if loaned_to: info_lines.append(field_line("Ödünç", loaned_to))
        if qty: info_lines.append(field_line("Miktar", f"{qty} {unit}" + (f" (Min: {qty_min})" if qty_min else "")))
        if tags: info_lines.append(field_line("Etiketler", tags))
        if move_no: info_lines.append(field_line("Koli no", str(move_no)))
        if child_count: info_lines.append(field_line("İçindeki öğe", str(child_count)))
        flags = []
        if is_fav: flags.append("Favori")
        if is_sell: flags.append("Satılık")
        if is_lost: flags.append("Kayıp")
        if flags: info_lines.append(field_line("İşaret", ", ".join(flags)))

        info_lbl = Label(text="\n".join(info_lines), font_size=fs(13), markup=True, halign="left", valign="top", size_hint_y=None)
        info_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        info_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(info_lbl)

        actions = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        actions.bind(minimum_height=actions.setter("height"))
        def act_btn(text, color_key, cb):
            b = RoundActionButton(text=text, size_hint_y=None, height=dph(44), font_size=fs(13), bold=True, bg_color=hex_rgba(th[color_key], 0.18), color=hex_rgba(th[color_key]))
            b.bind(on_release=lambda *a: (self.close_popup(), Clock.schedule_once(lambda dt: cb(), 0.15)))
            return b

        actions.add_widget(act_btn("Aç / İçine Gir", "primary", lambda: self.enter_item(item_id, name)))
        if not self.guest_mode:
            actions.add_widget(act_btn("Düzenle", "text_secondary", lambda: self.open_edit_item_dialog(item_id)))
            actions.add_widget(act_btn("Taşı", "text_secondary", lambda: self.open_move_dialog(item_id)))
            if child_count:
                actions.add_widget(act_btn(f"Kutuyu Boşalt ({child_count} öğe)", "text_secondary", lambda: self._confirm_empty_box(item_id, name)))
            actions.add_widget(act_btn("Sil", "danger", lambda: self._confirm_delete_item(item_id, name)))

        self.open_auto_popup("", box, buttons_row=actions, scrollable=False)

    def enter_item(self, item_id, name):
        if getattr(self.sm.transition, 'is_active', False):
            return
        room_id, _, _, breadcrumb = self.nav_stack[-1]
        self.nav_stack.append((room_id, item_id, name, breadcrumb + "  ›  " + name))
        self.current_room_search = ""
        self.current_room_sort = "id ASC"
        self.multi_select_mode = False
        self.selected_items = set()
        self._render_room()
        self.sm.transition = RiseInTransition(duration=0.28)
        self.sm.current = "room"

    def go_back(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        if getattr(self, '_is_going_back', False):
            return
        self._is_going_back = True
        Clock.schedule_once(lambda dt: setattr(self, '_is_going_back', False), 0.35)
        try:
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
            self.sm.transition = FadeTransition(duration=0.15)
            if self.nav_stack:
                self._render_room()
                self.sm.current = "room"
            else:
                self.refresh_home()
                self.sm.current = "home"
        except Exception:
            self.nav_stack = []
            self.refresh_home()
            self.sm.current = "home"

    def _confirm_empty_history(self):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text="Tüm silinenler geçmişi kalıcı olarak tamamen silinecek. Onaylıyor musunuz?", font_size=fs(14), size_hint_y=None, color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def confirm(*a):
            DB.empty_history()
            self.close_popup()
            Clock.schedule_once(lambda dt: self.open_history(), 0.15)
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), confirm, "TEMİZLE")
        self.open_auto_popup("Geçmişi Temizle", box, buttons_row=btn_row, scrollable=False)

    def open_history(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Silinenler Geçmişi", on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.get_history()
        if rows:
            btn_del = Button(text="Geçmişi Tamamen Temizle", size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["danger"]), color=(1,1,1,1), font_size=fs(13), bold=True)
            btn_del.bind(on_release=lambda *a: self._confirm_empty_history())
            box.add_widget(btn_del)
            box.add_widget(Widget(size_hint_y=None, height=dp(4)))
        if not rows:
            empty_lbl = Label(text="Henüz silinen bir şey yok.", size_hint_y=None, font_size=fs(14), color=hex_rgba(th["text_secondary"]))
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for hid, kind, name, path_text, deleted_at, restore_data in rows:
            row_box = SoftShadowCard(orientation="horizontal", size_hint_y=None, height=dph(60), padding=dp(8), spacing=dp(8), bg_color=hex_rgba(th["surface"]))
            txt = Label(text=f"{name}\n{path_text}  ·  {deleted_at}", font_size=fs(11), color=hex_rgba(th["text_secondary"]), halign="left", valign="middle")
            txt.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
            row_box.add_widget(txt)
            if restore_data:
                restore_btn = Button(text="Geri Getir", size_hint=(None, None), size=(dp(90), dp(40)), background_normal="", background_color=hex_rgba(th["ok"], 0.2), color=hex_rgba(th["ok"]), font_size=fs(11))
                restore_btn.bind(on_release=lambda inst, i=hid: Clock.schedule_once(lambda dt: self._do_restore(i), 0.1))
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

    def do_copy_shopping_list(self):
        rows = DB.get_low_stock_items()
        if not rows: return
        lines = ["🛒 ALIŞVERİŞ LİSTESİ"]
        for row in rows:
            unit = row[19] if len(row) > 19 else "Adet"
            lines.append(f"• {row[1]} (Eksik: {row[8] - row[7]} {unit})")
        text = "\n".join(lines)
        try:
            Clipboard.copy(text)
            self._show_message("Kopyalandı", "Alışveriş listesi başarıyla kopyalandı! WhatsApp'a yapıştırabilirsiniz.")
        except Exception as e:
            self._show_message("Hata", str(e))

    def open_shopping_list(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Alışveriş Listesi", on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.get_low_stock_items()
        if rows:
            copy_btn = Button(text="Listeyi Kopyala", size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["primary"]), color=(1,1,1,1), font_size=fs(14), bold=True)
            copy_btn.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: self.do_copy_shopping_list(), 0.1))
            box.add_widget(copy_btn)
        if not rows:
            empty_lbl = Label(text="Harika! Stoğu azalan veya tükenen hiçbir ürün bulunmuyor.", size_hint_y=None, font_size=fs(13), color=hex_rgba(th["ok"]), halign="left")
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for row in rows:
            item_id, name, cat, _, _, _, _, qty, qty_min = row[0:9]
            room_id = row[15]
            unit = row[19] if len(row) > 19 else "Adet"
            path = DB.get_path(item_id)
            crumb = " › ".join([DB.get_room(room_id)[1]] + [p[1] for p in path[:-1]]) if path else ""
            card = SoftShadowCard(orientation="horizontal", size_hint_y=None, height=dph(54), padding=(dp(12), dp(6)), spacing=dp(8), bg_color=hex_rgba(th["surface"]))
            info_col = BoxLayout(orientation="vertical")
            t_lbl = Label(text=name, font_size=fs(14), bold=True, color=hex_rgba(th["text"]), halign="left", valign="middle")
            t_lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
            sub_txt = f"{crumb}  ·  Mevcut: {qty} / Min: {qty_min} {unit}" if crumb else f"Mevcut: {qty} / Min: {qty_min} {unit}"
            s_lbl = Label(text=sub_txt, font_size=fs(11), color=hex_rgba(th["danger"]), halign="left", valign="middle")
            s_lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
            info_col.add_widget(t_lbl)
            info_col.add_widget(s_lbl)
            card.add_widget(info_col)
            go_btn = Button(text="Git", size_hint=(None, None), size=(dph(50), dph(38)), background_normal="", background_color=hex_rgba(th["primary"], 0.2), color=hex_rgba(th["primary"]), font_size=fs(12), bold=True)
            go_btn.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            card.add_widget(go_btn)
            box.add_widget(card)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def open_category_filter(self, category):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar(f"Kategori: {category}", on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.filter_by_category(category)
        if not rows:
            empty_lbl = Label(text="Bu kategoride eşya yok.", size_hint_y=None, font_size=fs(14), color=hex_rgba(th["text_secondary"]))
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for row in rows:
            item_id, name = row[0], row[1]
            room_id = row[15]
            path = DB.get_path(item_id)
            crumb = " › ".join([DB.get_room(room_id)[1]] + [p[1] for p in path[:-1]]) if path else ""
            btn = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def open_recent_list(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Son Eklenen 20 Eşya", on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.get_recent_items(20)
        if not rows:
            empty_lbl = Label(text="Henüz eşya eklenmemiş.", size_hint_y=None, font_size=fs(14), color=hex_rgba(th["text_secondary"]))
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for row in rows:
            item_id, name = row[0], row[1]
            room_id = row[15]
            path = DB.get_path(item_id)
            crumb = " › ".join([DB.get_room(room_id)[1]] + [p[1] for p in path[:-1]]) if path else ""
            btn = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def open_flag_list(self, field, title):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar(title, on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.flagged_items(field)
        if not rows:
            empty_lbl = Label(text="Liste boş.", size_hint_y=None, font_size=fs(14), color=hex_rgba(th["text_secondary"]))
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for row in rows:
            item_id, name = row[0], row[1]
            path = DB.get_path(item_id)
            crumb = " › ".join([p[1] for p in path]) if path else name
            btn = Button(text=f"{name}   ({crumb})", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left", shorten=True)
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def open_move_mode(self):
        if getattr(self.sm.transition, 'is_active', False):
            return
        th = self.theme()
        screen = self.sm.get_screen("info")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Taşınma Modu (Koli No)", on_back=self.go_back, show_menu=False))
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(10))
        box.bind(minimum_height=box.setter("height"))
        info_lbl = Label(text="Kutuların 'Düzenle' ekranından bir Koli No girin;\nburada numaraya göre listelenir.", size_hint_y=None, font_size=fs(12), color=hex_rgba(th["text_secondary"]), halign="left")
        info_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        info_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(info_lbl)
        c = DB.conn.cursor()
        c.execute(f"SELECT {DB.ITEM_COLS} FROM items WHERE move_no > 0 ORDER BY move_no")
        rows = c.fetchall()
        if not rows:
            empty_lbl = Label(text="Henüz koli numarası atanmamış.", size_hint_y=None, font_size=fs(14), color=hex_rgba(th["text_secondary"]))
            empty_lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
            empty_lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(30)))
            box.add_widget(empty_lbl)
        for row in rows:
            item_id, name, move_no = row[0], row[1], row[13]
            btn = Button(text=f"Koli #{move_no} — {name}", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13), halign="left")
            btn.bind(size=lambda w, *a: setattr(w, "text_size", (w.width - dp(16), None)))
            btn.bind(on_release=lambda inst, iid=item_id: Clock.schedule_once(lambda dt: self.jump_to_item(iid), 0.1))
            box.add_widget(btn)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition = SlideTransition(direction="left")
        self.sm.current = "info"

    def do_export_csv(self):
        try:
            path = DB.export_csv()
            self._show_message("Dışa Aktarıldı", f"Dosya başarıyla kaydedildi:\n\n{path}")
        except Exception as e:
            self._show_message("Hata", str(e))

    def _show_message(self, title, text):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(16))
        msg = Label(text=text, font_size=fs(13), color=hex_rgba(th["text"]), halign="left", valign="top", size_hint_y=None)
        msg.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        msg.bind(texture_size=lambda w, val: setattr(w, "height", val[1]))
        box.add_widget(msg)
        close = Button(text="TAMAM", size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1), font_size=fs(14))
        self.open_auto_popup(title, box, buttons_row=close)
        close.bind(on_release=lambda *a: self.close_popup())

    def open_add_room_dialog(self, edit_room_id=None):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text="Odayı Düzenle" if edit_room_id else "Yeni Oda Ekle", size_hint_y=None, bold=True, font_size=fs(16), color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        field = TextInput(hint_text="Oda adı (örn: Salon)", multiline=False, size_hint_y=None, height=dph(46), font_size=fs(15), keyboard_suggestions=False)
        box.add_widget(field)
        self._selected_room_type = "diger"
        type_btn = Button(text=ROOM_TYPES["diger"][0], size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15), color=hex_rgba(th["text"]), font_size=fs(14))
        dropdown = TrackedDropDown()
        for key in ROOM_TYPE_ORDER:
            label, color, abbr = ROOM_TYPES[key]
            item = Button(text=label, size_hint_y=None, height=dph(42), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13))
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
                field.text = str(existing[1])
                self._selected_room_type = str(existing[2]) if len(existing) > 2 else "diger"
                type_btn.text = ROOM_TYPES.get(self._selected_room_type, ROOM_TYPES["diger"])[0]
        def save(*a):
            name = field.text.strip()
            if not name: return
            if edit_room_id:
                DB.update_room(edit_room_id, name, self._selected_room_type)
            else:
                DB.add_room(name, self._selected_room_type)
            self.close_popup()
            Clock.schedule_once(lambda dt: self.refresh_home(), 0.15)
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), save, "KAYDET" if edit_room_id else "EKLE")
        self.open_auto_popup("", box, buttons_row=btn_row)

    def open_edit_room_dialog(self, room_id):
        self.open_add_room_dialog(edit_room_id=room_id)
        
    def open_edit_item_dialog(self, item_id):
        self.open_add_item_dialog(edit_id=item_id)

    def _confirm_delete_room(self, room_id, name):
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text=f"'{name}' odası ve içindeki tüm eşyalar silinsin mi?", font_size=fs(14), size_hint_y=None, color=hex_rgba(self.theme()["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def do_delete(*a):
            DB.delete_room(room_id)
            self.close_popup()
            Clock.schedule_once(lambda dt: self.refresh_home(), 0.15)
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), do_delete, "SİL")
        self.open_auto_popup("Odayı Sil", box, buttons_row=btn_row, scrollable=False)

    def _confirm_empty_box(self, item_id, name):
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text=f"'{name}' içindeki tüm öğeler bir üst seviyeye taşınsın mı?", font_size=fs(14), size_hint_y=None, color=hex_rgba(self.theme()["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        def do_empty(*a):
            DB.empty_box(item_id)
            self.close_popup()
            Clock.schedule_once(lambda dt: self._render_room(), 0.15)
        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), do_empty, "BOŞALT")
        self.open_auto_popup("Kutuyu Boşalt", box, buttons_row=btn_row, scrollable=False)

    def open_move_dialog(self, item_id):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(14))
        lbl = Label(text="Hangi odaya taşınsın?", size_hint_y=None, bold=True, font_size=fs(15), color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        inner.bind(minimum_height=inner.setter("height"))
        for rid, rname, rtype, remoji, rphoto in DB.get_rooms():
            b = Button(text=rname, size_hint_y=None, height=dph(42), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13))
            def do_move(inst, target_room=rid):
                DB.move_item(item_id, target_room, None)
                self.nav_stack = [(target_room, None, DB.get_room(target_room)[1], DB.get_room(target_room)[1])]
                self.close_popup()
                Clock.schedule_once(lambda dt: self._render_room(), 0.15)
            b.bind(on_release=do_move)
            inner.add_widget(b)
        box.add_widget(inner)
        cancel = Button(text="İPTAL", size_hint_y=None, height=dph(44), background_normal="", background_color=hex_rgba(th["text_secondary"], 0.3), color=hex_rgba(th["text"]), font_size=fs(14))
        self.open_auto_popup("Eşyayı Taşı", box, buttons_row=cancel)
        cancel.bind(on_release=lambda *a: self.close_popup())

    def open_add_item_dialog(self, edit_id=None, is_box=False):
        th = self.theme()
        box = self.themed_box(orientation="vertical", spacing=dp(8), padding=dp(14), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        d_title = "Yeni Eşya Ekle"
        if edit_id: d_title = "Eşyayı Düzenle"
        elif is_box: d_title = "Yeni Kutu / Depo Ekle"

        lbl = Label(text=d_title, size_hint_y=None, bold=True, font_size=fs(16), color=hex_rgba(th["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)

        def field(hint, h=46):
            t = TextInput(hint_text=hint, multiline=False, size_hint_y=None, height=dph(h), font_size=fs(14), keyboard_suggestions=False)
            box.add_widget(t)
            return t

        name_field = field("Kutu adı" if is_box else "Eşya adı (örn: Kanepe, Kablo)")

        self._selected_category = "Diğer" if is_box else ITEM_CATEGORIES[-1]
        cat_btn = Button(text=self._selected_category, size_hint_y=None, height=dph(46), background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15), color=hex_rgba(th["text"]), font_size=fs(14))
        dropdown = TrackedDropDown()
        for cat in ITEM_CATEGORIES:
            item = Button(text=cat, size_hint_y=None, height=dph(40), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(13))
            item.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(item)
        cat_btn.bind(on_release=dropdown.open)
        def on_select(instance, value):
            self._selected_category = value
            cat_btn.text = value
        dropdown.bind(on_select=on_select)
        if not is_box: box.add_widget(cat_btn)

        note_field = field("Not (isteğe bağlı)")
        price_field = field("Fiyat / değer (TL, isteğe bağlı)")
        price_field.input_filter = "float"

        expiry_field = field("Son kullanma / garanti (GG/AA/YYYY)")
        def on_expiry_text(instance, value):
            digits = ''.join([c for c in value if c.isdigit()])[:8]
            formatted = ''
            for i, d in enumerate(digits):
                if i == 2 or i == 4: formatted += '/'
                formatted += d
            if instance.text != formatted:
                instance.text = formatted
                Clock.schedule_once(lambda dt: setattr(instance, "cursor", (len(instance.text), 0)), 0)
        expiry_field.bind(text=on_expiry_text)

        loaned_field = field("Ödünç verildiyse kime")

        qty_row = BoxLayout(size_hint_y=None, height=dph(38), spacing=dp(6))
        qty_field = TextInput(hint_text="Miktar", multiline=False, font_size=fs(13), input_filter="int", keyboard_suggestions=False)
        qty_min_field = TextInput(hint_text="Min.", multiline=False, font_size=fs(13), input_filter="int", keyboard_suggestions=False)
        
        self._selected_unit = "Adet"
        unit_btn = Button(text=self._selected_unit, font_size=fs(12), background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15), color=hex_rgba(th["text"]))
        unit_dd = TrackedDropDown()
        for un in UNIT_TYPES:
            ub = Button(text=un, size_hint_y=None, height=dph(36), background_normal="", background_color=hex_rgba(th["surface"]), color=hex_rgba(th["text"]), font_size=fs(12))
            ub.bind(on_release=lambda btn: unit_dd.select(btn.text))
            unit_dd.add_widget(ub)
        unit_btn.bind(on_release=unit_dd.open)
        def on_unit_select(inst, val):
            self._selected_unit = val
            unit_btn.text = val
        unit_dd.bind(on_select=on_unit_select)
        
        qty_row.add_widget(qty_field)
        qty_row.add_widget(unit_btn)
        qty_row.add_widget(qty_min_field)
        box.add_widget(qty_row)

        tags_field = field("Etiketler (virgülle)")
        move_field = field("Taşınma koli no")
        move_field.input_filter = "int"

        # FOTOĞRAF SEÇİM ALANI (Kamera Eklentili ve Yön Düzelten)
        photo_row = BoxLayout(size_hint_y=None, height=dph(50), spacing=dp(8))
        photo_preview = Image(size_hint_x=None, width=dph(50), allow_stretch=True, keep_ratio=True)
        
        photo_state = {"current_file": "", "existing_file": ""}
        
        def update_photo_preview():
            path_to_show = ""
            if photo_state["current_file"]:
                path_to_show = photo_state["current_file"]
            elif photo_state["existing_file"]:
                full_path = os.path.join(get_photo_dir(), photo_state["existing_file"])
                if os.path.exists(full_path):
                    path_to_show = full_path
            
            if path_to_show:
                photo_preview.source = path_to_show
                photo_preview.opacity = 1
                photo_preview.reload()
            else:
                photo_preview.source = ""
                photo_preview.opacity = 0
                
        def on_photo_picked(path):
            if not path: return
            p_dir = get_photo_dir()
            
            # Eğer fotoğraf bizim Evim/Fotograflar içindeyse (kameradan)
            if path.startswith(p_dir):
                fix_image_orientation(path)
                photo_state["current_file"] = path
            else:
                # Galeriden geldiyse, Evim klasörüne kopyala ve yönünü düzelt
                ext = os.path.splitext(path)[1].lower()
                if not ext: ext = ".jpg"
                dest = os.path.join(p_dir, f"photo_{uuid.uuid4().hex[:8]}{ext}")
                try:
                    shutil.copy(path, dest)
                    fix_image_orientation(dest)
                    photo_state["current_file"] = dest
                except Exception:
                    pass
            update_photo_preview()

        def take_camera_photo(*a):
            if camera is None:
                self._show_message("Hata", "Kamera modülü yüklenemedi. Lütfen baştan derleyin.")
                return

            temp_filename = os.path.join(get_photo_dir(), f"cam_{uuid.uuid4().hex[:8]}.jpg")
            
            def _on_complete(filepath):
                def check_and_apply(dt):
                    path_to_check = filepath if (filepath and os.path.exists(filepath)) else temp_filename
                    if os.path.exists(path_to_check):
                        on_photo_picked(path_to_check)
                    else:
                        self._show_message("Uyarı", "Fotoğraf alınamadı. Lütfen tekrar deneyin.")
                Clock.schedule_once(check_and_apply, 0.5)

            try:
                camera.take_picture(filename=temp_filename, on_complete=_on_complete)
            except Exception as e:
                self._show_message("Hata", f"Kamera açılamadı: {e}")

        btn_box = BoxLayout(spacing=dp(6))
        gal_btn = Button(text="Galeri", background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(12))
        gal_btn.bind(on_release=lambda *a: self.open_photo_chooser(on_photo_picked))
        
        cam_btn = Button(text="Kamera", background_normal="", background_color=hex_rgba(th["surface2"]), color=hex_rgba(th["text"]), font_size=fs(12))
        cam_btn.bind(on_release=take_camera_photo)
        
        btn_box.add_widget(gal_btn)
        btn_box.add_widget(cam_btn)
        
        clear_photo_btn = Button(text="Sil", size_hint_x=None, width=dph(40), background_normal="", background_color=hex_rgba(th["danger"]), color=(1,1,1,1), font_size=fs(11), bold=True)
        def clear_photo(*a):
            photo_state["current_file"] = ""
            photo_state["existing_file"] = ""
            update_photo_preview()
        clear_photo_btn.bind(on_release=clear_photo)

        photo_row.add_widget(photo_preview)
        photo_row.add_widget(btn_box)
        photo_row.add_widget(clear_photo_btn)
        box.add_widget(photo_row)

        chk_row = BoxLayout(size_hint_y=None, height=dph(46), spacing=dp(8))
        states = {"fav": False, "sell": False, "lost": False}
        
        def update_chip(btn, key, color_hex):
            is_active = states[key]
            btn.background_color = hex_rgba(color_hex, 0.9) if is_active else hex_rgba(th["text_secondary"], 0.18)
            btn.color = (1, 1, 1, 1) if is_active else hex_rgba(th["text"])
            
        def toggle_chip(btn, key, color_hex):
            states[key] = not states[key]
            update_chip(btn, key, color_hex)

        fav_btn = Button(text="Favori", font_size=fs(12), bold=True, background_normal="", color=(1,1,1,1))
        fav_btn.bind(on_release=lambda inst: toggle_chip(inst, "fav", th["warn"]))
        update_chip(fav_btn, "fav", th["warn"])

        sell_btn = Button(text="Satılık", font_size=fs(12), bold=True, background_normal="", color=(1,1,1,1))
        sell_btn.bind(on_release=lambda inst: toggle_chip(inst, "sell", th["ok"]))
        update_chip(sell_btn, "sell", th["ok"])

        lost_btn = Button(text="Kayıp", font_size=fs(12), bold=True, background_normal="", color=(1,1,1,1))
        lost_btn.bind(on_release=lambda inst: toggle_chip(inst, "lost", th["danger"]))
        update_chip(lost_btn, "lost", th["danger"])
        
        chk_row.add_widget(fav_btn)
        chk_row.add_widget(sell_btn)
        chk_row.add_widget(lost_btn)
        box.add_widget(chk_row)

        if edit_id:
            try:
                db_item = DB.get_item(edit_id)
                if db_item:
                    name_field.text = str(db_item[1] or "")
                    self._selected_category = str(db_item[2] or "Diğer")
                    cat_btn.text = self._selected_category
                    note_field.text = str(db_item[3] or "")
                    price_field.text = str(db_item[4]) if db_item[4] else ""
                    expiry_field.text = str(db_item[5] or "")
                    loaned_field.text = str(db_item[6] or "")
                    qty_field.text = str(db_item[7]) if db_item[7] else ""
                    qty_min_field.text = str(db_item[8]) if db_item[8] else ""
                    tags_field.text = str(db_item[9] or "")
                    move_field.text = str(db_item[13]) if db_item[13] else ""
                    
                    if len(db_item) > 19:
                        self._selected_unit = str(db_item[19] or "Adet")
                        unit_btn.text = self._selected_unit
                        
                    photo_state["existing_file"] = str(db_item[18] or "")
                    update_photo_preview()
                    
                    states["fav"] = bool(db_item[10])
                    update_chip(fav_btn, "fav", th["warn"])
                    
                    states["sell"] = bool(db_item[11])
                    update_chip(sell_btn, "sell", th["ok"])
                    
                    states["lost"] = bool(db_item[12])
                    update_chip(lost_btn, "lost", th["danger"])
            except Exception:
                pass

        update_photo_preview()

        def save(*a):
            name = name_field.text.strip()
            if not name: return
            room_id, parent_id, _, _ = self.nav_stack[-1]
            
            p_val = price_field.text.strip()
            q_val = qty_field.text.strip()
            qm_val = qty_min_field.text.strip()
            m_val = move_field.text.strip()
            
            final_photo = photo_state["existing_file"]
            if photo_state["current_file"]:
                final_photo = os.path.basename(photo_state["current_file"])
            elif not photo_state["existing_file"] and not photo_state["current_file"]:
                final_photo = ""
            
            kw = dict(
                price=float(p_val) if p_val else 0,
                expiry=expiry_field.text.strip(),
                loaned_to=loaned_field.text.strip(),
                qty=int(q_val) if q_val else 0,
                qty_min=int(qm_val) if qm_val else 0,
                tags=tags_field.text.strip(),
                is_favorite=states["fav"],
                is_sell=states["sell"],
                is_lost=states["lost"],
                move_no=int(m_val) if m_val else 0,
                unit=self._selected_unit,
                photo_path=final_photo
            )
            if edit_id:
                DB.update_item(edit_id, name, self._selected_category, note_field.text.strip(), **kw)
            else:
                DB.add_item(room_id, parent_id, name, self._selected_category, note_field.text.strip(), **kw)
            self.close_popup()
            Clock.schedule_once(lambda dt: self._render_room(), 0.15)

        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), save, "KAYDET")
        self.open_auto_popup("", box, buttons_row=btn_row)

    def _confirm_delete_item(self, item_id, name):
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        path = breadcrumb + "  ›  " + name
        box = self.themed_box(orientation="vertical", spacing=dp(10), padding=dp(14))
        lbl = Label(text=f"'{name}' silinsin mi?\n(Geçmişten geri getirilebilir)", font_size=fs(13), size_hint_y=None, color=hex_rgba(self.theme()["text"]))
        lbl.bind(width=lambda w, val: setattr(w, "text_size", (val, None)))
        lbl.bind(texture_size=lambda w, val: setattr(w, "height", val[1] + dp(10)))
        box.add_widget(lbl)

        def do_delete(*a):
            DB.delete_item(item_id, path)
            self.close_popup()
            Clock.schedule_once(lambda dt: self._render_room(), 0.15)

        btn_row = self.styled_popup_buttons(lambda: self.close_popup(), do_delete, "SİL")
        self.open_auto_popup("Eşyayı Sil", box, buttons_row=btn_row, scrollable=False)

if __name__ == "__main__":
    EvimApp().run()
