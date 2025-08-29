# --- CONFIG ---
from fastapi import FastAPI
app = FastAPI()

#from kivy.config import Config
#import random, os

random.seed(os.urandom(16))

Config.set("kivy", "keyboard_mode", "system")  # 👈 Force Android system keyboard
 Prefer SDL2 audio on Windows to avoid GStreamer DLL issues
Config.set("kivy", "audio", "sdl2")
os.environ["KIVY_AUDIO"] = "sdl2"
from kivy.core.window import Window

Window.softinput_mode = "pan"

# --- FONT CONFIG ---
import os
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path

# --- Absolute Path Fix ---
# Get the absolute path of the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Build absolute paths to resource directories
fonts_dir = os.path.join(script_dir, 'fonts')
sounds_dir = os.path.join(script_dir, 'sounds')

# Add resource directories to Kivy's search paths
resource_add_path(fonts_dir)
resource_add_path(sounds_dir)

# --- For Debugging: You can remove these lines once it works ---
print(f"✅ Current Script Directory: {script_dir}")
print(f"✅ Expecting Fonts In: {fonts_dir}")
print(f"✅ Expecting Sounds In: {sounds_dir}")
# ----------------------------------------------------------------

# --- Define absolute paths for the font files for robust loading ---
nova_font_path = os.path.join(fonts_dir, 'Orbitron-Bold.ttf')

# Prefer OpenSansEmoji; if missing, fall back to NotoEmoji-Regular, then seguiemj.ttf (Windows)
emoji_candidates = [
    os.path.join(fonts_dir, 'OpenSansEmoji.ttf'),
    os.path.join(fonts_dir, 'NotoEmoji-Regular.ttf'),
    os.path.join(fonts_dir, 'seguiemj.ttf'),  # note: Kivy renders it as monochrome
]
emoji_font_path = None
for path in emoji_candidates:
    if os.path.exists(path):
        emoji_font_path = path
        break
if not emoji_font_path:
    # Last resort: still point to OpenSansEmoji so registration fails clearly
    emoji_font_path = os.path.join(fonts_dir, 'OpenSansEmoji.ttf')

# Register the fonts using their full, absolute paths
LabelBase.register(name='NovaFont', fn_regular=nova_font_path)
LabelBase.register(name='CyberFont', fn_regular=nova_font_path)
LabelBase.register(name='EmojiSans', fn_regular=emoji_font_path)

print(f"✅ Using emoji font: {emoji_font_path}")
print("ℹ️ Note: Kivy labels render emoji in monochrome. Color emoji (e.g., Segoe UI Emoji) won't appear in color.")

# Note: Kivy's default_font expects file paths, not font names. We'll explicitly
# set font_name on emoji-capable widgets instead of misusing default_font.
# --- IMPORTS ---
import threading, time, math, random
from threading import Lock
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.dropdown import DropDown
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.graphics import Color, Ellipse, Line, Rectangle, InstructionGroup
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader

# This is a placeholder for your core logic.
try:
    from core import handle_message, init_memory, display_help
except ImportError:
    def handle_message(msg):
        return f"This is a test response to: {msg} ⚡"


    def init_memory():
        print("Initializing memory...")


    def display_help():
        return "This is the help message."


# --- SCREEN MANAGER ---
class WindowManager(ScreenManager):
    pass


# --- DATA STREAM EFFECT ---
class DataStream(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.columns = 40
        self.drops = [random.uniform(0, self.height) for _ in range(self.columns)]
        self.speeds = [random.uniform(dp(2), dp(6)) for _ in range(self.columns)]
        self.lengths = [random.randint(20, 35) for _ in range(self.columns)]
        self.colors = [self.random_color() for _ in range(self.columns)]
        self.col_width = self.width / self.columns
        self.trails = [[] for _ in range(self.columns)]
        Clock.schedule_interval(self.update, 1 / 30)
        self.bind(size=self.on_resize)

    def on_resize(self, *args):
        self.col_width = self.width / self.columns

    def random_color(self):
        return (random.uniform(0.0, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0))

    def update(self, dt):
        self.canvas.clear()
        with self.canvas:
            for i in range(self.columns):
                x = i * self.col_width + self.col_width / 2
                self.trails[i].insert(0, self.drops[i])
                if len(self.trails[i]) > self.lengths[i]:
                    self.trails[i].pop()
                for j, y in enumerate(self.trails[i]):
                    alpha = max(0, 0.8 * (1 - j / self.lengths[i]))
                    Color(*self.colors[i], alpha)
                    Line(points=[x, y, x, y - dp(2)], width=2)
                self.drops[i] -= self.speeds[i]
                if self.drops[i] < -dp(10):
                    self.drops[i] = self.height + dp(10)
                    self.speeds[i] = random.uniform(dp(2), dp(6))
                    self.lengths[i] = random.randint(20, 35)
                    self.trails[i] = []
                    self.colors[i] = self.random_color()


# --- GLITCH IMAGE WIDGET ---
class GlitchImage(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.glitch_group = None

    def trigger_glitch(self):
        if not self.texture: return
        self.glitch_group = InstructionGroup()
        self.glitch_group.add(Color(1, 1, 1, 0.05))
        self.glitch_group.add(Rectangle(pos=self.pos, size=self.size))
        for _ in range(random.randint(5, 10)):
            tex_x = random.randint(0, self.texture.width - 20)
            tex_y = random.randint(0, self.texture.height - 5)
            tex_w = random.randint(10, 20)
            tex_h = random.randint(2, 5)
            pos_x = self.x + random.randint(0, int(self.width - tex_w))
            pos_y = self.y + random.randint(0, int(self.height - tex_h))
            self.glitch_group.add(Color(1, 1, 1, 1))
            self.glitch_group.add(Rectangle(
                pos=(pos_x, pos_y),
                size=(tex_w, tex_h),
                texture=self.texture.get_region(tex_x, tex_y, tex_w, tex_h)
            ))
        self.canvas.after.add(self.glitch_group)

    def reset_glitch(self):
        if self.glitch_group:
            self.canvas.after.remove(self.glitch_group)
            self.glitch_group = None


# --- KV STRING ---
KV_STRING = """
#:import Window kivy.core.window.Window
#:import dp kivy.metrics.dp
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

WindowManager:
    transition: FadeTransition(duration=0.3)
    WelcomeScreen:
        name: 'welcome'
    ChatScreen:
        name: 'chat'
    AboutScreen:
        name: 'about'

<UserBubble>:
    size_hint_x: None
    padding: dp(12), dp(8)
    markup: True
    font_name: "CyberFont"
    canvas.before:
        Color:
            rgba: 0.2, 0.7, 1, 0.9
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16]
    color: 0,0,0,1

<NovaBubble>:
    size_hint_x: None
    padding: dp(12), dp(8)
    markup: True
    font_name: "CyberFont"
    canvas.before:
        Color:
            rgba: 0.5, 0.2, 0.8, 0.9
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16]
    color: 1,1,1,1

<TypingBubble>:
    size_hint_x: None
    halign: "left"
    valign: "middle"
    padding: dp(12), dp(8)
    text: "NOVA is thinking"
    font_name: "NovaFont"
    color: 1,1,1,1
    canvas.before:
        Color:
            rgba: 0.5, 0.2, 0.8, 0.5
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16]

<NeonSignButton>:
    background_normal: ""
    background_color: 0, 0, 0, 0
    font_size: "20sp"
    bold: True
    color: 1, 1, 1, 0.96
    font_name: "NovaFont"
    # Base body
    canvas.before:
        # Base dark rounded body
        Color:
            rgba: 0, 0, 0, 0.78
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.edge_radius]
        # Soft inner top highlight for 3D look
        Color:
            rgba: 1, 1, 1, 0.06
        Rectangle:
            pos: self.x, self.y + self.height * 0.5
            size: self.width, self.height * 0.45
        # Outer glow layers (expand outward with decreasing alpha)
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.35 * self.glow_a
        RoundedRectangle:
            pos: self.x - dp(2), self.y - dp(2)
            size: self.width + dp(4), self.height + dp(4)
            radius: [self.edge_radius + dp(1)]
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.18 * self.glow_a
        RoundedRectangle:
            pos: self.x - dp(4), self.y - dp(4)
            size: self.width + dp(8), self.height + dp(8)
            radius: [self.edge_radius + dp(2)]
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.08 * self.glow_a
        RoundedRectangle:
            pos: self.x - dp(7), self.y - dp(7)
            size: self.width + dp(14), self.height + dp(14)
            radius: [self.edge_radius + dp(4)]
        # Subtle drop shadow below
        Color:
            rgba: 0, 0, 0, 0.25
        RoundedRectangle:
            pos: self.x, self.y - dp(2)
            size: self.width, self.height
            radius: [self.edge_radius]
    # Neon tube outlines
    canvas.after:
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.90 * self.glow_a
        Line:
            width: 1.4
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.edge_radius)
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.55 * self.glow_a
        Line:
            width: 2.4
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.edge_radius)
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.28 * self.glow_a
        Line:
            width: 3.6
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.edge_radius)

<NeonPanel>:
    # Base body
    canvas.before:
        # Base dark rounded body
        Color:
            rgba: 0, 0, 0, self.fill_a
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.edge_radius]
        # Outer glow layers
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.28 * self.glow_a
        RoundedRectangle:
            pos: self.x - dp(2), self.y - dp(2)
            size: self.width + dp(4), self.height + dp(4)
            radius: [self.edge_radius + dp(1)]
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.14 * self.glow_a
        RoundedRectangle:
            pos: self.x - dp(5), self.y - dp(5)
            size: self.width + dp(10), self.height + dp(10)
            radius: [self.edge_radius + dp(3)]
    canvas.after:
        # Neon tube outlines
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.85 * self.glow_a
        Line:
            width: 1.2
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.edge_radius)
        Color:
            rgba: self.neon_color[0], self.neon_color[1], self.neon_color[2], 0.38 * self.glow_a
        Line:
            width: 2.2
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.edge_radius)

<SendButton@Button>:
    background_normal: ''
    background_color: 0, 0, 0, 0
    text: ''
    size_hint: None, None
    size: dp(48), dp(48)
    canvas.before:
        # Neon glow rings (purple for chat)
        Color:
            rgba: 155/255, 89/255, 182/255, 0.32
        Ellipse:
            pos: self.x - dp(4), self.y - dp(4)
            size: self.width + dp(8), self.height + dp(8)
        Color:
            rgba: 155/255, 89/255, 182/255, 0.18
        Ellipse:
            pos: self.x - dp(7), self.y - dp(7)
            size: self.width + dp(14), self.height + dp(14)
        # Base body
        Color:
            rgba: 0, 0, 0, 0.8
        Ellipse:
            pos: self.pos
            size: self.size
    canvas.after:
        # Neon tube outlines
        Color:
            rgba: 155/255, 89/255, 182/255, 0.9
        Line:
            circle: (self.center_x, self.center_y, self.width/2.0)
            width: 1.4
        Color:
            rgba: 155/255, 89/255, 182/255, 0.55
        Line:
            circle: (self.center_x, self.center_y, self.width/2.0 - dp(1))
            width: 2.4
        # Paper-plane mark
        Color:
            rgba: 1, 1, 1, 0.92
        Line:
            points: [self.center_x + self.width * 0.15, self.center_y, self.center_x - self.width * 0.15, self.center_y + self.height * 0.2, self.center_x - self.width * 0.05, self.center_y, self.center_x - self.width * 0.15, self.center_y - self.height * 0.2]
            close: True
            width: 1.5

<WelcomeScreen>:
    RelativeLayout:
        GlitchImage:
            id: background_image
            source: "background.png"
            fit_mode: "fill"
            size: root.size
            pos: root.pos

        Label:
            id: welcome_title
            text: "TALK TO NOVA"
            font_name: "NovaFont"
            font_size: "36sp"
            size_hint: None, None
            size: self.texture_size
            pos_hint: {"center_x": 0.5, "top": 0.9}
            color: 0.1, 1, 0.9, 1

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(15)
            size_hint_y: None
            height: dp(150)
            pos_hint: {"center_x": 0.5, "center_y": 0.3}

            NeonSignButton:
                id: enter_button
                text: "ENTER"
                font_size: "22sp"
                size_hint: (0.5, None)
                height: dp(50)
                pos_hint: {"center_x": 0.5}
                neon_color: 0.05, 0.95, 1, 1
                color: 1, 1, 1, 1
                on_press: app.play_press_sound()
                on_release: app.play_sound_and_change_screen('chat')

            NeonSignButton:
                id: exit_button
                text: "EXIT NOVA"
                font_size: "18sp"
                size_hint: (0.4, None)
                height: dp(45)
                pos_hint: {"center_x": 0.5}
                neon_color: 1, 0.2, 0.3, 1
                color: 1, 1, 1, 1
                on_press: app.play_press_sound()
                on_release: root.show_scared_popup()

        Widget:
            id: particle_layer

        NeonSignButton:
            text: "Menu"
            size_hint: None, None
            size: dp(90), dp(40)
            pos_hint: {"x": 0, "top": 1}
            neon_color: 0.05, 0.95, 1, 1
            on_press: app.play_press_sound()
            on_release: root.open_menu(self)

<ChatScreen>:
    name: 'chat'
    on_enter: self.load_memory_in_thread()
    RelativeLayout:
        Image:
            source: "background.png"
            fit_mode: "fill"
            size: root.size
            pos: root.pos

        BouncingBall:
            id: bouncing_ball
            size_hint: None, None
            size: dp(15), dp(15)

        # The ScrollView is now a direct child of the RelativeLayout and fills the screen.
        # It will be drawn first, so it's in the background.
        ScrollView:
            id: scroll_view
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}
            bar_width: '5dp'
            bar_color: 155/255, 89/255, 182/255, 0.8
            bar_inactive_color: 0.2,0.2,0.2,0

            GridLayout:
                id: chat_container
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: '8dp'
                # Padding is added to push content away from the top and bottom bars.
                # top padding = banner height (50) + spacing (10) = 60
                # bottom padding = input height (50) + spacing (10) = 60
                padding: '12dp', dp(60), '12dp', dp(60)

        # The top banner
        NeonPanel:
            size_hint_y: None
            height: dp(50)
            pos_hint: {'top': 1}
            padding: dp(10), 0, dp(10), 0
            neon_color: 155/255, 89/255, 182/255, 1
            fill_a: 0.45

            NeonSignButton:
                text: '< Back'
                size_hint_x: None
                width: dp(92)
                neon_color: 155/255, 89/255, 182/255, 1
                on_press: app.play_press_sound()
                on_release: app.play_sound_and_change_screen('welcome')
                font_name: "NovaFont"

            Label:
                text: "NOVA Chat"
                font_name: "NovaFont"
                font_size: "18sp"
                color: 1,1,1,0.8
                markup: True

            Widget:

        # The input box (neon panel)
        NeonPanel:
            size_hint_y: None
            height: dp(50)
            pos_hint: {'y': 0}
            spacing: dp(10)
            padding: dp(10)
            neon_color: 155/255, 89/255, 182/255, 1
            fill_a: 0.60

            TextInput:
                id: input_box
                hint_text: "Message NOVA..."
                multiline: False
                on_text_validate: root.send_message()
                background_color: 0, 0, 0, 0
                foreground_color: 1, 1, 1, 1
                cursor_color: 1, 1, 1, 1
                font_size: '12sp'
                font_name: "NovaFont"
                padding: dp(12), dp(8)

            SendButton:
                id: send_button
                on_release: root.send_message()
                pos_hint: {'center_y': 0.5}

<AboutScreen>:
    name: 'about'
    RelativeLayout:
        DataStream:
            id: data_stream
            size_hint: 1, 1
            pos: 0, 0

        Image:
            source: "background.png"
            fit_mode: "fill"
            size: root.size
            pos: root.pos
            opacity: 0.4

        NeonPanel:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(15)
            neon_color: 0.1, 1, 0.9, 1
            fill_a: 0.0  # Transparent to remove green/yellow tint behind text
            glow_a: 0.0  # Remove blue/cyan glow/outline so no color shows behind text

            Label:
                text: "About NOVA"
                font_size: "32sp"
                font_name: "NovaFont"
                size_hint_y: None
                height: self.texture_size[1]
                color: 0.1, 1, 0.9, 1

            ScrollView:
                bar_width: '5dp'
                bar_color: 155/255, 89/255, 182/255, 0.8
                bar_inactive_color: 1,1,1,0.3
                GridLayout:
                    cols: 1
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: '15dp'
                    padding: dp(10), dp(10)

                    Label:
                        text: "[b]Paralogic Engine[/b]"
                        markup: True
                        font_size: "22sp"
                        font_name: "NovaFont"
                        color: 1,1,1,1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None

                    Label:
                        text: "[b]Project Goal[/b]\\nTo develop the Paralogic Engine as a next-generation computational framework capable of dual-phase reasoning and multi-cycle processing. This system extends the boundaries of logic computation, enabling operations on zero, infinity, and unconventional numeric bases, providing a foundation for advanced problem-solving and cognitive augmentation."
                        markup: True
                        font_size: "16sp"
                        font_name: "NovaFont"
                        color: 1,1,1,1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None

                    Label:
                        text: "[b]Breakthroughs & Accomplishments[/b]\\n\\nSuccessfully implemented dual-cycle processing capable of handling complex binary and non-binary logic operations.\\n\\nCreated a working prototype of the Paralogic Engine integrated with an AI-driven reasoning layer.\\n\\nDemonstrated scalable processing for advanced logic operations that traditional systems cannot natively handle.\\n\\nDeveloped a foundational architecture supporting real-time memory, adaptive learning, and cycle-aware decision-making."
                        markup: True
                        font_size: "16sp"
                        font_name: "NovaFont"
                        color: 1,1,1,1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None

                    Label:
                        text: "[b]Future Directions[/b]\\n\\nExpand Paralogic Engine integration with autonomous AI systems to enhance reasoning, memory retention, and situational awareness.\\n\\nAdvance mathematical modeling for zero, infinity, and multi-base operations, unlocking new computational possibilities.\\n\\nEnable decentralized, user-accessible AI frameworks using the Paralogic Engine as the cognitive core.\\n\\nExplore applications in scientific research, simulation, creative AI, and decentralized problem-solving networks."
                        markup: True
                        font_size: "16sp"
                        font_name: "NovaFont"
                        color: 1,1,1,1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None

                    Label:
                        text: "[b]Contact & Support[/b]\\nEmail: rebelcore.class.nova@gmail.com\\nCash App: $rebelcorenova"
                        markup: True
                        font_size: "16sp"
                        font_name: "NovaFont"
                        color: 1,1,1,1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None

            NeonSignButton:
                text: "Back"
                font_name: "NovaFont"
                size_hint: (0.6, None)
                height: dp(50)
                pos_hint: {"center_x": 0.5}
                neon_color: 0.1, 1, 0.9, 1
                on_press: app.play_press_sound()
                on_release: app.play_sound_and_change_screen('welcome')
"""


# --- BUBBLES ---
class ChatBubble(Label): pass


class UserBubble(ChatBubble): pass


class NovaBubble(ChatBubble): pass


class TypingBubble(Label): pass


# --- Neon Sign Button & Panel ---
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
class NeonSignButton(Button):
    neon_color = ListProperty([0.05, 0.95, 1, 1])
    edge_radius = NumericProperty(25)
    glow_a = NumericProperty(1.0)  # overall glow alpha multiplier
    enable_flicker = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # subtle random flicker to mimic neon
        Clock.schedule_interval(self._random_flicker, 0.12)

    def _random_flicker(self, dt):
        if not self.enable_flicker:
            return
        import random
        r = random.random()
        if r < 0.06:  # occasional micro flicker
            try:
                from kivy.animation import Animation
                (Animation(glow_a=0.6, opacity=0.92, duration=0.04)
                 + Animation(glow_a=1.0, opacity=1.0, duration=0.08)).start(self)
            except Exception:
                pass
        elif r < 0.08:  # rare stronger flicker
            try:
                from kivy.animation import Animation
                (Animation(glow_a=0.45, opacity=0.86, duration=0.03)
                 + Animation(glow_a=1.0, opacity=1.0, duration=0.10)).start(self)
            except Exception:
                pass

from kivy.uix.boxlayout import BoxLayout
class NeonPanel(BoxLayout):
    neon_color = ListProperty([155/255.0, 89/255.0, 182/255.0, 1])  # default purple
    edge_radius = NumericProperty(16)
    glow_a = NumericProperty(1.0)
    fill_a = NumericProperty(0.55)  # base body alpha


# --- SCREENS ---
class WelcomeScreen(Screen):
    # Properties driving exit animation (TV-off)
    mask_h = NumericProperty(0)
    line_w = NumericProperty(0)
    line_a = NumericProperty(1.0)

    def on_enter(self):
        # Reset opacity in case we faded out before
        self.opacity = 1
        if not hasattr(self.ids, "particle_layer"):
            return
        self.particles = []
        self.create_particles(25)
        # Store event refs so we can cancel on leave (prevents CPU drain)
        self._evt_particles = Clock.schedule_interval(self.animate_particles, 1 / 60)
        self._evt_title_glow = Clock.schedule_interval(self.animate_title_glow, 1 / 30)
        self.animate_buttons()
        # Slightly reduce glitch frequency to save GPU
        self._evt_glitch = Clock.schedule_interval(self.start_glitch_effect, 1.0)

    def animate_buttons(self):
        enter_button = self.ids.enter_button
        anim_enter = (
                Animation(glow_a=0.65, duration=0.8, t="in_out_sine")
                + Animation(glow_a=1.0, duration=0.8, t="in_out_sine")
        )
        anim_enter.repeat = True
        anim_enter.start(enter_button)

        exit_button = self.ids.exit_button
        anim_exit = (
                Animation(glow_a=0.6, duration=0.9, t="in_out_sine")
                + Animation(glow_a=1.0, duration=0.9, t="in_out_sine")
        )
        anim_exit.repeat = True
        anim_exit.start(exit_button)

    def start_glitch_effect(self, dt):
        # Lower probability reduces GPU spikes while keeping the effect
        if random.random() < 0.06:
            self.trigger_glitch()

    def trigger_glitch(self, *args):
        self.ids.background_image.trigger_glitch()
        Clock.schedule_once(self.reset_glitch, 0.1)

    def reset_glitch(self, *args):
        self.ids.background_image.reset_glitch()

    def on_leave(self):
        # Cancel scheduled events to avoid background CPU usage
        for evt_name in ("_evt_particles", "_evt_title_glow", "_evt_glitch"):
            evt = getattr(self, evt_name, None)
            if evt:
                try:
                    evt.cancel()
                except Exception:
                    pass
                setattr(self, evt_name, None)
        # Clear particles and canvas layer
        if hasattr(self, "particles"):
            self.particles.clear()
        if hasattr(self.ids, "particle_layer"):
            try:
                self.ids.particle_layer.canvas.clear()
            except Exception:
                pass
        # Ensure any static overlay is removed
        if hasattr(self, 'static_overlay'):
            try:
                self.remove_widget(self.static_overlay)
            except Exception:
                pass
            self.static_overlay = None

    def animate_title_glow(self, dt):
        t = time.time()
        r = 0.1 + 0.2 * math.sin(t * 2)
        g = 1
        b = 0.9 + 0.1 * math.cos(t * 3)
        self.ids.welcome_title.color = (r, g, b, 1)

    def create_particles(self, count):
        layer = self.ids.particle_layer
        for _ in range(count):
            size = random.randint(4, 10)
            x, y = random.uniform(0, self.width), random.uniform(0, self.height)
            dx, dy = random.uniform(-1, 1), random.uniform(-0.5, 0.5)
            particle = {"x": x, "y": y, "dx": dx, "dy": dy, "size": size}
            with layer.canvas:
                Color(0, 1, 1, 0.05)
                particle["ellipse"] = Ellipse(pos=(x, y), size=(size, size))
            self.particles.append(particle)

    def animate_particles(self, dt):
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            if p["x"] > self.width:
                p["x"] = 0
            if p["x"] < 0:
                p["x"] = self.width
            if p["y"] > self.height:
                p["y"] = 0
            if p["y"] < 0:
                p["y"] = self.height
            p["ellipse"].pos = (p["x"], p["y"])

    def show_scared_popup(self):
        # Prevent re-entry
        if getattr(self, "_exiting", False):
            return
        self._exiting = True

        # Sound and disable inputs
        App.get_running_app().play_power_down_sound()
        self.ids.exit_button.disabled = True
        self.ids.enter_button.disabled = True

        # 1) Rapid glitch burst
        for i in range(5):
            Clock.schedule_once(lambda dt: self.trigger_glitch(), 0.05 * i)

        # 2) Brief static overlay (~0.30s)
        self.static_overlay = Widget(size=self.size, pos=self.pos)
        self.add_widget(self.static_overlay)
        self.static_event = Clock.schedule_interval(self.draw_static, 1 / 30)
        # stop static shortly after it starts
        def _stop_static(dt):
            try:
                if hasattr(self, 'static_event') and self.static_event:
                    self.static_event.cancel()
            except Exception:
                pass
        Clock.schedule_once(_stop_static, 0.35)

        # 3) TV-off collapse after static finishes
        Clock.schedule_once(self.start_tv_off_animation, 0.35)

    def draw_static(self, dt):
        if not hasattr(self, 'static_overlay'): return
        # Clear the previous frame's static
        self.static_overlay.canvas.clear()
        with self.static_overlay.canvas:
            # Draw several random grey rectangles to simulate static
            for _ in range(100):
                Color(random.random() * 0.5 + 0.5, 1)  # Random grey color
                width = random.randint(int(self.width * 0.1), int(self.width * 0.8))
                height = random.randint(1, 3)
                x = random.randint(0, int(self.width - width))
                y = random.randint(0, int(self.height - height))
                Rectangle(pos=(x, y), size=(width, height))

    def start_tv_off_animation(self, *args):
        # Create overlay for TV-off effect (closing masks + center white line)
        try:
            # Clean any previous overlay
            if hasattr(self, 'exit_overlay') and self.exit_overlay in self.children:
                self.remove_widget(self.exit_overlay)
        except Exception:
            pass

        self.exit_overlay = Widget(size=self.size, pos=self.pos)
        self.add_widget(self.exit_overlay)

        # Initialize properties
        self.mask_h = 0
        self.line_w = self.width
        self.line_a = 0.9

        with self.exit_overlay.canvas:
            # Top mask (black)
            self._col_top = Color(0, 0, 0, 1)
            self._rect_top = Rectangle(pos=(self.x, self.y + self.height), size=(self.width, 0))
            # Bottom mask (black)
            self._col_bottom = Color(0, 0, 0, 1)
            self._rect_bottom = Rectangle(pos=(self.x, self.y), size=(self.width, 0))
            # Center white line
            self._line_color = Color(1, 1, 1, self.line_a)
            self._line_rect = Rectangle(pos=(self.center_x - self.line_w / 2, self.center_y - dp(1)), size=(self.line_w, dp(2)))

        # Update function to sync canvas with properties
        self.bind(mask_h=self._update_exit_canvas, line_w=self._update_exit_canvas, line_a=self._update_exit_canvas,
                  size=self._update_exit_canvas, pos=self._update_exit_canvas)
        # Ensure an immediate layout update
        self._update_exit_canvas()

        # Animate masks closing to center
        anim_close = Animation(mask_h=self.height / 2.0, duration=0.28, t='out_cubic')
        anim_close.bind(on_complete=self._after_close)
        anim_close.start(self)

    def _after_close(self, *args):
        # --- FIX START ---
        # The .bind() method does not return the animation object, so you cannot chain .start()
        # Create the animation, bind the event, and then start it.
        anim = Animation(line_w=0, line_a=0, duration=0.12, t='in_cubic')
        anim.bind(on_complete=self.stop_app_after_effect)
        anim.start(self)
        # --- FIX END ---

    def _update_exit_canvas(self, *args):
        if not hasattr(self, '_rect_top'):
            return
        w, h = self.width, self.height
        mh = max(0, float(self.mask_h))
        # Bottom mask grows upward
        self._rect_bottom.pos = (self.x, self.y)
        self._rect_bottom.size = (w, mh)
        # Top mask grows downward
        self._rect_top.pos = (self.x, self.y + h - mh)
        self._rect_top.size = (w, mh)
        # Center white line
        lw = max(0, float(self.line_w))
        th = dp(2)
        self._line_rect.size = (lw, th)
        self._line_rect.pos = (self.center_x - lw / 2.0, self.center_y - th / 2.0)
        if hasattr(self, '_line_color'):
            self._line_color.a = max(0.0, float(self.line_a))

    def stop_app_after_effect(self, *args):
        # Stop the static effect drawing if active
        try:
            if hasattr(self, 'static_event') and self.static_event:
                self.static_event.cancel()
        except Exception:
            pass
        # Stop the application
        App.get_running_app().stop()

    def open_menu(self, button):
        dropdown = DropDown()
        about_btn = Button(text="About Us", size_hint_y=None, height=dp(44))
        about_btn.bind(on_release=lambda btn: self.go_about(dropdown))
        dropdown.add_widget(about_btn)
        dropdown.add_widget(
            Button(text="[i]Coming Soon[/i]", markup=True, size_hint_y=None, height=dp(44))
        )
        dropdown.add_widget(
            Button(text="[i]Coming Soon[/i]", markup=True, size_hint_y=None, height=dp(44))
        )
        dropdown.open(button)

    def go_about(self, dropdown):
        """Handles the action for the 'About Us' button."""
        dropdown.dismiss()
        App.get_running_app().play_sound_and_change_screen("about")


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._core_lock = Lock()
        self._typing_bubble = None
        self._typing_event = None
        self._dots = 0

    def load_memory_in_thread(self):
        self.ids.input_box.disabled = True
        self.ids.send_button.disabled = True
        threading.Thread(target=self.initialize_core, daemon=True).start()

    def initialize_core(self):
        init_memory()
        Clock.schedule_once(self.on_memory_loaded)

    def on_memory_loaded(self, *args):
        self.ids.input_box.disabled = False
        self.ids.send_button.disabled = False
        App.get_running_app().play_nova_message_sound()
        self.add_bubble("NOVA Online. Type !help if you need it.", is_user=False)

    def send_message(self):
        user_input = self.ids.input_box.text.strip()
        if not user_input: return
        App.get_running_app().play_send_sound()
        self.add_bubble(user_input, is_user=True)
        self.ids.input_box.text = ""
        self.show_typing_bubble()
        threading.Thread(target=self.get_response, args=(user_input,), daemon=True).start()

    def get_response(self, user_input):
        try:
            with self._core_lock:
                response = handle_message(user_input)
        except Exception as e:
            response = f"[Error] {e}"
        Clock.schedule_once(lambda dt: self.deliver_response(response))

    def deliver_response(self, response):
        self.hide_typing_bubble()
        if response:
            App.get_running_app().play_nova_message_sound()
            self.add_bubble(response, is_user=False)

    def show_typing_bubble(self):
        if self._typing_bubble: return
        self._typing_bubble = TypingBubble()
        self._typing_bubble.size_hint_x = None
        self._typing_bubble.width = dp(150)
        self.ids.chat_container.add_widget(self._typing_bubble)
        self.scroll_to_bottom()
        self._typing_event = Clock.schedule_interval(self.update_typing_dots, 0.5)

    def update_typing_dots(self, dt):
        self._dots = (self._dots + 1) % 4
        if self._typing_bubble:
            self._typing_bubble.text = "NOVA is thinking" + "." * self._dots

    def hide_typing_bubble(self):
        if self._typing_bubble:
            self.ids.chat_container.remove_widget(self._typing_bubble)
            self._typing_bubble = None
        if self._typing_event:
            self._typing_event.cancel()
            self._typing_event = None

    def add_bubble(self, text, is_user):
        BubbleClass = UserBubble if is_user else NovaBubble
        bubble = BubbleClass(
            size_hint=(None, None),
            text_size=(self.ids.chat_container.width * 0.8, None)
        )
        bubble.bind(texture_size=bubble.setter('size'))
        # Make bubble responsive to container width changes (reflow like major chat apps)
        def _update_bubble_width(inst, w, b=bubble):
            b.text_size = (w * 0.8, None)
        self.ids.chat_container.bind(width=_update_bubble_width)

        row = BoxLayout(size_hint_y=None, spacing=dp(10))
        bubble.bind(height=row.setter('height'))
        if is_user:
            row.add_widget(Widget())
            row.add_widget(bubble)
        else:
            row.add_widget(bubble)
            row.add_widget(Widget())
        self.ids.chat_container.add_widget(row)

        def set_text_later(dt):
            bubble.text = text
            self.scroll_to_bottom()

        Clock.schedule_once(set_text_later, 0)

    def scroll_to_bottom(self):
        self.ids.scroll_view.scroll_y = 0


# --- AboutScreen ---
class AboutScreen(Screen): pass


# --- Bouncing Ball ---
class BouncingBall(Widget):
    dx = NumericProperty(3)
    dy = NumericProperty(3)
    lines = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.set_random_start, 0)
        self.prev_pos = (self.center_x, self.center_y)
        with self.canvas:
            self.ball_color = Color(0.5, 0, 1, 0.5)
            self.ball = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_interval(self.update, 1 / 60)

    def set_random_start(self, *args):
        if self.parent:
            self.x = random.randint(0, int(self.parent.width - self.width))
            self.y = random.randint(0, int(self.parent.height - self.height))
            self.prev_pos = (self.center_x, self.center_y)

    def update_graphics(self, *args):
        self.ball.pos = self.pos
        self.ball.size = self.size

    def update(self, dt):
        if not self.parent: return
        self.x += self.dx
        self.y += self.dy
        if self.right >= self.parent.width or self.x <= 0: self.dx *= -1
        if self.top >= self.parent.height or self.y <= 0: self.dy *= -1
        cx, cy = self.center_x, self.center_y
        t = time.time()
        r = 0.3 + 0.3 * math.sin(t * 2)
        b = 0.7 + 0.2 * math.cos(t * 3)
        with self.canvas:
            Color(r, 0, b, 0.25)
            line = Line(points=[self.prev_pos[0], self.prev_pos[1], cx, cy], width=dp(2))
            self.lines.append(line)
        self.prev_pos = (cx, cy)


# --- MAIN APP ---
class NovaApp(App):
    def _prime_sound(self, snd, volume=0.2):
        """Prime a sound by setting volume and doing a quick play/stop so it's decoded."""
        if snd:
            snd.volume = volume
            try:
                snd.play()
                snd.stop()
            except Exception:
                pass

    def _play_instant(self, snd):
        """Stop, seek to start, and play to minimize latency."""
        if snd:
            try:
                snd.stop()
                if hasattr(snd, 'seek'):
                    snd.seek(0)
                snd.play()
            except Exception as e:
                print(f"Error playing sound: {e}")


    def build(self):
        # --- SOUND LOADING & PRIMING ---
        # Resolve absolute paths to avoid CWD issues
        try:
            base = sounds_dir if 'sounds_dir' in globals() else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
        except Exception:
            base = 'sounds'
        p_click = os.path.join(base, 'click.wav')
        p_transition = os.path.join(base, 'Transition.wav')
        p_send = os.path.join(base, 'send.wav')
        p_power = os.path.join(base, 'power.wav')
        p_nova = os.path.join(base, 'nova_message.wav')

        print(f"🔊 Loading sounds from: {base}")
        print(f" - click: {p_click}")
        print(f" - transition: {p_transition}")
        print(f" - send: {p_send}")
        print(f" - power: {p_power}")
        print(f" - nova_message: {p_nova}")

        self.press_sound = SoundLoader.load(p_click)
        if not self.press_sound:
            print(f"⚠️ [WARNING] Could not load sound: {p_click}")
        self._prime_sound(self.press_sound, volume=0.2)

        self.transition_sound = SoundLoader.load(p_transition)
        if not self.transition_sound:
            # case-insensitive fallback
            alt = os.path.join(base, 'transition.wav')
            self.transition_sound = SoundLoader.load(alt)
            if not self.transition_sound:
                print(f"⚠️ [WARNING] Could not load sound: {p_transition}")
        self._prime_sound(self.transition_sound, volume=0.25)

        self.send_sound = SoundLoader.load(p_send)
        if not self.send_sound:
            print(f"⚠️ [WARNING] Could not load sound: {p_send}")
        self._prime_sound(self.send_sound, volume=0.25)

        self.power_down_sound = SoundLoader.load(p_power)
        if not self.power_down_sound:
            print(f"⚠️ [WARNING] Could not load sound: {p_power}")
      
        # Slightly higher volume for power-down so it cuts through the glitch/static
        self._prime_sound(self.power_down_sound, volume=0.45)

        self.nova_message_sound = SoundLoader.load(p_nova)
        if not self.nova_message_sound:
            print(f"⚠️ [WARNING] Could not load sound: {p_nova}")
        self._prime_sound(self.nova_message_sound, volume=0.3)

        return Builder.load_string(KV_STRING)

    # --- SOUND PLAYBACK METHODS ---
    def play_press_sound(self):
        self._play_instant(self.press_sound)

    def play_sound_and_change_screen(self, screen_name):
        """Plays the transition sound and schedules the screen change for the next frame."""
        self._play_instant(self.transition_sound)

        def change_screen_callback(dt):
            self.root.current = screen_name

        Clock.schedule_once(change_screen_callback, 0)

    def play_send_sound(self):
        self._play_instant(self.send_sound)

    def play_power_down_sound(self):
        """Plays the power down sound for the exit animation."""
        self._play_instant(self.power_down_sound)

    def play_nova_message_sound(self):
        """Plays the sound for a new message from Nova."""
        self._play_instant(self.nova_message_sound)


if __name__ == '__main__':

    NovaApp().run()

