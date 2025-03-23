# window.py
#
# Copyright 2025 CodeLeech
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
    reset_button = Gtk.Template.Child('reset_button')
    start_button = Gtk.Template.Child('start_button')
    reset_revealer = Gtk.Template.Child('reset_revealer')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize timer variables
        self.timer_running = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.elapsed_time = 0
        self.start_time = 0
        self.timeout_id = None

        # Connect signals
        self.minutes_spin.connect('value-changed', self._on_minutes_changed)
        self.start_button.connect('clicked', self._on_start_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)

        # Set up drawing area
        self.progress_circle.set_draw_func(self.draw_timer_arc, None)

        # Add CSS for styling
        css_provider = Gtk.CssProvider()
        css_data = b"""
            .timer-label { font-size: 48px; font-weight: 600; }
            .button-box { min-width: 300px; }
            button.circular { padding: 4px; margin: 2px; border-radius: 9999px; }
            button.small { padding: 2px; }
            headerbar { padding: 0; min-height: 24px; box-shadow: none; border-bottom: none; }
            window { margin: 0; }

            /* Add margin to the right side of the headerbar's end button */
            .window-margin {
                margin-right: 8px;
            }

            /* Make the reset button REALLY smaller */
            .small-reset-button {
                padding: 0px; /* Reduce padding even more */
                min-width: 25px; /* Override min-width */
                min-height: 25px; /* Override min-height */
                font-size: 0.6em; /* Reduce font size even more */
                border-width: 0px; /* Remove border */
                margin: 0px; /* Remove margin */
            }
        """
        css_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Initial setup
        self._update_time_label()
        self._update_start_button_state()

    def _on_reset_clicked(self, button):
        minutes = self.minutes_spin.get_value_as_int()
        self.remaining_seconds = minutes * 60
        self.total_seconds = self.remaining_seconds
        self.elapsed_time = 0
        self._update_time_label()
        #self.reset_button_revealer.set_reveal_child(False) #Removed
        self.minutes_spin.set_sensitive(True)
        self.progress_circle.queue_draw()
        self._update_start_button_state()
        self.reset_revealer.set_reveal_child(False)
        self.start_button.set_icon_name("media-playback-start-symbolic")


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
        else:
            self._stop_timer()
            #self.reset_button_revealer.set_reveal_child(False) #Removed

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
        self.start_button.set_icon_name("media-playback-pause-symbolic") # Set icon to pause
        self.reset_revealer.set_reveal_child(False) # Ensure reset button is hidden

    def _stop_timer(self):
        self.timer_running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.elapsed_time = time.time() - self.start_time  # Save the elapsed time
        self.minutes_spin.set_sensitive(False)  # Disable minutes_spin when paused
        self._update_start_button_state()
        self.start_button.set_icon_name("media-playback-start-symbolic") # Set icon to start
        self.reset_revealer.set_reveal_child(True) # Always reveal reset button on pause

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

    def _update_time_label(self):
        if self.remaining_seconds < 0:
            self.remaining_seconds = 0
        minutes = int(self.remaining_seconds // 60)
        seconds = int(self.remaining_seconds % 60)
        self.time_label.set_label(f"{minutes:02d}:{seconds:02d}")

    def _timer_finished(self):
        self.timer_running = False
        minutes = self.minutes_spin.get_value_as_int()
        self.remaining_seconds = minutes * 60
        self.total_seconds = self.remaining_seconds
        self._update_time_label()
        self.start_button.set_icon_name("media-playback-start-symbolic") # Set icon to start
        self.minutes_spin.set_sensitive(True)
        self._update_start_button_state()
        self.elapsed_time = 0  # Reset elapsed time when the timer finishes
        self.reset_revealer.set_reveal_child(False) # Ensure reset button is hidden
