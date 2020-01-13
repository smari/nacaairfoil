###
#  Based on NACA_Airfoil_2.py by David Wehr.
#  Original: https://blenderartists.org/t/naca-airfoil-generator/519965/6
#  Changes:
#    - Updated for Blender 2.81
#    - Updated panel
###
bl_info = {
    "name": "Add Airfoil",
    "description": "Creates the profile for the 4-digit NACA series.",
    "author": "David Wehr, Smári McCarthy",
    "version": (0, 0, 3),
    "blender": (2, 81, 0),
    "location": "View3D > Add > Mesh > Airfoil",
    "warning": "",
    "category": "Add Mesh"}

import math as M
import bpy
from bpy.props import (IntProperty, BoolProperty, PointerProperty)

class AirfoilPropSet:
    #Properties that define the airfoil
    # NACA foil number: 5921 -> MPTT
    # M : Max Camber (as percentage of chord)
    # P : Chordwise position of max camber (in tenths of chord)
    # TT: Maximum thickness (as percentage of chord)

    m : IntProperty (
        name = "Maximum Camber",
        description = "Maximum Camber (% of chord)",
        default = 0,
        min = 0,
        max = 9)
    p : IntProperty (
        name = "Camber Position",
        description = "Position of Camber (% of chord)",
        default = 0,
        min = 0,
        max = 9)
    t : IntProperty (
        name = "Thickness",
        description = "Maximum thickness (% of chord)",
        default = 12,
        min = 0,
        max = 99)
    res : IntProperty (
        name = "Resolution",
        description = "Number of x coordinates to calculate for",
        default = 100,
        min = 2)

class NACAAirfoilData(AirfoilPropSet, bpy.types.PropertyGroup):
    isAirfoil : BoolProperty(
        name = "Is it an airfoil?",
        default = True
    )

class NACAAirfoil(AirfoilPropSet, bpy.types.Operator):
    bl_idname = "mesh.make_airfoil"
    bl_label = "NACA Airfoil"
    bl_description = "Creates a 4-digit NACA Airfoil"
    bl_options = {"REGISTER", "UNDO"}

    def calculate_airfoil(self, context):
        """Calculate the airfoil"""
        # Convert percentages to decimals
        m = self.m*0.01
        p = self.p*0.1
        t = self.t*0.01

        # Each x value to calculate for
        x_values = []
        # The camber line y values
        camb_values = []
        # The thickness distribution
        thick_values = []
        # Coordinates for the upper and lower parts of the airfoil
        cords_u = []
        cords_l = []

        # Creates a list of x values
        for iter in range(self.res+1):
            x_values.append((1/self.res) * iter)

        # Calculate the thickness along the chord for each x value
        for x in x_values:
            cnst = t/0.2
            y = cnst*( (0.2969*M.sqrt(x)) - (0.1260*x) - (0.3516*(x**2)) + (0.2843*(x**3)) - (0.1015*(x**4)) )
            thick_values.append(y)

        # For each x value, calculate the location of y for the camber line
        for idx, x in enumerate(x_values):

            #Use a different formula if x is less than or greater than p
            if x > p:
                constant = m/((1-p)**2)
                camb_y = constant *( (1-(2*p)) + (2*p*x) - (x**2) )

                #Angle of the tangent to the curve.  Lets us map the thickness to the camber line
                angle = M.atan(constant * ((2*p) - (2*x)))

                #Determine the final coordinates
                xu = x - (M.sin(angle) * thick_values[idx])
                yu = camb_y + (M.cos(angle) * thick_values[idx])
                xl = x + (M.sin(angle) * thick_values[idx])
                yl = camb_y - (M.cos(angle) * thick_values[idx])

                cords_u.append([xu, yu])
                cords_l.append([xl, yl])

            if x <= p:
                #Create an exception for if p = 0 (Division by zero)
                try:
                    constant = m/(p **2)
                except:
                    constant = 0
                camb_y = constant*((2*p*x) - (x**2))

                angle = M.atan(constant * ((2*p) - (2*x)))

                xu = x - (M.sin(angle) * thick_values[idx])
                yu = camb_y + (M.cos(angle) * thick_values[idx])
                xl = x + (M.sin(angle) * thick_values[idx])
                yl = camb_y - (M.cos(angle) * thick_values[idx])

                cords_u.append([xu, yu])
                cords_l.append([xl, yl])

            camb_values.append(camb_y)

        # Y location to place vertices on
        y = 0

        #List of all the vertices and faces
        vertices = []
        faces = []

        #Add each vertex to the list of vertices
        for index in range(self.res+1):
            vertices.append([cords_u[index][0], y, cords_u[index][1]])
            vertices.append([cords_l[index][0], y, cords_l[index][1]])

        #The basic face
        base = [0, 1, 3, 2]

        #Create the list of faces.
        for index in range(self.res):
            faces.append([i + (2*(index)) for i in base])

        #Create a new mesh and link the vertex and face data to it
        airfoil_mesh = bpy.data.meshes.new("airfoil")
        airfoil_mesh.from_pydata(vertices, [], faces)

        #Update the displayed mesh with the new data
        airfoil_mesh.update()

        #The object name depends on what NACA airfoil it is, so it dynamically
        #changes the object name depending on the parameters
        obj_name = "NACA " + str(int(m*100)) + str(int(p*10)) + str(int(t*100))
        airfoil_obj = bpy.data.objects.new(obj_name, airfoil_mesh)

        #Link object to the scene
        context.scene.collection.objects.link(airfoil_obj)

        bpy.ops.object.select_all(action = "DESELECT")
        airfoil_obj.select_set(True)

    def execute(self, context):
        self.calculate_airfoil(context)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.calculate_airfoil(context)
        return {"FINISHED"}


class BakeNACAAirfoil(bpy.types.Operator):
    """Convert NACA Airfoil to mesh"""
    bl_idname = "mesh.convert_w_mesh"
    bl_label = "Convert Airfoil to regular mesh"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        context.object.data.AirfoilData.isAirfoil = False
        return {'FINISHED'}


class NACAAirfoilPanel(bpy.types.Panel):
    """Creates a Panel in the data context of the properties editor"""
    bl_label = "Airfoil data"
    bl_idname = "DATA_PT_Airfoillayout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return (context.object.type == 'MESH')

    def draw(self, context):
        obj = context.object

        col = self.layout.column(align=True)
        col.prop(AirfoilData, "m", text="Max Camber")
        col.prop(AirfoilData, "p", text="Camber Position")
        col.prop(AirfoilData, "t", text="Thickness")
        col.prop(AirfoilData, "res", text="Resolution")

        self.layout.separator()
        self.layout.operator(operator="mesh.convert_w_mesh", icon='NDOF_DOM')


def add_to_menu(self, context):
    self.layout.operator("mesh.make_airfoil", icon="PLUGIN")


def register():
    bpy.utils.register_class(NACAAirfoilData)
    bpy.types.Mesh.AirfoilData = PointerProperty(type=NACAAirfoilData)
    bpy.utils.register_class(NACAAirfoil)
    bpy.utils.register_class(NACAAirfoilPanel)
    bpy.types.VIEW3D_MT_mesh_add.append(add_to_menu)


def unregister():
    bpy.utils.unregister_class(NACAAirfoilPanel)
    bpy.utils.unregister_class(NACAAirfoil)
    bpy.utils.unregister_class(NACAAirfoilData)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_to_menu)

if __name__ == "__main__":
    register()
