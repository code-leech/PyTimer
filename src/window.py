import math
import time
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, GLib, Gdk

@Gtk.Template(resource_path='/code/leech/pytimer/window.ui')
class PytimerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PytimerWindow'

    # Template children
    timer_overlay = Gtk.Template.Child('timer_overlay')
    progress_circle = Gtk.Template.Child('progress_circle')
    time_label = Gtk.Template.Child('time_label')
    minutes_spin = Gtk.Template.Child('minutes_spin')
    header_bar = Gtk.Template.Child('header_bar')
    button_box = Gtk.Template.Child('button_box')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize timer variables
        self.timer_running = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.elapsed_time = 0
        self.start_time = 0
        self.timeout_id = None

        # Create buttons programmatically
        self.start_button = Gtk.Button()
        self.start_button.set_icon_name("media-playback-start-symbolic")
        self.start_button.add_css_class("circular")
        self.start_button.add_css_class("raised")
        self.start_button.connect('clicked', self._on_start_clicked)

        self.reset_button = Gtk.Button()
        self.reset_button.set_icon_name("edit-undo-symbolic")
        self.reset_button.add_css_class("circular")
        self.reset_button.add_css_class("small")
        self.reset_button.add_css_class("destructive-action")
        self.reset_button.set_visible(False)
        self.reset_button.connect('clicked', self._on_reset_clicked)

        # Add buttons to GtkFixed and set positions
        self.button_box.put(self.start_button, 15, 0)
        self.button_box.put(self.reset_button, 65, 0)

        # Connect signals
        self.minutes_spin.connect('value-changed', self._on_minutes_changed)

        # Set up drawing area
        self.progress_circle.set_draw_func(self.draw_timer_arc, None)

        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .timer-label { font-size: 48px; font-weight: 300; }
            .button-box { min-width: 300px; }
            button.circular { padding: 4px; margin: 2px; border-radius: 9999px; }
            button.small { padding: 2px; }
            headerbar { padding: 0; min-height: 24px; box-shadow: none; border-bottom: none; }
            window { margin: 0; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Initial setup
        self._update_time_label()
        self._update_start_button_state()

    def _on_reset_clicked(self, button):
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.elapsed_time = 0
        self._update_time_label()
        self.reset_button.set_visible(False)
        self.minutes_spin.set_sensitive(True)
        self.progress_circle.queue_draw()
        self._update_start_button_state()

    def _on_start_clicked(self, button):
        if not self.timer_running:
            if self.total_seconds == 0:
                minutes = self.minutes_spin.get_value_as_int()
                if minutes > 0:
                    self.total_seconds = minutes * 60
                    self.remaining_seconds = self.total_seconds
            if self.remaining_seconds == 0:
                self._on_reset_clicked(None)  # Reset the timer if it has finished naturally
                minutes = self.minutes_spin.get_value_as_int()
                if minutes > 0:
                    self.total_seconds = minutes * 60
                    self.remaining_seconds = self.total_seconds
            self.start_time = time.time() - self.elapsed_time
            self._start_timer()
            button.set_icon_name("media-playback-stop-symbolic")
        else:
            self._stop_timer()
            button.set_icon_name("media-playback-start-symbolic")
            self.reset_button.set_visible(True)

    def draw_timer_arc(self, area, cr, width, height, data):
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10
        cr.set_source_rgba(0.7686, 0.7686, 0.7686, 0.5)  # Converted from #c4c4c4
        cr.set_line_width(8)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()
        if self.total_seconds > 0:
            cr.set_source_rgb(0.2, 0.6, 1.0)
            progress = self.elapsed_time / self.total_seconds
            cr.arc(center_x, center_y, radius, -math.pi/2,
                   2 * math.pi * progress - math.pi/2)
            cr.stroke()

    def _on_minutes_changed(self, spin_button):
        if not self.timer_running:
            minutes = spin_button.get_value_as_int()
            self.remaining_seconds = minutes * 60
            self.total_seconds = self.remaining_seconds
            self._update_time_label()
            self._update_start_button_state()

    def _update_start_button_state(self):
        minutes = self.minutes_spin.get_value_as_int()
        self.start_button.set_sensitive(minutes > 0 or self.remaining_seconds > 0)

    def _start_timer(self):
        self.timer_running = True
        self.timeout_id = GLib.timeout_add(16, self._update_timer)  # Update every ~16ms for 60fps
        self.minutes_spin.set_sensitive(False)
        self.reset_button.set_visible(False)

    def _stop_timer(self):
        self.timer_running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.elapsed_time = time.time() - self.start_time  # Save the elapsed time
        self.minutes_spin.set_sensitive(False)  # Disable minutes_spin when paused
        self._update_start_button_state()

    def _update_timer(self):
        if self.remaining_seconds > 0:
            self.elapsed_time = time.time() - self.start_time
            self.remaining_seconds = self.total_seconds - self.elapsed_time
            self._update_time_label()
            self.progress_circle.queue_draw()
            if self.remaining_seconds > 0:
                return True
            else:
                self._timer_finished()
                return False
        else:
            self._timer_finished()
            return False

    def _update_time_label(self):
        if self.remaining_seconds < 0:
            self.remaining_seconds = 0
        minutes = int(self.remaining_seconds // 60)
        seconds = int(self.remaining_seconds % 60)
        self.time_label.set_label(f"{minutes:02d}:{seconds:02d}")

    def _timer_finished(self):
        self.timer_running = False
        self.start_button.set_icon_name("media-playback-start-symbolic")
        self.minutes_spin.set_sensitive(True)
        self._update_start_button_state()
        self.elapsed_time = 0  # Reset elapsed time when the timer finishes

    def on_close_button_clicked(self, button):
        self.close()
