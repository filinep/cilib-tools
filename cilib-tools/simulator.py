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
        self.gui.add_from_file("../etc/ui/simulator.glade")

        self.pack_start(self.get("simulator"), True, True, 0)
        self.gui.connect_signals(self)

        self.vte = Vte.Terminal()
        pane = self.get("vteScroll")
        pane.add(self.vte)

        self.working = None
        self.pause = False

        self.store = self.get("store")
        self.get("visibilityFilter").set_visible_column(7)

        self.comboModel = self.get("comboModel")

    def get(self, name):
        return self.gui.get_object(name)

    def combo_edited(self, column, path, new_text):
        treeIter = self.store.get_iter(path)

        if type(new_text) == Gtk.TreeIter:
            new_text = self.comboModel.get_value(new_text, 0)

        self.store.set_value(treeIter, self.get("treeview").get_columns().index(column) - 1, new_text)

    def entry_edited(self, column, path, new_text):
        treeIter = self.store.get_iter(path)
        self.store.set_value(treeIter, self.get("treeview").get_columns().index(column) - 1, new_text)

    def populate_combo(self, column, editable, path):
        self.comboModel.clear()

        for i in Common.sections[column.get_title().lower()].items:
            self.comboModel.append([i])

    def on_add_click(self, button):
        self.store.append(["", "", "", "30", "", True, "#ffffff", True,
                           self.comboModel, self.comboModel, self.comboModel])

    def on_outputfolder_set(self, widget):
        print widget.get_filename()

    def on_header_toggle(self, w):
        newState = not self.get("runHeader").get_active()
        self.get("runHeader").set_active(newState)
        self.store.foreach(self.toggle_all, newState)

    def toggle_all(self, model, path, it, data):
        it = self.store.get_iter(path)
        self.store.set_value(it, 5, data)

    def on_run_toggle(self, cell, path):
        it = self.store.get_iter(path)
        self.store.set_value(it, 5, not self.store.get_value(it, 5))

    def on_stop_click(self, button):
        try:
            os.kill(self.working[1], signal.SIGKILL)
            self.working = "Done"
        except Exception:
            Common.set_status("No simulations running")

    def on_run_click(self, button):
        if self.working is None:
            self.vte.reset(True, True)
            pids = []
            self.store.foreach(self.prepare_run, pids)
            self.collective_run(pids)
        else:
            Common.set_status("Simulations are already running...")

    def collective_run(self, pids):
        for f in pids:
            if not self.working == "Done":
                self.send_text("\rRunning simulation " + str(pids.index(f) + 1) + " of " + str(len(pids)) + ": " + f[1] + " " + f[2] + " " + f[3])
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

        if self.working == "Done":
            self.send_text("\r\nSimulations aborted")
        self.working = None

    def prepare_run(self, model, path, it, data):
        row = self.store.get(it, 0, 1, 2, 3, 4, 5)
        if row[5]:
            f = self.create_tempfile(it)
            data.append((f.name, row[0], row[1], row[2]))

    def create_tempfile(self, it):
        row = self.store.get(it, 0, 1, 2)
        outFile = tempfile.NamedTemporaryFile(mode="r+", delete=False)

        Common.save(outFile, row[0], row[1], row[2], it)

        return outFile

    def check_folder(self):
        for i in self.store:
            f = os.path.join(self.get("outputFolder").get_filename(), i[4])
            if os.path.exists(f):
                i[6] = "#00dd00"

    def restart_vte(self, widget):
        self.vte.fork_command_full(Vte.PtyFlags.DEFAULT, "~", ["/bin/bash"], [],
                                GLib.SpawnFlags.CHILD_INHERITS_STDIN, None, None)

    def start_sim(self, sim):
        return self.vte.fork_command_full(Vte.PtyFlags.DEFAULT, ".", ["../bin/simulator.sh", sim], [], GLib.SpawnFlags.CHILD_INHERITS_STDIN, None, None)

    def send_text(self, text):
        if not text[-1] == "\n":
            text = text + "\n"

        self.vte.feed(text, len(text))

    def tree_search(self, editable):
        words = editable.get_text().split()
        for r in self.store:
            found = True
            row = ' '.join([r[i] for i in range(5)])
            for w in words:
                found = found and (row.find(w) > -1)
            r[7] = (found or editable.get_text() == "")

