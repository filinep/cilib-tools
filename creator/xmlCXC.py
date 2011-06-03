#!/usr/bin/python
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
import copy
from cilibReflection import *
from xml.etree import ElementTree
from gi.repository import Gtk, Gdk

class xml_cxc():
    elements = {"algorithm":{"items":[], "store":None, "base":"algorithm.Algorithm"},
                "problem":{"items":[], "store":None, "base":"problem.Problem"},
                "measurements":{"items":[], "store":None, "base":"simulator.MeasurementSuite"},
                "simulation":{"items":[], "store":None, "base":""}}
    cr = CilibReflection()
    filename = ""
    tabCount = ""
    selected = None
    selectedModel = None
    copied = None
    copiedModel = None

    def __init__(self):
        self.gui = Gtk.Builder()
        self.gui.add_from_file("ui/xmlCXC.glade")
        self.gui.connect_signals(self)
        
        Gdk.set_show_events(True)

        #get comboModel = this is where all the combobox options go, we repopulate it for each cell
        self.comboModel = self.gui.get_object("comboModel")

        #save the models for easy access
        for el in self.elements.keys():
            #tag, options, options view, attribute type, default, id, visible
            self.elements[el]["store"] = self.gui.get_object(el + "Model")

    def recurse_open(self, xmlElement, modelElement, model):
        toInsert = [xmlElement.tag, self.comboModel]

        #get info to add to model
        #output is special: has more than 1 attribute
        if xmlElement.tag == "output":
            toInsert.append(xmlElement.attrib["file"])
            toInsert.append("file")
            toInsert.append("primitive")
            toInsert.append("")
            toInsert.append(True)
        elif len(xmlElement.attrib.keys()) > 0:
            ID = ""

            #iterate over remaining attributes
            for k in xmlElement.attrib.keys():
                #save id for later
                if k == "id":
                    ID = xmlElement.attrib[k]
                    self.elements[xmlElement.tag]["items"].append(ID)

                #value and idref are primitives
                elif k == "idref" or k == "value":
                    toInsert.append(xmlElement.attrib[k])
                    toInsert.append(k)
                    toInsert.append("primitive")

                #for class need to get the default base class...
                elif k == "class":
                    toInsert.append(xmlElement.attrib[k])
                    toInsert.append(k)

                    #... over here
                    if xmlElement.tag in self.elements.keys():
                        default = self.elements[xmlElement.tag]["base"]
                    else:
                        parent = model.get_value(modelElement, 2)
                        methods = self.cr.getMethods("net.sourceforge.cilib." + parent)

                        index = methods["methods"].index(xmlElement.tag)
                        default = methods["parameters"][index][0]

                    toInsert.append(default.replace("net.sourceforge.cilib.", ""))

                #assume the rest of the attributes can become method calls, so add them as children
                else:
                    element = ElementTree.Element(k)
                    element.set("value", xmlElement.attrib[k])
                    xmlElement.append(element)
                    del(xmlElement.attrib[k])

            if len(xmlElement.attrib) == 0:
                toInsert.append("")
                toInsert.append("")
                toInsert.append("")

            toInsert.append(ID)
            toInsert.append(True)

        #this is for elements without any info e.g. <simulation>... well that's it i guess
        else:
            toInsert.append("")
            toInsert.append("")
            toInsert.append("")
            toInsert.append("")
            toInsert.append(True)

        #add to model
        modelChild = model.append(modelElement, toInsert)

        #get available options
        if "class" in xmlElement.attrib.keys():
            options = copy.deepcopy(self.cr.getMethods("net.sourceforge.cilib." + xmlElement.attrib["class"]))
        else:
            options = None

        #recurse through children
        for e in xmlElement:
            #keep track of used options
            if options is not None:
                #remove used options, except add* methods cos can have more than 1
                if not e.tag.startswith("add") and e.tag in options["methods"]:
                    del(options["parameters"][options["methods"].index(e.tag)])
                    del(options["methods"][options["methods"].index(e.tag)])

            self.recurse_open(e, modelChild, model)

        #the rest of the options not in the xml file
        if options is not None:
            for m in range(len(options["methods"])):
                toInsert = [options["methods"][m], self.comboModel]

                if not options["parameters"][m][0] == "primitive":
                    toInsert.append("Default")
                    toInsert.append("class")
                    toInsert.append(options["parameters"][m][0].replace("net.sourceforge.cilib.", ""))
                    toInsert.append("")
                    toInsert.append(True)
                else:
                    toInsert.append("Primitive")
                    toInsert.append("value")
                    toInsert.append("primitive")
                    toInsert.append("")
                    toInsert.append(True)

                model.append(modelChild, toInsert)

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

    def on_expand_click(self, widget):
        for el in self.elements.keys():
            self.gui.get_object(el + "Treeview").expand_all()

    def on_collapse_click(self, widget):
        for el in self.elements.keys():
            self.gui.get_object(el + "Treeview").collapse_all()

    def view_treeview_popup(self, treeview, event, data=None):
        menu = self.gui.get_object("treeviewPopup")
        menu.show_all()

        if event is not None:
            button = event.button
        else:
            button = 0

        menu.popup(None, None, None, None, button, event.time)

    def combo_edited(self, model, path, new_text):
        treeIter = model.get_iter(path)
        model.set_value(treeIter, 2, new_text)

    def populate_combo(self, model, editable, path, store=None):
        self.comboModel.clear()

        section = [x for x in self.elements.keys() if self.elements[x]["store"] == model][0]
        treeIter = model.get_iter(path)
        row = model.get(treeIter, 0, 1, 2, 3, 4, 5, 6)

        if not section == "simulation":
            deps = self.cr.getDependents("net.sourceforge.cilib." + row[4])

            self.comboModel.append(["Default"])
            for d in deps:
                self.comboModel.append([d.replace("net.sourceforge.cilib.", "")])
        else:
            if row[0] in self.elements.keys():
                for i in self.elements[row[0]]["items"]:
                    self.comboModel.append([i])

    def on_cell_changed(self, model, path, new_iter):
        newValue =  self.comboModel.get_value(new_iter, 0) #0 means column 0 in combo model
        treeIter = model.get_iter(path)
        parent = model.iter_parent(treeIter)
        section = [x for x in self.elements.keys() if self.elements[x]["store"] == model][0]

        if not section == "simulation":
            #if more than one can be added (assuming all add* methods)
            if model.get_value(treeIter, 0).startswith("add"):
                model.insert_after(parent, treeIter, model.get(treeIter, 0, 1, 2, 3, 4, 5, 6))
                #TODO insert defaults-^

            model.set_value(treeIter, 2, newValue) #2 means column 2 in tree model

            #remove existing children
            while model.iter_has_child(treeIter):
                model.remove(model.iter_children(treeIter))

            if not newValue == "Default" and not newValue == "Primitive":
                methods = self.cr.getMethods("net.sourceforge.cilib." + newValue)
                for m in range(len(methods["methods"])):
                    deps = self.cr.getDependents(methods["parameters"][m][0])

                    if methods["parameters"][m][0] == "primitive":
                        model.append(treeIter, (methods["methods"][m], self.comboModel, "Primitive", "value", "Primitive", "", True))
                    else:
                        model.append(treeIter, (methods["methods"][m], self.comboModel, "Default", "class", methods["parameters"][m][0].replace("net.sourceforge.cilib.", ""), "", True))

    def on_window_destroy(self, widget):
        Gtk.main_quit()
        sys.exit(0)

    def on_new_click(self, widget):
        self.filename = ""
        for el in self.elements.keys():
            self.elements[el]["store"].clear()
            self.elements[el]["items"] = []

    def on_open_click(self, widget):
        #TODO check for changes?

        for el in self.elements.keys():
            self.elements[el]["store"].clear()
            self.elements[el]["items"] = []

        dialog = self.gui.get_object("fileOpen")

        response = dialog.run()
        f = dialog.get_filename()
        dialog.hide()
        
        if response == 0:
            try:
                self.gui.get_object("statusbar").get_message_area().get_children()[0].set_text("Opening...")

                self.filename = f
                self.gui.get_object("window").set_title(self.gui.get_object("window").get_title() + " - " + self.filename)

                xmlFile = open(self.filename, "rw").read()
                self.xml = ElementTree.fromstring(xmlFile)

                #populate the trees
                for c in self.xml:
                    if c.tag == "measurements":
                        self.recurse_open(c, None, self.elements[c.tag]["store"])
                    else:
                        for cc in c:
                            self.recurse_open(cc, None, self.elements[cc.tag]["store"])

                self.gui.get_object("statusbar").get_message_area().get_children()[0].set_text("Opened")
            except:
                self.on_new_click(None)
                self.gui.get_object("statusbar").get_message_area().get_children()[0].set_text("Error opening file")
                dialog = Gtk.MessageDialog(self.gui.get_object("window"), Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not parse file...")
                dialog.run()
                dialog.destroy()
                print sys.exc_info()

    def row_inserted(self, treeview, path, it):
        treeview.expand_to_path(path)

    def new_section(self, section):
        entry = self.gui.get_object("newSectionEntry")
        error = self.gui.get_object("errorLabel")
        dialog = self.gui.get_object("getID")
        response = dialog.run()

        if response == 0:
            if entry.get_text() == "":
                error.set_text("ID cannot be empty")
                self.new_section(section)
            else:
                self.elements[section]["store"].append(None, 
                    [section, self.comboModel, "Default", "class", 
                     self.elements[section]["base"], entry.get_text(), True])
                self.elements[section]["items"].append(entry.get_text())
                self.elements[section]["items"].sort()
                dialog.hide()
        else:
            dialog.hide()

        entry.set_text("")
        error.set_text("")

    def add_new_algorithm(self, widget):
        self.new_section("algorithm")

    def add_new_problem(self, widget):
        self.new_section("problem")

    def add_new_measurements(self, widget):
        self.new_section("measurements")

    def add_new_simulation(self, widget):
        model = self.elements["simulation"]["store"]
        parent = model.append(None, ["simulation", self.comboModel, "", "", 
                     self.elements["simulation"]["base"], "", True])
        model.append(parent, ["algorithm", self.comboModel, "", "idref", "primitive", "", True])
        model.append(parent, ["problem", self.comboModel, "", "idref", "primitive", "", True])
        model.append(parent, ["measurements", self.comboModel, "", "idref", "primitive", "", True])
        model.append(parent, ["samples", self.comboModel, "Primitive", "value", "primitive", "", True])
        model.append(parent, ["output", self.comboModel, "Primitive", "file", "primitive", "", True])

    def on_copy_click(self, widget):
        self.copied = self.selected
        self.copiedModel = self.selectedModel

    def on_paste_click(self, widget):
        self.copy_subtree(self.copiedModel, self.selectedModel, self.copied, self.selected)

    def on_delete_click(self, widget):
        self.delete_subtree(self.selectedModel, self.selected)

    def on_about_click(self, widget):
        dialog = self.gui.get_object("aboutdialog")
        dialog.run()
        dialog.hide()

    def on_saveAs_click(self, widget):
        self.on_save_click(widget, True)
    
    def on_save_click(self, widget, saveas=False):
        f = self.filename

        if saveas or self.filename == "":
            dialog = self.gui.get_object("fileSave")
            response = dialog.run()
            f = dialog.get_filename()
            dialog.hide()
        else:
            response = 0

        if response == 0:
            self.filename = f
            self.gui.get_object("window").set_title(self.gui.get_object("window").get_title() + " - " + self.filename)

            outFile = open(self.filename, "w")

            outFile.write("""<?xml version="1.0"?>\n""")
            outFile.write("""<!DOCTYPE simulator [\n""")
            outFile.write("""<!ATTLIST algorithm id ID #IMPLIED>\n""")
            outFile.write("""<!ATTLIST problem id ID #IMPLIED>\n""")
            outFile.write("""<!ATTLIST measurements id ID #IMPLIED>\n""")
            outFile.write("""]>\n\n""")
            outFile.write("""<simulator>\n""")

            keys = self.elements.keys()
            keys.sort()
            for el in keys:
                self.inc_tab()
                if not el == "measurements":
                    outFile.write("\t<" + el + "s>\n")
                    self.inc_tab()

                root = self.elements[el]["store"].get_iter_first()
                while root is not None:
                    self.recurse_save(outFile, self.elements[el]["store"], root)
                    root = self.elements[el]["store"].iter_next(root)

                if not el == "measurements":
                    outFile.write("\t</" + el + "s>\n")
                    self.dec_tab()
                self.dec_tab()

            outFile.write("""</simulator>\n""")
            outFile.close()

    def recurse_save(self, f, src, root):
        row = src.get(root, 0, 1, 2, 3, 4, 5, 6)
        f.write(self.tab() + "<" + str(row[0]))

        if not row[5] == "":
            f.write(" id=\"" + str(row[5]) + "\"")

        if row[3] == "value":
            f.write(" value=\"" + str(row[2]) + "\"")
        elif row[3] == "":
            pass
        elif row[3] == "idref":
            f.write(" idref=\"" + str(row[2]) + "\"")
        elif row[3] == "file":
            f.write(" format=\"TXT\" file=\"" + str(row[2]) + "\"")
        else:
            f.write(" class=\"" + str(row[2]) + "\"")

        #check if must go to sublevel
        allDefault = True
        for i in range(src.iter_n_children(root)):
            lmnt = src.get_value(src.iter_nth_child(root, i), 2)
            if not (lmnt == "Default" or lmnt == "Primitive" or lmnt == "idref" or lmnt == "file"):
                allDefault = False

        if not allDefault:
            f.write(">\n")

            for i in range(src.iter_n_children(root)):
                child = src.iter_nth_child(root, i)
                lmnt = src.get(child, 2)[0]

                if not (lmnt == "Default" or lmnt == "Primitive"):
                    self.inc_tab()
                    self.recurse_save(f, src, src.iter_nth_child(root, i))
                    self.dec_tab()

            f.write(self.tab() + "</" + str(row[0]) + ">\n")
        else:
            f.write("/>\n")

    def tab(self):
        return self.tabCount

    def inc_tab(self):
        self.tabCount = self.tabCount + "\t"
        return self.tabCount

    def dec_tab(self):
        self.tabCount = self.tabCount[:-1]
        return self.tabCount

    def copy_subtree(self, src, dest, srcRoot, destRoot):
        newDest = dest.append(destRoot, src.get(srcRoot, 0, 1, 2, 3, 4, 5, 6))

        for i in range(src.iter_n_children(srcRoot)):
            self.copy_subtree(src, dest, src.iter_nth_child(srcRoot, i), newDest)

    def delete_subtree(self, src, root):
        src.remove(root)

if __name__ == "__main__":
    app = xml_cxc()
    Gtk.main()
