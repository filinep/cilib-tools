import sys
import os
import tempfile
import time
from gi.repository import Gtk, Vte, GLib
from xml.etree import ElementTree

class Simulator(Gtk.Box):
    def __init__(self, tools):
        super(Simulator, self).__init__()
        self.gui = Gtk.Builder()
        self.gui.add_from_file("ui/simulator.glade")

        self.pack_start(self.get("simulator"), True, True, 0)
        self.gui.connect_signals(self)

        self.vte = Vte.Terminal()
        self.vte.connect("child-exited", self.restart_vte)
        self.vte.fork_command_full(Vte.PtyFlags.DEFAULT, "~", ["/bin/bash"], [], GLib.SpawnFlags.CHILD_INHERITS_STDIN, None, None)
        self.send_cmd("PS1=\"#\"")
        self.send_cmd("clear")

        pane = self.get("vteScroll")
        pane.add(self.vte)

        self.store = self.get("store")
        self.comboModel = self.get("comboModel")
        self.tools = tools
        self.items = {"algorithms":self.tools.sections["algorithm"].items,
                      "problems":self.tools.sections["algorithm"].items,
                      "measurements":self.tools.sections["algorithm"].items}

    def get(self, name):
        return self.gui.get_object(name)

    def combo_edited(self, column, path, new_text):
        treeIter = self.store.get_iter(path)

        if type(new_text) == Gtk.TreeIter:
            new_text = self.comboModel.get_value(new_text, 0)

        self.store.set_value(treeIter, self.get("treeview").get_columns().index(column) - 1, new_text)
        column

    def entry_edited(self, column, path, new_text):
        treeIter = self.store.get_iter(path)
        self.store.set_value(treeIter, self.get("treeview").get_columns().index(column) - 1, new_text)

    def populate_combo(self, column, editable, path):
        self.comboModel.clear()

        for i in self.items[column.get_title().lower() + "s"]:
            self.comboModel.append([i])

    def on_add_click(self, button):
        self.store.append(["", "", "", "30", "", True, self.comboModel, self.comboModel, self.comboModel])

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

    def on_run_click(self, button):
        self.send_cmd("cd ~/Desktop/cilib-git")
        self.send_cmd("clear")
        self.store.foreach(self.single_run, None)

    def single_run(self, model, path, it, data):
        row = self.store.get(it, 0, 1, 2, 3, 4, 5)
        if row[5]:
            f = self.create_tempfile(it)
            name = f.name
            self.send_cmd("./simulator.sh " + f.name + "; #" + row[0] + " " + row[1] + " " + row[2])

    def create_tempfile(self, it):
        row = self.store.get(it, 0, 1, 2)
        outFile = tempfile.NamedTemporaryFile(mode="r+", delete=False)

        outFile.write("""<?xml version="1.0"?>\n""")
        outFile.write("""<!DOCTYPE simulator [\n""")
        outFile.write("""<!ATTLIST algorithm id ID #IMPLIED>\n""")
        outFile.write("""<!ATTLIST problem id ID #IMPLIED>\n""")
        outFile.write("""<!ATTLIST measurements id ID #IMPLIED>\n""")
        outFile.write("""]>\n\n""")
        outFile.write("""<simulator>\n""")

        outFile.write("""<algorithms>\n""")
        s = self.tools.sections["algorithm"].store
        self.tools.recurse_save(outFile, s, self.find_idref(s, row[0]))
        outFile.write("""</algorithms>\n""")

        outFile.write("""<problems>\n""")
        s = self.tools.sections["problem"].store
        self.tools.recurse_save(outFile, s, self.find_idref(s, row[1]))
        outFile.write("""</problems>\n""")

        s = self.tools.sections["measurements"].store
        self.tools.recurse_save(outFile, s, self.find_idref(s, row[2]))

        outFile.write("""<simulations>\n""")
        self.tools.sim_save(outFile, it)
        outFile.write("""</simulations>\n""")

        outFile.write("""</simulator>\n""")
        outFile.close()

        return outFile

    def find_idref(self, store, idref):
        it = store.get_iter_first()

        while it is not None:
            row = store.get_value(it, 5)
            if row == idref:
                return it

            it = store.iter_next(it)

        return None

    def restart_vte(self, widget):
        self.vte.fork_command_full(Vte.PtyFlags.DEFAULT, "~", ["/bin/bash"], [],
                                GLib.SpawnFlags.CHILD_INHERITS_STDIN, None, None)

    def send_cmd(self, cmd):
        if not cmd[-1] == "\n":
            cmd = cmd + "\n"

        self.vte.feed_child(cmd, len(cmd))

    def send_text(self, text):
        if not text[-1] == "\n":
            text = text + "\n"

        self.vte.feed(text, len(text))

    def on_window_destroy(self, widget):
        Gtk.main_quit()
        sys.exit(0)

