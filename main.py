# -*- coding: utf-8 -*-
"""
EVİM - Ev Eşya Envanteri Uygulaması
Odalar -> Eşyalar -> Eşyaların içindeki eşyalar (sınırsız derinlik)
Sade Kivy ile geliştirilmiştir (KivyMD KULLANILMAZ - Android derlemesinde
kivymd'nin pip kurulumu kararsız olduğu için tamamen çıkarıldı).
"""

import os
import sqlite3
import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.lang import Builder
from kivy.utils import platform, get_color_from_hex

# ---------------------------------------------------------------------------
# Veritabani
# ---------------------------------------------------------------------------

def get_db_path():
    if platform == "android":
        from android.storage import app_storage_path
        base = app_storage_path()
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "evim.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(get_db_path())
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color_index INTEGER DEFAULT 0
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
            item_name TEXT,
            path_text TEXT,
            deleted_at TEXT
        )""")
        self.conn.commit()

    def add_room(self, name, color_index=0):
        c = self.conn.cursor()
        c.execute("INSERT INTO rooms (name, color_index) VALUES (?,?)", (name, color_index))
        self.conn.commit()
        return c.lastrowid

    def get_rooms(self):
        c = self.conn.cursor()
        c.execute("SELECT id, name, color_index FROM rooms ORDER BY id")
        return c.fetchall()

    def delete_room(self, room_id):
        c = self.conn.cursor()
        c.execute("SELECT name FROM rooms WHERE id=?", (room_id,))
        row = c.fetchone()
        if row:
            self._log_history(row[0], row[0])
        c.execute("DELETE FROM rooms WHERE id=?", (room_id,))
        self.conn.commit()

    def add_item(self, room_id, parent_id, name, category, note):
        c = self.conn.cursor()
        c.execute("""INSERT INTO items (room_id, parent_id, name, category, note)
                     VALUES (?,?,?,?,?)""", (room_id, parent_id, name, category, note))
        self.conn.commit()
        return c.lastrowid

    def update_item(self, item_id, name, category, note):
        c = self.conn.cursor()
        c.execute("UPDATE items SET name=?, category=?, note=? WHERE id=?",
                   (name, category, note, item_id))
        self.conn.commit()

    def get_items(self, room_id, parent_id):
        c = self.conn.cursor()
        if parent_id is None:
            c.execute("""SELECT id, name, category, note FROM items
                         WHERE room_id=? AND parent_id IS NULL ORDER BY id""", (room_id,))
        else:
            c.execute("""SELECT id, name, category, note FROM items
                         WHERE parent_id=? ORDER BY id""", (parent_id,))
        return c.fetchall()

    def count_children(self, item_id):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM items WHERE parent_id=?", (item_id,))
        return c.fetchone()[0]

    def get_item(self, item_id):
        c = self.conn.cursor()
        c.execute("SELECT id, name, category, note FROM items WHERE id=?", (item_id,))
        return c.fetchone()

    def delete_item(self, item_id, path_text):
        c = self.conn.cursor()
        c.execute("SELECT name FROM items WHERE id=?", (item_id,))
        row = c.fetchone()
        if row:
            self._log_history(row[0], path_text)
        c.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def _log_history(self, name, path_text):
        c = self.conn.cursor()
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        c.execute("INSERT INTO history (item_name, path_text, deleted_at) VALUES (?,?,?)",
                   (name, path_text, now))
        self.conn.commit()

    def get_history(self):
        c = self.conn.cursor()
        c.execute("SELECT item_name, path_text, deleted_at FROM history ORDER BY id DESC LIMIT 200")
        return c.fetchall()


DB = Database()

CARD_COLORS = ["#FF6F3C", "#3C8DFF", "#3CB878", "#B23CFF",
               "#FF3C7E", "#FFB23C", "#3CD2FF", "#8D6E63"]
ITEM_CATEGORIES = ["Elektronik", "Mobilya", "Giyim", "Kitap/Kırtasiye",
                    "Mutfak Eşyası", "Dekorasyon", "Belge", "Diğer"]

THEMES = {
    "light": {
        "bg": "#F4F1ED", "surface": "#FFFFFF", "text": "#26221E",
        "text_secondary": "#8A8378", "primary": "#FF6F3C", "danger": "#E4573D",
    },
    "dark": {
        "bg": "#1B1815", "surface": "#26221E", "text": "#F4F1ED",
        "text_secondary": "#9C958A", "primary": "#FF8A5C", "danger": "#FF6B54",
    },
}

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

<Avatar>:
    canvas.before:
        Color:
            rgba: self.bg_color
        Ellipse:
            pos: self.pos
            size: self.size
    Label:
        text: root.letter
        font_size: root.size[0] * 0.42
        bold: True
        color: 1,1,1,1
        pos: root.pos
        size: root.size

<TopBar>:
    size_hint_y: None
    height: dp(58)
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


class Avatar(FloatLayout):
    bg_color = ListProperty([1, 1, 1, 1])
    letter = StringProperty("?")


class TopBar(BoxLayout):
    bar_color = ListProperty([1, 1, 1, 1])


class IconBtn(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        kw.setdefault("size_hint", (None, None))
        kw.setdefault("size", (dp(40), dp(40)))
        super().__init__(**kw)


def hex_rgba(hex_color, alpha=1.0):
    r = get_color_from_hex(hex_color)
    return [r[0], r[1], r[2], alpha]


class HomeScreen(Screen):
    pass


class RoomScreen(Screen):
    pass


class HistoryScreen(Screen):
    pass


class EvimApp(App):
    theme_name = StringProperty("light")
    nav_stack = []

    def theme(self):
        return THEMES[self.theme_name]

    def build(self):
        self.title = "Evim"
        Window.clearcolor = hex_rgba(self.theme()["bg"])
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(RoomScreen(name="room"))
        self.sm.add_widget(HistoryScreen(name="history"))
        self.refresh_home()
        return self.sm

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        Window.clearcolor = hex_rgba(self.theme()["bg"])
        if self.sm.current == "home":
            self.refresh_home()
        elif self.sm.current == "room":
            self._render_room()
        elif self.sm.current == "history":
            self.open_history()

    def make_topbar(self, title, on_back=None, show_theme=True, show_history=False):
        th = self.theme()
        bar = TopBar(bar_color=hex_rgba(th["primary"]))
        if on_back:
            back = IconBtn(text="<", font_size=24, color=(1, 1, 1, 1))
            back.bind(on_release=lambda *a: on_back())
            bar.add_widget(back)
        lbl = Label(text=title, bold=True, font_size=20, color=(1, 1, 1, 1),
                    halign="left", valign="middle")
        lbl.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
        bar.add_widget(lbl)
        if show_history:
            hist = IconBtn(text="[Geçmiş]", font_size=13, color=(1, 1, 1, 0.65))
            hist.bind(on_release=lambda *a: self.open_history())
            bar.add_widget(hist)
        if show_theme:
            icon = "Açık" if self.theme_name == "dark" else "Koyu"
            th_btn = IconBtn(text=icon, font_size=13, color=(1, 1, 1, 1), size=(dp(56), dp(40)))
            th_btn.bind(on_release=lambda *a: self.toggle_theme())
            bar.add_widget(th_btn)
        return bar

    def styled_popup_buttons(self, cancel_cb, confirm_cb, confirm_text="KAYDET"):
        th = self.theme()
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10),
                         padding=(dp(4), dp(4)))
        cancel = Button(text="İPTAL", background_normal="",
                         background_color=hex_rgba(th["text_secondary"], 0.3),
                         color=hex_rgba(th["text"]))
        cancel.bind(on_release=lambda *a: cancel_cb())
        ok = Button(text=confirm_text, background_normal="",
                    background_color=hex_rgba(th["primary"]), color=(1, 1, 1, 1))
        ok.bind(on_release=confirm_cb)
        row.add_widget(cancel)
        row.add_widget(ok)
        return row

    def refresh_home(self):
        th = self.theme()
        screen = self.sm.get_screen("home")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("EVİM", show_history=True))

        scroll = ScrollView()
        grid = GridLayout(cols=2, spacing=dp(14), padding=dp(14), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for rid, name, color_idx in DB.get_rooms():
            grid.add_widget(self._make_room_card(rid, name, color_idx))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        fab_wrap = FloatLayout(size_hint_y=None, height=dp(70))
        fab = Button(text="+", font_size=30, size_hint=(None, None), size=(dp(58), dp(58)),
                     pos_hint={"right": 0.96, "y": 0.15},
                     background_normal="", background_color=hex_rgba(th["primary"]),
                     color=(1, 1, 1, 1))
        fab.bind(on_release=lambda *a: self.open_add_room_dialog())
        fab_wrap.add_widget(fab)
        root.add_widget(fab_wrap)

        screen.add_widget(root)
        Window.clearcolor = hex_rgba(th["bg"])

    def _make_room_card(self, room_id, name, color_idx):
        th = self.theme()
        color = CARD_COLORS[color_idx % len(CARD_COLORS)]
        card = RoundedCard(orientation="vertical", size_hint=(1, None), height=dp(150),
                            padding=dp(10), spacing=dp(6), bg_color=hex_rgba(th["surface"]))
        avatar_wrap = FloatLayout(size_hint_y=None, height=dp(64))
        avatar = Avatar(size_hint=(None, None), size=(dp(64), dp(64)),
                         pos_hint={"center_x": 0.5}, bg_color=hex_rgba(color),
                         letter=name[0].upper())
        avatar_wrap.add_widget(avatar)
        card.add_widget(avatar_wrap)
        name_lbl = Label(text=name, color=hex_rgba(th["text"]), bold=True, font_size=16)
        card.add_widget(name_lbl)
        btn_row = BoxLayout(size_hint_y=None, height=dp(30))
        enter_btn = Button(text="Aç", background_normal="",
                            background_color=hex_rgba(th["primary"], 0.15), color=hex_rgba(th["primary"]))
        enter_btn.bind(on_release=lambda *a: self.enter_room(room_id, name))
        del_btn = Button(text="Sil", background_normal="",
                          background_color=hex_rgba(th["danger"], 0.12), color=hex_rgba(th["danger"]))
        del_btn.bind(on_release=lambda *a: self._confirm_delete_room(room_id, name))
        btn_row.add_widget(enter_btn)
        btn_row.add_widget(del_btn)
        card.add_widget(btn_row)
        return card

    def enter_room(self, room_id, name):
        self.nav_stack = [(room_id, None, name, name)]
        self._render_room()
        self.sm.transition.direction = "left"
        self.sm.current = "room"

    def _render_room(self):
        th = self.theme()
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        screen = self.sm.get_screen("room")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar(title, on_back=self.go_back))

        crumb = Label(text=breadcrumb, size_hint_y=None, height=dp(26), font_size=12,
                      color=hex_rgba(th["text_secondary"]))
        root.add_widget(crumb)

        scroll = ScrollView()
        grid = GridLayout(cols=2, spacing=dp(14), padding=dp(14), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        items = DB.get_items(room_id, parent_id)
        if not items:
            empty = Label(text="Henüz eşya eklenmedi.\nSağ alttaki + ile ekleyin.",
                          color=hex_rgba(th["text_secondary"]), size_hint_y=None, height=dp(80))
            grid.add_widget(empty)
        for item_id, name, category, note in items:
            grid.add_widget(self._make_item_card(item_id, name, category, note))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        fab_wrap = FloatLayout(size_hint_y=None, height=dp(70))
        fab = Button(text="+", font_size=30, size_hint=(None, None), size=(dp(58), dp(58)),
                     pos_hint={"right": 0.96, "y": 0.15},
                     background_normal="", background_color=hex_rgba(th["primary"]),
                     color=(1, 1, 1, 1))
        fab.bind(on_release=lambda *a: self.open_add_item_dialog())
        fab_wrap.add_widget(fab)
        root.add_widget(fab_wrap)

        screen.add_widget(root)

    def _make_item_card(self, item_id, name, category, note):
        th = self.theme()
        child_count = DB.count_children(item_id)
        color = CARD_COLORS[item_id % len(CARD_COLORS)]
        card = RoundedCard(orientation="vertical", size_hint=(1, None), height=dp(150),
                            padding=dp(8), spacing=dp(4), bg_color=hex_rgba(th["surface"]))
        cat_lbl = Label(text=category, size_hint_y=None, height=dp(16), font_size=11,
                         color=hex_rgba(th["text_secondary"]))
        card.add_widget(cat_lbl)
        avatar_wrap = FloatLayout(size_hint_y=None, height=dp(50))
        avatar = Avatar(size_hint=(None, None), size=(dp(50), dp(50)),
                         pos_hint={"center_x": 0.5}, bg_color=hex_rgba(color),
                         letter=name[0].upper())
        avatar_wrap.add_widget(avatar)
        card.add_widget(avatar_wrap)
        title = name + (f"  ({child_count})" if child_count else "")
        name_lbl = Label(text=title, color=hex_rgba(th["text"]), font_size=14, bold=True)
        card.add_widget(name_lbl)
        btn_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4))
        open_btn = Button(text="Gir", background_normal="",
                           background_color=hex_rgba(th["primary"], 0.15), color=hex_rgba(th["primary"]), font_size=12)
        open_btn.bind(on_release=lambda *a: self.enter_item(item_id, name))
        edit_btn = Button(text="Düzenle", background_normal="",
                           background_color=hex_rgba(th["text_secondary"], 0.15), color=hex_rgba(th["text"]), font_size=12)
        edit_btn.bind(on_release=lambda *a: self.open_edit_item_dialog(item_id))
        del_btn = Button(text="Sil", background_normal="",
                          background_color=hex_rgba(th["danger"], 0.12), color=hex_rgba(th["danger"]), font_size=12)
        del_btn.bind(on_release=lambda *a: self._confirm_delete_item(item_id, name))
        btn_row.add_widget(open_btn)
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        card.add_widget(btn_row)
        return card

    def enter_item(self, item_id, name):
        room_id, _, _, breadcrumb = self.nav_stack[-1]
        self.nav_stack.append((room_id, item_id, name, breadcrumb + "  ›  " + name))
        self._render_room()
        self.sm.transition.direction = "left"
        self.sm.current = "room"

    def go_back(self):
        if self.nav_stack:
            self.nav_stack.pop()
        self.sm.transition.direction = "right"
        if self.nav_stack:
            self._render_room()
            self.sm.current = "room"
        else:
            self.refresh_home()
            self.sm.current = "home"

    def open_history(self):
        th = self.theme()
        screen = self.sm.get_screen("history")
        screen.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.make_topbar("Silinenler Geçmişi", on_back=self.go_back, show_theme=False))
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=dp(8))
        box.bind(minimum_height=box.setter("height"))
        rows = DB.get_history()
        if not rows:
            box.add_widget(Label(text="Henüz silinen bir şey yok.", size_hint_y=None, height=dp(40),
                                  color=hex_rgba(th["text_secondary"])))
        for name, path_text, deleted_at in rows:
            line = Label(text=f"{name}  ·  {path_text}  ·  {deleted_at}",
                         size_hint_y=None, height=dp(30), font_size=12,
                         color=hex_rgba(th["text_secondary"]), halign="left")
            line.bind(size=lambda w, *a: setattr(w, "text_size", w.size))
            box.add_widget(line)
        scroll.add_widget(box)
        root.add_widget(scroll)
        screen.add_widget(root)
        self.sm.transition.direction = "left"
        self.sm.current = "history"

    def open_add_room_dialog(self):
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        field = TextInput(hint_text="Oda adı (örn: Salon)", multiline=False, size_hint_y=None, height=dp(44))
        box.add_widget(field)
        popup = Popup(title="Yeni Oda Ekle", content=box, size_hint=(0.85, None), height=dp(180))

        def save(*a):
            name = field.text.strip()
            if not name:
                return
            DB.add_room(name, len(DB.get_rooms()))
            popup.dismiss()
            self.refresh_home()

        box.add_widget(self.styled_popup_buttons(popup.dismiss, save, "EKLE"))
        popup.open()

    def _confirm_delete_room(self, room_id, name):
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text=f"'{name}' odası ve içindeki tüm eşyalar silinsin mi?"))
        popup = Popup(title="Odayı Sil", content=box, size_hint=(0.85, None), height=dp(180))

        def do_delete(*a):
            DB.delete_room(room_id)
            popup.dismiss()
            self.refresh_home()

        box.add_widget(self.styled_popup_buttons(popup.dismiss, do_delete, "SİL"))
        popup.open()

    def open_add_item_dialog(self, edit_id=None):
        th = self.theme()
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        name_field = TextInput(hint_text="Eşya adı (örn: Kanepe, Kutu)", multiline=False,
                                size_hint_y=None, height=dp(44))
        note_field = TextInput(hint_text="Not (isteğe bağlı)", multiline=False,
                                size_hint_y=None, height=dp(44))

        self._selected_category = ITEM_CATEGORIES[-1]
        cat_btn = Button(text=self._selected_category, size_hint_y=None, height=dp(44),
                          background_normal="", background_color=hex_rgba(th["text_secondary"], 0.15),
                          color=hex_rgba(th["text"]))
        dropdown = DropDown()
        for cat in ITEM_CATEGORIES:
            item = Button(text=cat, size_hint_y=None, height=dp(40),
                          background_normal="", background_color=hex_rgba(th["surface"]),
                          color=hex_rgba(th["text"]))
            item.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(item)
        cat_btn.bind(on_release=dropdown.open)

        def on_select(instance, value):
            self._selected_category = value
            cat_btn.text = value
        dropdown.bind(on_select=on_select)

        box.add_widget(Label(text="Eşyayı Düzenle" if edit_id else "Yeni Eşya Ekle",
                              size_hint_y=None, height=dp(30), bold=True))
        box.add_widget(name_field)
        box.add_widget(cat_btn)
        box.add_widget(note_field)

        if edit_id:
            item = DB.get_item(edit_id)
            if item:
                name_field.text = item[1]
                self._selected_category = item[2]
                cat_btn.text = item[2]
                note_field.text = item[3] or ""

        popup = Popup(title="", content=box, size_hint=(0.9, None), height=dp(360), separator_height=0)

        def save(*a):
            name = name_field.text.strip()
            if not name:
                return
            room_id, parent_id, _, _ = self.nav_stack[-1]
            if edit_id:
                DB.update_item(edit_id, name, self._selected_category, note_field.text.strip())
            else:
                DB.add_item(room_id, parent_id, name, self._selected_category, note_field.text.strip())
            popup.dismiss()
            self._render_room()

        box.add_widget(self.styled_popup_buttons(popup.dismiss, save, "KAYDET"))
        popup.open()

    def open_edit_item_dialog(self, item_id):
        self.open_add_item_dialog(edit_id=item_id)

    def _confirm_delete_item(self, item_id, name):
        room_id, parent_id, title, breadcrumb = self.nav_stack[-1]
        path = breadcrumb + "  ›  " + name
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(Label(text=f"'{name}' silinsin mi?\n(İçindeki eşyalar da silinir)"))
        popup = Popup(title="Eşyayı Sil", content=box, size_hint=(0.85, None), height=dp(200))

        def do_delete(*a):
            DB.delete_item(item_id, path)
            popup.dismiss()
            self._render_room()

        box.add_widget(self.styled_popup_buttons(popup.dismiss, do_delete, "SİL"))
        popup.open()


if __name__ == "__main__":
    EvimApp().run()
