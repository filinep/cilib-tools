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
import copy
import sys
from cilibReflection import *
from xml.etree import ElementTree
from gi.repository import Gtk
from section import Section
from simulator import Simulator

class CilibTools():
    sections = {"algorithm":None, "problem":None, "measurements":None, "simulation":None}
    tabCount = ""
    filename = ""

    def __init__(self):
        self.gui = Gtk.Builder()
        self.gui.add_from_file("ui/cilib-tools.glade")
        self.gui.connect_signals(self)

        self.keys = self.sections.keys()
        self.keys.sort()

        self.sections["algorithm"] = Section("algorithm", "algorithm.Algorithm")
        self.sections["problem"] = Section("problem", "problem.Problem")
        self.sections["measurements"] = Section("measurements", "simulator.MeasurementSuite")
        self.sections["simulation"] = Simulator(self)

        self.get("sections").append_page(self.sections["algorithm"], Gtk.Label("Algorithms"))
        self.get("sections").append_page(self.sections["problem"], Gtk.Label("Problems"))
        self.get("sections").append_page(self.sections["measurements"], Gtk.Label("Measurments"))
        self.get("sections").append_page(self.sections["simulation"], Gtk.Label("Simulator"))

        self.get("sections").show_all()
        self.comboModel = Gtk.ListStore(str)

    def get(self, name):
        return self.gui.get_object(name)

    def on_open_click(self, widget):
        #TODO check for changes?

        for el in self.keys:
            self.sections[el].store.clear()
            self.sections[el].items = []

        dialog = self.get("fileOpen")

        response = dialog.run()
        f = dialog.get_filename()
        dialog.hide()
        
        if response == 0:
            try:
                self.get("statusbar").get_message_area().get_children()[0].set_text("Opening...")

                self.filename = f
                self.get("window").set_title(self.get("window").get_title() + " - " + self.filename)

                xmlFile = open(self.filename, "rw").read()
                self.xml = ElementTree.fromstring(xmlFile)

                #populate the trees
                for c in self.xml:
                    if c.tag == "measurements":
                        self.recurse_open(c, None, self.sections[c.tag].store)
                    else:
                        for cc in c:
                            if cc.tag == "algorithm" or cc.tag == "problem":
                                self.recurse_open(cc, None, self.sections[cc.tag].store)
                            else:
                                self.sim_open(cc)

                self.get("statusbar").get_message_area().get_children()[0].set_text("Opened")
            except:
                self.on_new_click(None)
                self.get("statusbar").get_message_area().get_children()[0].set_text("Error opening file")
                dialog = Gtk.MessageDialog(self.get("window"), Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Could not parse file...\n" + str(sys.exc_info()))
                dialog.run()
                dialog.destroy()
                print sys.exc_info()

    def sim_open(self, xmlElement):
        if "samples" in xmlElement.attrib.keys():
            sam = xmlElement.attrib["samples"]

        for el in xmlElement:
            if el.tag == "algorithm":
                alg = el.attrib["idref"]
            elif el.tag == "problem":
                prob = el.attrib["idref"]
            elif el.tag == "measurements":
                m = el.attrib["idref"]
            elif el.tag == "output":
                f = el.attrib["file"]
            elif el.tag == "samples":
                sam = el.attrib["value"]

        self.sections["simulation"].store.append([alg, prob, m, sam, f, True, 
                                                self.sections["simulation"].comboModel,
                                                self.sections["simulation"].comboModel,
                                                self.sections["simulation"].comboModel])

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
                    self.sections[xmlElement.tag].items.append(ID)

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
                    if xmlElement.tag in self.keys:
                        default = self.sections[xmlElement.tag].base
                    else:
                        parent = model.get_value(modelElement, 2)
                        methods = cilib.getMethods("net.sourceforge.cilib." + parent)

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
            options = copy.deepcopy(cilib.getMethods("net.sourceforge.cilib." + xmlElement.attrib["class"]))
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
                else:
                    toInsert.append("Primitive")
                    toInsert.append("value")
                    toInsert.append("primitive")

                toInsert.append("")
                toInsert.append(True)
                model.append(modelChild, toInsert)

    def on_new_click(self, widget):
        self.filename = ""
        for el in self.keys:
            self.sections[el].store.clear()
            self.sections[el].items = []

    def on_about_click(self, widget):
        dialog = self.gui.get_object("aboutdialog")
        dialog.run()
        dialog.hide()

    def on_quit_click(self, widget):
        Gtk.main_quit()
        sys.exit(0)

    def on_saveas_click(self, widget):
        self.on_save_click(widget, True)
    
    def on_save_click(self, widget, saveas=False):
        f = self.filename

        if saveas or self.filename == "":
            dialog = self.get("fileSave")
            response = dialog.run()
            f = dialog.get_filename()
            dialog.hide()
        else:
            response = 0

        if response == 0:
            self.filename = f
            self.get("window").set_title(self.get("window").get_title() + " - " + self.filename)

            outFile = open(self.filename, "w")

            outFile.write("""<?xml version="1.0"?>\n""")
            outFile.write("""<!DOCTYPE simulator [\n""")
            outFile.write("""<!ATTLIST algorithm id ID #IMPLIED>\n""")
            outFile.write("""<!ATTLIST problem id ID #IMPLIED>\n""")
            outFile.write("""<!ATTLIST measurements id ID #IMPLIED>\n""")
            outFile.write("""]>\n\n""")
            outFile.write("""<simulator>\n""")

            for el in self.keys:
                self.inc_tab()
                if not el == "measurements":
                    outFile.write("\t<" + el + "s>\n")
                    self.inc_tab()

                root = self.sections[el].store.get_iter_first()
                while root is not None:
                    if el == "simulation":
                        self.sim_save(outFile, root)
                    else:
                        self.recurse_save(outFile, self.sections[el].store, root)
                    root = self.sections[el].store.iter_next(root)

                if not el == "measurements":
                    outFile.write("\t</" + el + "s>\n")
                    self.dec_tab()
                self.dec_tab()

            outFile.write("""</simulator>\n""")
            outFile.close()

    def sim_save(self, f, it):
        row = self.sections["simulation"].store.get(it, 0, 1, 2, 3, 4)
        f.write(self.tabCount + "<simulation samples=\"" + row[3] + "\">\n")
        f.write(self.tabCount + "\t<algorithm idref=\"" + row[0] + "\"/>\n")
        f.write(self.tabCount + "\t<problem idref=\"" + row[1] + "\"/>\n")
        f.write(self.tabCount + "\t<measurements idref=\"" + row[2] + "\"/>\n")
        f.write(self.tabCount + "\t<output format=\"TXT\" file=\"" + row[4] + "\"/>\n")
        f.write(self.tabCount + "</simulation>\n")

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

if __name__ == "__main__":
    app = CilibTools()
    Gtk.main()
