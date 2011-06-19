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
from cilibReflection import *
from gi.repository import Gtk, Gdk

class Section(Gtk.Box):
    def __init__(self, name, base):
        super(Section, self).__init__()
        self.gui = Gtk.Builder()
        self.gui.add_from_file('../etc/ui/section.glade')

        self.pack_start(self.get('section'), True, True, 0)
        self.gui.connect_signals(self)

        self.comboModel = self.get('comboModel')
        self.name = name
        self.base = base

        self.selected = ''
        self.copied = ''
        self.selectedModel = None
        self.copiedModel = None
        self.items = []

        self.store = self.get('store')

    def view_treeview_popup(self, treeview, event, data=None):
        menu = self.get('treeviewPopup')
        menu.show_all()

        if event is not None:
            button = event.button
        else:
            button = 0

        menu.popup(None, None, None, None, button, event.time)

    def get(self, name):
        return self.gui.get_object(name)

    def combo_edited(self, model, path, new_text):
        treeIter = self.store.get_iter(path)
        self.store.set_value(treeIter, 2, new_text)

    def populate_combo(self, model, editable, path, store=None):
        self.comboModel.clear()

        treeIter = self.store.get_iter(path)
        row = self.store.get(treeIter, 0, 1, 2, 3, 4, 5, 6)

        deps = cilib.getDependents('net.sourceforge.cilib.' + row[4])

        self.comboModel.append(['Default'])
        for d in deps:
            self.comboModel.append([d.replace('net.sourceforge.cilib.', '')])

    def on_cell_changed(self, model, path, new_iter):
        newValue =  self.comboModel.get_value(new_iter, 0)
        treeIter = self.store.get_iter(path)
        parent = self.store.iter_parent(treeIter)

        #if more than one can be added (assuming all add* methods)
        if self.store.get_value(treeIter, 0).startswith('add'):
            row = self.store.get(treeIter, 0, 1, 2, 3, 4, 5, 6)
            self.store.insert_after(parent, treeIter, row)
            #TODO insert defaults-^

        oldValue = self.store.get_value(treeIter, 2)
        self.store.set_value(treeIter, 2, newValue)

        #remove existing children
        while self.store.iter_has_child(treeIter):
            self.store.remove(self.store.iter_children(treeIter))

        if not (newValue == 'Default' or newValue == 'Primitive' or oldValue == newValue):
            methods = cilib.getMethods('net.sourceforge.cilib.' + newValue)
            for m in range(len(methods['methods'])):
                deps = cilib.getDependents(methods['parameters'][m][0])

                if methods['parameters'][m][0] == 'primitive':
                    self.store.append(treeIter, (methods['methods'][m],
                                                 self.comboModel, 'Primitive',
                                                 'value', 'Primitive', '', True))
                else:
                    self.store.append(treeIter, (methods['methods'][m],
                                                 self.comboModel, 'Default',
                                                 'class',
                                                 methods['parameters'][m][0]
                                                    .replace('net.sourceforge.cilib.', ''),
                                                 '', True))

    def row_inserted(self, treeview, path, it):
        treeview.expand_to_path(path)

    def on_copy_click(self, widget):
        self.copied = self.selected
        self.copiedModel = self.selectedModel

    def on_paste_click(self, widget):
        self.copy_subtree(self.copiedModel, self.selectedModel, self.copied,
                          self.selected)

    def on_delete_click(self, widget):
        self.delete_subtree(self.selectedModel, self.selected)

    def on_treeview_click(self, treeview, event, data=None):
        if event.type == Gdk.EventType.BUTTON_RELEASE and event.button == 3:
            selection = treeview.get_selection()

            if selection.count_selected_rows() <= 1:
                path = treeview.get_path_at_pos(int(event.x), int(event.y))
                if path is not None:
                    selection.unselect_all()
                    selection.select_path(path[0])

                    model = treeview.get_model()
                    self.selected = model.get_iter(path[0])
                    self.selectedModel = model

            self.view_treeview_popup(treeview, event, data)

    def on_collapse_click(self, button):
        self.get('treeview').collapse_all()

    def on_expand_click(self, button):
        self.get('treeview').expand_all()

    def on_add_click(self, button):
        entry = self.get('idEntry')
        error = self.get('errorLabel')
        dialog = self.get('getID')
        response = dialog.run()

        if response == 0:
            if entry.get_text() == '':
                error.show()
                self.on_add_click(button)
            else:
                self.store.append(None, 
                    [self.name, self.comboModel, 'Default', 'class', self.base,
                     entry.get_text(), True])
                self.items.append(entry.get_text())
                self.items.sort()
                dialog.hide()
        else:
            dialog.hide()

        entry.set_text('')
        error.hide()

    def copy_subtree(self, src, dest, srcRoot, destRoot):
        newDest = dest.append(destRoot, src.get(srcRoot, 0, 1, 2, 3, 4, 5, 6))

        for i in range(src.iter_n_children(srcRoot)):
            self.copy_subtree(src, dest, src.iter_nth_child(srcRoot, i), newDest)

    def delete_subtree(self, src, root):
        src.remove(root)

