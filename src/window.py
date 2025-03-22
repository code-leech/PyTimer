import math
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
        self.timeout_id = None

        # Create start button
        self.start_button = Gtk.Button(
            icon_name="media-playback-start-symbolic",
            css_classes=["circular"]
        )
        self.start_button.set_valign(Gtk.Align.END)
        self.start_button.connect('clicked', self._on_start_clicked)
        self.button_box.append(self.start_button)

        # Create reset button
        self.reset_button = Gtk.Button(
            icon_name="view-refresh-symbolic",
            css_classes=["circular", "destructive-action"]
        )
        self.reset_button.set_valign(Gtk.Align.END)
        self.reset_button.connect('clicked', self._on_reset_clicked)
        self.reset_button.set_visible(False)  # Initially hidden
        self.button_box.append(self.reset_button)

        # Set up drawing area
        self.progress_circle.set_draw_func(self.draw_timer_arc, None)

        # Connect signals
        self.minutes_spin.connect('value-changed', self._on_minutes_changed)

        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .timer-label { font-size: 48px; font-weight: 300; }
            button.circular { padding: 4px; margin: 2px; border-radius: 9999px; }
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
        self._update_time_label()
        self.reset_button.set_visible(False)
        self.progress_circle.queue_draw()

    def _on_start_clicked(self, button):
        if not self.timer_running:
            if self.total_seconds == 0:
                minutes = self.minutes_spin.get_value_as_int()
                if minutes > 0:
                    self.total_seconds = minutes * 60
                    self.remaining_seconds = self.total_seconds
            self._start_timer()
            button.set_icon_name("media-playback-stop-symbolic")
        else:
            self._stop_timer()
            button.set_icon_name("media-playback-start-symbolic")
            if self.remaining_seconds > 0:
                self.reset_button.set_visible(True)

    def draw_timer_arc(self, area, cr, width, height, data):
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10
        cr.set_source_rgba(0.9, 0.9, 0.9, 0.2)
        cr.set_line_width(8)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()
        if self.total_seconds > 0:
            cr.set_source_rgb(0.2, 0.6, 1.0)
            progress = 1 - (self.remaining_seconds / self.total_seconds)
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
        self.timeout_id = GLib.timeout_add_seconds(1, self._update_timer)
        self.minutes_spin.set_sensitive(False)

    def _stop_timer(self):
        self.timer_running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.minutes_spin.set_sensitive(True)
        self._update_start_button_state()

    def _update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._update_time_label()
            self.progress_circle.queue_draw()
            return True
        else:
            self._timer_finished()
            return False

    def _update_time_label(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.time_label.set_label(f"{minutes:02d}:{seconds:02d}")

    def _timer_finished(self):
        self.timer_running = False
        self.start_button.set_icon_name("media-playback-start-symbolic")
        self.minutes_spin.set_sensitive(True)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self._update_time_label()
        self.progress_circle.queue_draw()
        self._update_start_button_state()
