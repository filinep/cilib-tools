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
import os
import tempfile
import time
import thread
import signal
import common as Common
from gi.repository import Gtk, Vte, GLib
from xml.etree import ElementTree

class Simulator(Gtk.Box):
    def __init__(self):
        super(Simulator, self).__init__()
        self.gui = Gtk.Builder()
        self.gui.add_from_file('../etc/ui/simulator.glade')

        self.pack_start(self.get('simulator'), True, True, 0)
        self.gui.connect_signals(self)

        self.vte = Vte.Terminal()
        pane = self.get('vteScroll')
        pane.add(self.vte)

        self.working = None
        self.store = self.get('store')
        self.get('visibilityFilter').set_visible_column(7)
        self.comboModel = self.get('comboModel')

    def get(self, name):
        return self.gui.get_object(name)

    def combo_edited(self, column, path, new_text):
        it = [i for i in self.store if i[7]][int(path)]

        if type(new_text) == Gtk.TreeIter:
            new_text = self.comboModel.get_value(new_text, 0)

        it[self.get('treeview').get_columns().index(column) - 1] = new_text

    def entry_edited(self, column, path, new_text):
        it = [i for i in self.store if i[7]][int(path)]
        it[self.get('treeview').get_columns().index(column) - 1] = new_text

    def populate_combo(self, column, editable, path):
        self.comboModel.clear()

        for i in Common.sections[column.get_title().lower()].items:
            self.comboModel.append([i])

    def on_add_click(self, button):
        self.store.append(['', '', '', '30', '', True, '#ffffff', True,
                           self.comboModel, self.comboModel, self.comboModel])

    def on_outputfolder_set(self, widget):
        newFolder = widget.get_filename()
        for i in self.store:
            filename = i[4].split('/')[-1]
            i[4] = os.path.join(newFolder, filename)

    def on_header_toggle(self, w):
        newState = not self.get('runHeader').get_active()
        self.get('runHeader').set_active(newState)
        self.store.foreach(self.toggle_all, newState)

    def toggle_all(self, model, path, it, data):
        if self.store.get_value(it, 7):
            self.store.set_value(it, 5, data)

    def on_run_toggle(self, cell, path):
        it = [i for i in self.store if i[7]][int(path)]
        it[5] = not it[5]

    def on_stop_click(self, button):
        try:
            os.kill(self.working[1], signal.SIGKILL)
            self.working = 'Done'
        except Exception:
            Common.set_status('No simulations running')

    def on_run_click(self, button):
        if self.working is None:
            self.vte.reset(True, True)
            pids = []
            self.store.foreach(self.prepare_run, pids)
            self.collective_run(pids)
        else:
            Common.set_status('Simulations are already running...')

    def collective_run(self, pids):
        for f in pids:
            if not self.working == 'Done':
                self.send_text('\rRunning simulation ' + str(pids.index(f) + 1)
                               + ' of ' + str(len(pids)) + ': ' + f[1] + ' '
                               + f[2] + ' ' + f[3])
                self.working = self.start_sim(f[0])
                working = True

                while working:
                    try:
                        os.kill(self.working[1], 0)
                    except Exception:
                        working = False
                    else:
                        Gtk.main_iteration()

                self.check_folder()
            else:
                break

        if self.working == 'Done':
            self.send_text('\r\nSimulations aborted')
        self.working = None

    def prepare_run(self, model, path, it, data):
        row = self.store.get(it, 0, 1, 2, 3, 4, 5)
        if row[5]:
            f = self.create_tempfile(it)
            data.append((f.name, row[0], row[1], row[2]))

    def create_tempfile(self, it):
        row = self.store.get(it, 0, 1, 2)
        outFile = tempfile.NamedTemporaryFile(mode='r+', delete=False)

        Common.save_xml(outFile, row[0], row[1], row[2], it)

        return outFile

    def check_folder(self):
        for i in self.store:
            f = os.path.join(self.get('outputFolder').get_filename(), i[4])
            if os.path.exists(f) or os.path.exists(i[4]):
                i[6] = '#00dd00'

    def start_sim(self, sim):
        return self.vte.fork_command_full(Vte.PtyFlags.DEFAULT, '.',
                                          ['../bin/simulator.sh', sim], [], 
                                          GLib.SpawnFlags.CHILD_INHERITS_STDIN,
                                          None, None)

    def send_text(self, text):
        if not text[-1] == '\n':
            text = text + '\n'

        self.vte.feed(text, len(text))

    def tree_search(self, editable):
        words = editable.get_text().split()
        for r in self.store:
            found = True
            row = ' '.join([r[i] for i in range(5)])
            for w in words:
                found = found and (row.find(w) > -1)
            r[7] = (found or editable.get_text() == '')

    def clear_search_click(self, entry, icon, data):
        if icon == Gtk.EntryIconPosition.SECONDARY:
            entry.set_text('')

    def on_dimension_remove_click(self, treeSelection):
        data = treeSelection.get_selected()
        if data[1] is not None:
            data[0].remove(data[1])

    def on_dimension_add_click(self, a1):
        self.get('dimGenModel').append(['30'])

    def on_generate_simulations_click(self, button):
        #TODO constraints
        for el in ['algorithm', 'problem', 'measurements']:
            model = self.get(el + 'GenModel')
            model.clear()
            for i in Common.sections[el].items:
                model.append([True, i])

        dialog = self.get('simGeneratorDialog')
        response = dialog.run()
        dialog.hide()

        algs = [i for i in self.get('algorithmGenModel') if i[0]]
        probs = [i for i in self.get('problemGenModel') if i[0] and not i[1][0].isdigit()]
        ms = [i for i in self.get('measurementsGenModel') if i[0]]
        dims = [i for i in self.get('dimGenModel')]

        if response == 0:
            self.generate_probs(probs, dims)
            for m in ms:
                for d in dims:
                    for a in algs:
                        for p in probs:
                            self.store.append([a[1], d[0]+'_'+p[1], m[1],
                                              self.get('samplesEntry').get_text(),
                                              'data/' + d[0] + '_' + p[1] + '_'
                                              + a[1] + '.txt', True, '#ffffff', True,
                                              self.comboModel, self.comboModel,
                                              self.comboModel])

    def generate_probs(self, ids, dims):
        for i in [x[1] for x in ids]:
            it = Common.find_idref(Common.sections['problem'].store, i)
            for d in [x[0] for x in dims]:
                if Common.find_idref(Common.sections['problem'].store, d + '_' + i) is None:
                    newIt = Common.copy_subtree(Common.sections['problem'].store,
                                            Common.sections['problem'].store,
                                            it, None)
                    Common.sections['problem'].store.set_value(newIt, 5, d + '_' + i)
                    domainIt = Common.find_in_store(Common.sections['problem'].store,
                                                    newIt, 0, 'domain')
                    if domainIt is not None:
                        Common.sections['problem'].store.set_value(domainIt, 2,
                            Common.sections['problem'].store.get_value(domainIt, 2)
                                .split('^')[0] + '^' + d)

    def dim_edited(self, cell, path, newText):
        model = self.get('dimGenModel')
        model.set_value(model.get_iter(path), 0, newText)

    def on_gen_toggle(self, model, path):
        it = model.get_iter(path)
        model.set_value(it, 0, not model.get_value(it, 0))

