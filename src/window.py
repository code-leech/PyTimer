# window.py
#
# Copyright 2025 code-leech
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk

@Gtk.Template(resource_path='/code/leech/pytimer/window.ui')
class PytimerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PytimerWindow'

    # Template children
    timer_overlay = Gtk.Template.Child('timer_overlay')
    progress_circle = Gtk.Template.Child('progress_circle')
    time_label = Gtk.Template.Child('time_label')
    start_button = Gtk.Template.Child('start_button')
    minutes_spin = Gtk.Template.Child('minutes_spin')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize timer variables
        self.timer_running = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.timeout_id = None

        # Set up the drawing area
        self.progress_circle.set_draw_func(self.draw_timer_arc, None)

        # Connect signals using connect_after to ensure widget is fully initialized
        self.start_button.connect_after('clicked', self._on_start_clicked)
        self.minutes_spin.connect_after('value-changed', self._on_minutes_changed)

        # Add custom CSS for styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .timer-label {
                font-size: 48px;
                font-weight: 300;
            }

            .timer-circle {
                margin: 24px;
            }

            headerbar.tall {
                min-height: 64px;
            }

            button.circular {
                padding: 8px;
                margin: 4px;
                border-radius: 9999px;
            }

            button.closebutton {
                padding: 0;
                margin: 0;
                min-width: 24px;
                min-height: 24px;
                background-color: #ebebeb;
                border-radius: 9999px;
            }

            button.closebutton:hover {
                background-color: #d4d4d4;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Set initial time display
        self._update_time_label()

    def draw_timer_arc(self, area, cr, width, height, data):
        """Draw the circular progress indicator"""
        # Calculate center and radius
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10

        # Draw background circle with modern styling
        cr.set_source_rgba(0.9, 0.9, 0.9, 0.2)  # More subtle background
        cr.set_line_width(8)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.stroke()

        if self.total_seconds > 0:
            # Draw progress arc with modern color
            progress = 1 - (self.remaining_seconds / self.total_seconds)
            cr.set_source_rgb(0.2, 0.6, 1.0)  # Brighter blue for better visibility
            cr.arc(center_x, center_y, radius, -math.pi/2,
                  2 * math.pi * progress - math.pi/2)
            cr.stroke()

    def _on_start_clicked(self, button):
        """Handle start/stop button clicks"""
        if not self.timer_running:
            minutes = self.minutes_spin.get_value_as_int()
            if minutes > 0:
                self.total_seconds = minutes * 60
                self.remaining_seconds = self.total_seconds
                self._start_timer()
                button.set_icon_name("media-playback-stop-symbolic")
        else:
            self._stop_timer()
            button.set_icon_name("media-playback-start-symbolic")

    def _on_minutes_changed(self, spin_button):
        """Handle minutes spinbutton value changes"""
        if not self.timer_running:
            minutes = spin_button.get_value_as_int()
            self.remaining_seconds = minutes * 60
            self.total_seconds = self.remaining_seconds  # Update total seconds when minutes change
            self._update_time_label()
            self.progress_circle.queue_draw()

    def _start_timer(self):
        """Start the timer"""
        self.timer_running = True
        self.timeout_id = GLib.timeout_add_seconds(1, self._update_timer)
        self.minutes_spin.set_sensitive(False)

    def _stop_timer(self):
        """Stop the timer"""
        self.timer_running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.minutes_spin.set_sensitive(True)

    def _update_timer(self):
        """Update timer state - called every second while timer is running"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._update_time_label()
            self.progress_circle.queue_draw()
            return True
        else:
            self._timer_finished()
            return False

    def _update_time_label(self):
        """Update the time display label"""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.time_label.set_label(f"{minutes:02d}:{seconds:02d}")

    def _timer_finished(self):
        """Handle timer completion"""
        self.timer_running = False
        self.start_button.set_icon_name("media-playback-start-symbolic")
        self.minutes_spin.set_sensitive(True)
