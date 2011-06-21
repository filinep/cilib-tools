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
from gi.repository import Gtk
from xml.etree import ElementTree
from cilibReflection import *

header = """<?xml version="1.0"?>
<!DOCTYPE simulator [
<!ATTLIST algorithm id ID #IMPLIED>
<!ATTLIST problem id ID #IMPLIED>
<!ATTLIST measurements id ID #IMPLIED>
]>\n\n"""

sections = {
    'algorithm':None,
    'problem':None,
    'measurements':None,
    'simulation':None
    }

statusbar = None
window = None
tabs = ''

def set_status(string):
    if statusbar is not None:
        statusbar.get_message_area().get_children()[0].set_text(string)

def set_title(string):
    if window is not None:
        window.set_title('CILib-Tools - ' + string)

def save_xml(outFile, alg=None, prob=None, m=None, sim=None):
    global sections
    if not None in [alg, prob, m, sim]:
        individuals = {
            'algorithm': find_idref(sections['algorithm'].store, alg),
            'problem': find_idref(sections['problem'].store, prob),
            'measurements': find_idref(sections['measurements'].store, m),
            'simulation': sim
            }

    keys = sorted(sections.keys())

    outFile.write(header)
    outFile.write('<simulator>\n')

    for el in keys:
        inc_tab()
        if not el == 'measurements':
            outFile.write('\t<' + el + 's>\n')
            inc_tab()

        if not None in [alg, prob, m, sim]:
            recurse_save(outFile, sections[el].store, individuals[el], el)
        else:
            root = sections[el].store.get_iter_first()
            while root is not None:
                recurse_save(outFile, sections[el].store, root, el)
                root = sections[el].store.iter_next(root)

        if not el == 'measurements':
            outFile.write('\t</' + el + 's>\n')
            dec_tab()
        dec_tab()

    outFile.write('''</simulator>\n''')
    outFile.close()

def recurse_save(f, src, root, el):
    if el == 'simulation':
        row = src.get(root, 0, 1, 2, 3, 4)
        f.write(tab() + '<simulation samples=\"' + row[3] + '\">\n')
        f.write(tab() + '\t<algorithm idref=\"' + row[0] + '\"/>\n')
        f.write(tab() + '\t<problem idref=\"' + row[1] + '\"/>\n')
        f.write(tab() + '\t<measurements idref=\"' + row[2] + '\"/>\n')
        f.write(tab() + '\t<output format=\"TXT\" file=\"' + row[4] + '\"/>\n')
        f.write(tab() + '</simulation>\n')
    else:
        row = src.get(root, 0, 1, 2, 3, 4, 5, 6)
        f.write(tab() + '<' + str(row[0]))

        if not row[5] == '':
            f.write(' id=\"' + str(row[5]) + '\"')

        if row[3] == 'value':
            f.write(' value=\"' + str(row[2]) + '\"')
        elif row[3] == '':
            pass
        elif row[3] == 'idref':
            f.write(' idref=\"' + str(row[2]) + '\"')
        else:
            f.write(' class=\"' + str(row[2]) + '\"')

        #check if must go to sublevel
        allDefault = True
        for i in range(src.iter_n_children(root)):
            lmnt = src.get_value(src.iter_nth_child(root, i), 2)
            if not (lmnt == 'Default' or lmnt == 'Primitive' or lmnt == 'idref'):
                allDefault = False

        if not allDefault:
            f.write('>\n')

            for i in range(src.iter_n_children(root)):
                child = src.iter_nth_child(root, i)
                lmnt = src.get(child, 2)[0]

                if not (lmnt == 'Default' or lmnt == 'Primitive'):
                    inc_tab()
                    recurse_save(f, src, src.iter_nth_child(root, i), el)
                    dec_tab()

            f.write(tab() + '</' + str(row[0]) + '>\n')
        else:
            f.write('/>\n')

def inc_tab():
    global tabs
    tabs = tabs + '\t'

def dec_tab():
    global tabs
    tabs = tabs[:-1]

def tab():
    global tabs
    return tabs

def find_idref(store, idref):
    it = store.get_iter_first()

    while it is not None:
        row = store.get_value(it, 5)
        if row == idref:
            return it

        it = store.iter_next(it)

    return None

def find_in_store(store, it, column, term):
    while it is not None:
        if store.get_value(it, column) == term:
            return it

        ret = None
        if store.iter_n_children(it) > 0:
            ret = find_in_store(store, store.iter_nth_child(it, 0), column, term)

        if ret is None:
            it = store.iter_next(it)
        else:
            return ret
    return None

def open_xml(f):
    xmlFile = open(f, 'rw').read()
    xml = ElementTree.fromstring(xmlFile)

    #populate the trees
    for c in xml:
        if c.tag == 'measurements':
            recurse_open(c, None, sections[c.tag].store, c.tag)
        else:
            for cc in c:
                recurse_open(cc, None, sections[cc.tag].store, cc.tag)

def recurse_open(xmlElement, modelElement, model, el):
    global sections
    keys = sorted(sections.keys())

    if el == 'simulation':
        if 'samples' in xmlElement.attrib.keys():
            sam = xmlElement.attrib['samples']

        for e in xmlElement:
            if e.tag == 'algorithm':
                alg = e.attrib['idref']
            elif e.tag == 'problem':
                prob = e.attrib['idref']
            elif e.tag == 'measurements':
                m = e.attrib['idref']
            elif e.tag == 'output':
                f = e.attrib['file']
            elif e.tag == 'samples':
                sam = e.attrib['value']

        model.append([alg, prob, m, sam, f, True, '#ffffff', True,
                     sections[el].comboModel, sections[el].comboModel,
                     sections[el].comboModel])
    else:
        toInsert = [xmlElement.tag, Gtk.ListStore(str)]

        #get info to add to model
        #output is special: has more than 1 attribute
        if xmlElement.tag == 'output':
            toInsert.append(xmlElement.attrib['file'])
            toInsert.append('file')
            toInsert.append('primitive')
            toInsert.append('')
            toInsert.append(True)
        elif len(xmlElement.attrib.keys()) > 0:
            ID = ''

            #iterate over remaining attributes
            for k in xmlElement.attrib.keys():
                #save id for later
                if k == 'id':
                    ID = xmlElement.attrib[k]
                    sections[xmlElement.tag].items.append(ID)

                #value and idref are primitives
                elif k == 'idref' or k == 'value':
                    toInsert.append(xmlElement.attrib[k])
                    toInsert.append(k)
                    toInsert.append('primitive')

                #for class need to get the default base class...
                elif k == 'class':
                    toInsert.append(xmlElement.attrib[k])
                    toInsert.append(k)

                    #... over here
                    if xmlElement.tag in keys:
                        default = sections[xmlElement.tag].base
                    else:
                        parent = model.get_value(modelElement, 2)
                        methods = cilib.getMethods('net.sourceforge.cilib.' + parent)

                        index = methods['methods'].index(xmlElement.tag)
                        default = methods['parameters'][index][0]

                    toInsert.append(default.replace('net.sourceforge.cilib.', ''))

                #assume the rest of the attributes can become method calls,
                #so add them as children
                else:
                    element = ElementTree.Element(k)
                    element.set('value', xmlElement.attrib[k])
                    xmlElement.append(element)
                    del(xmlElement.attrib[k])

            if len(xmlElement.attrib) == 0:
                toInsert.append('')
                toInsert.append('')
                toInsert.append('')

            toInsert.append(ID)
            toInsert.append(True)

        #this is for elements without any info e.g. <simulation>...
        #well that's it i guess
        else:
            toInsert.append('')
            toInsert.append('')
            toInsert.append('')
            toInsert.append('')
            toInsert.append(True)

        #add to model
        modelChild = model.append(modelElement, toInsert)

        #get available options
        if 'class' in xmlElement.attrib.keys():
            options = copy.deepcopy(cilib.getMethods('net.sourceforge.cilib.'
                                                + xmlElement.attrib['class']))
        else:
            options = None

        #recurse through children
        for e in xmlElement:
            #keep track of used options
            if options is not None:
                #remove used options, except add* methods cos can have more than 1
                if not e.tag.startswith('add') and e.tag in options['methods']:
                    del(options['parameters'][options['methods'].index(e.tag)])
                    del(options['methods'][options['methods'].index(e.tag)])

            recurse_open(e, modelChild, model, el)

        #the rest of the options not in the xml file
        if options is not None:
            for m in range(len(options['methods'])):
                toInsert = [options['methods'][m], Gtk.ListStore(str)]

                if not options['parameters'][m][0] == 'primitive':
                    toInsert.append('Default')
                    toInsert.append('class')
                    toInsert.append(options['parameters'][m][0]
                                        .replace('net.sourceforge.cilib.', ''))
                else:
                    toInsert.append('Primitive')
                    toInsert.append('value')
                    toInsert.append('primitive')

                toInsert.append('')
                toInsert.append(True)
                model.append(modelChild, toInsert)

def copy_subtree(src, dest, srcRoot, destRoot):
    newDest = dest.append(destRoot, src.get(srcRoot, 0, 1, 2, 3, 4, 5, 6))

    for i in range(src.iter_n_children(srcRoot)):
        copy_subtree(src, dest, src.iter_nth_child(srcRoot, i), newDest)

    return newDest

def delete_subtree(src, root):
    src.remove(root)
