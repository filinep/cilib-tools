/**
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
 */
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.IOException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.jar.JarFile;
import java.util.zip.ZipEntry;

public class CilibReflection {
    private HashMap<String, List<String>> dependencies;
    
    public CilibReflection(String jarName)
            throws IOException, ClassNotFoundException {
        dependencies = new HashMap<String, List<String>>();
        
        buildDependencies(jarName);
    }
    
    public List<String> getDependentsOf(String root) {
        if(!root.startsWith("net.sourceforge.cilib")) {
            root = "net.sourceforge.cilib.".concat(root);
        }
            
        return dependencies.get(root);
    }

    private void buildDependencies(String jarFile)
            throws IOException, ClassNotFoundException {
        JarFile jar;
        ArrayList<String> classList = new ArrayList<String>();

        jar = new JarFile(jarFile);
            
        for (Enumeration e = jar.entries(); e.hasMoreElements();) {
            String filename = ((ZipEntry) e.nextElement()).getName();

            if (filename.endsWith(".class") && filename.startsWith("net/sourceforge/cilib") && !filename.contains("$")) {
                filename = filename.replace('\\', '/').substring(0, filename.indexOf(".class"));

                filename = filename.replace('/', '.');
                filename = (filename.startsWith(".") ? filename.substring(1) : filename);

                if (!classList.contains(filename)) {
                    classList.add(filename);
                }
            }
        }

        for(String s1 : classList) {
            Class class1 = getClass().getClassLoader().loadClass(s1);
            ArrayList<String> dependents = new ArrayList<String>();

            for(String s2 : classList) {
                Class class2 = getClass().getClassLoader().loadClass(s2);

                if(class1.isAssignableFrom(class2)
                        && !Modifier.isAbstract(class2.getModifiers())
                        && !Modifier.isInterface(class2.getModifiers())) {
                    dependents.add(s2);
                }
            }

            dependencies.put(s1, dependents);
        }
    }
    
    public void save() {
        try {
            FileWriter fw = new FileWriter("./classes");
            PrintWriter out = new PrintWriter(fw);
            for(String s : dependencies.keySet()) {
                out.print(s);
                for(String s1 : dependencies.get(s)) {
                    out.print(" " + s1);
                }
                out.println();
            }
            out.close();
            
            fw = new FileWriter("./methods");
            out = new PrintWriter(fw);
            for(String s : dependencies.keySet()) {
                out.println(s);
                for(String s1 : getMethods(s)) {
                    out.println("=" + s1);
                }
            }
            out.close();
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
    
    /**
     * 
     * @param className
     * @return A list of strings where each string consists of a space separated list 
     * @throws ClassNotFoundException 
     */
    public List<String> getMethods(String className) throws ClassNotFoundException {
        ArrayList<String> methodsList = new ArrayList<String>();
        
        Class class1 = getClass().getClassLoader().loadClass(className);
        
        Method[] methods = class1.getMethods();
        
        for(Method m : methods) {
            String mName = m.getName();
            boolean add = true;
            
            if((mName.startsWith("set") || mName.startsWith("add")) 
                        && Modifier.isPublic(m.getModifiers())
                        && mName.length() > 3
                        && !mName.contains("Listener")) {
                Class[] params = m.getParameterTypes();
                String paramString = "";
                
                for(Class c : params) {
                    if(c.isPrimitive() || String.class.equals(c)) {
                        paramString += " primitive";
                    } else if(!c.getName().startsWith("net.sourceforge.cilib")) {
                        add = false;
                    } else {
                        paramString += " " + c.getName();
                    }
                }
                
                if(add) {
                    methodsList.add(mName + paramString);
                }
            }
        }
        
        return methodsList;
    }
    
    public static void main(String[] args) {
        try {
            CilibReflection ref = new CilibReflection(args[0]);
            ref.save();
        } catch(Exception e) {
            e.printStackTrace();
        }
    }
}
