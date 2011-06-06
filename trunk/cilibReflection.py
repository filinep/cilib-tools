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

class CilibReflection:
    classes = {}
    methods = {}

    def __init__(self):
        classFile = open("cilib/classes")
        classesLines = classFile.readlines()

        for cl in classesLines:
            cl = cl.replace("\n", "")
            classesSplit = cl.split(" ")
            if len(classesSplit) > 1:
                self.classes[classesSplit[0]] = classesSplit[1:len(classesSplit)]
            else:
                self.classes[classesSplit[0]] = []

        methodFile = open("cilib/methods")
        methodsLines = methodFile.readlines()

        prev = ""
        for m in methodsLines:
            m = m.replace("\n", "")
            if m[0] == "=":
                mSplit = m.split(" ")
                if m[1:4] == "set":
                    self.methods[prev]["methods"].append(mSplit[0].replace("=set", ""))
                    self.methods[prev]["methods"][-1] = self.methods[prev]["methods"][-1][0].lower() + self.methods[prev]["methods"][-1][1:]
                else:
                    self.methods[prev]["methods"].append(mSplit[0].replace("=", ""))
                self.methods[prev]["parameters"].append([ns.replace("\n", "") for ns in mSplit[1:len(mSplit)]])
            else:
                self.methods[m] = {"methods":[], "parameters":[]}
                prev = m

    def getDependents(self, root):
        try:
            rType = self.classes[root]
        except:
            rType = []
        return rType

    def getMethods(self, root):
        try:
            rType = self.methods[root]
        except:
            rType = {}
        return rType

cilib = CilibReflection()
