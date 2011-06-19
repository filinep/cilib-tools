"""
 * cilib-tools
 * Copyright (C) 2011
 * Filipe Nepomuceno
 *
 * These tools are free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * These tools are distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library; if not, see <http://www.gnu.org/licenses/>.
 """
import sys
import traceback
from gi.repository import Gtk
from section import Section
from simulator import Simulator
import common as Common

class CilibTools():
    filename = ''

    def __init__(self):
        self.gui = Gtk.Builder()
        self.gui.add_from_file('../etc/ui/cilib-tools.glade')
        self.gui.connect_signals(self)

        Common.statusbar = self.get('statusbar')
        Common.window = self.get('window')

        self.keys = sorted(Common.sections.keys())

        Common.sections['algorithm'] = Section('algorithm', 'algorithm.Algorithm')
        Common.sections['problem'] = Section('problem', 'problem.Problem')
        Common.sections['measurements'] = Section('measurements', 'simulator.MeasurementSuite')
        Common.sections['simulation'] = Simulator()

        self.get('sections').append_page(Common.sections['algorithm'], Gtk.Label('Algorithms'))
        self.get('sections').append_page(Common.sections['problem'], Gtk.Label('Problems'))
        self.get('sections').append_page(Common.sections['measurements'], Gtk.Label('Measurments'))
        self.get('sections').append_page(Common.sections['simulation'], Gtk.Label('Simulator'))

        self.get('sections').show_all()

    def get(self, name):
        return self.gui.get_object(name)

    def on_open_click(self, widget):
        #TODO check for changes?
        dialog = self.get('fileOpen')

        response = dialog.run()
        f = dialog.get_filename()
        dialog.hide()
        
        if response == 0:
            Common.set_status('Opening...')
            self.on_new_click(None)
            try:
                self.filename = f
                Common.set_title(self.filename)

                Common.open_xml(self.filename)

                Common.set_status('Opened ' + self.filename)
            except:
                self.on_new_click(None)
                Common.set_status('Error opening file ' + self.filename)
                self.filename = ''
                dialog = Gtk.MessageDialog(self.get('window'), Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                       'Could not parse file...\n\n'
                                       + str(traceback.format_exc()))
                dialog.run()
                dialog.destroy()

    def on_new_click(self, widget):
        self.filename = ''
        Common.set_title('')
        for el in self.keys:
            Common.sections[el].store.clear()
            Common.sections[el].items = []

    def on_about_click(self, widget):
        dialog = self.get('aboutdialog')
        dialog.run()
        dialog.hide()

    def on_quit_click(self, widget):
        #TODO check for changes
        quit = False
        if Common.sections['simulation'].working is not None:
            dialog = Gtk.MessageDialog(self.get('window'), Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO,
                                       'Simulations are busy running. Are you sure you want to quit?')
            r = dialog.run()
            dialog.destroy()

            if r == -8:
                Common.sections['simulation'].on_stop_click(None)
                quit = True
        else:
            quit = True

        if quit:
            Gtk.main_quit()
            sys.exit(0)

    def on_saveas_click(self, widget):
        self.on_save_click(widget, True)

    def on_save_click(self, widget, saveas=False):
        f = self.filename

        if saveas or self.filename == '':
            dialog = self.get('fileSave')
            response = dialog.run()
            f = dialog.get_filename()
            dialog.hide()
        else:
            response = 0

        if response == 0:
            self.filename = f
            Common.set_status('Saving...')
            Common.set_title(self.filename)
            outFile = open(self.filename, 'w')
            Common.save_xml(outFile)
            Common.set_status('Saved to ' + self.filename)

if __name__ == '__main__':
    app = CilibTools()
    Gtk.main()
