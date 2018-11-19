# #####
# This file is part of the RobotDesigner of the Neurorobotics subproject (SP10)
# in the Human Brain Project (HBP).
# It has been forked from the RobotEditor (https://gitlab.com/h2t/roboteditor)
# developed at the Karlsruhe Institute of Technology in the
# High Performance Humanoid Technologies Laboratory (H2T).
# #####

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# #####
#
# Copyright (c) 2016, FZI Forschungszentrum Informatik
#
# Changes:
#   2014      : Stefan Ulbrich (FZI), Igor Peric (FZI Forschungszentrum Informatik)
#       URDF import/export implemented
#   2016-01-15: Stefan Ulbrich (FZI)
#       Major refactoring. Integrated into complex plugin framework.
#
# ######
"""
Sphinx-autodoc tag
"""

# ######
# System imports
# import os
# import sys
# import math

# ######
# Blender imports
import bpy
from bpy.props import StringProperty
# import mathutils

# ######
# RobotDesigner imports
# from ..core import config, PluginManager
from ..core.operators import RDOperator
from .helpers import ModelSelected, ObjectMode
from .segments import SelectSegment

# from .. import export


class Traverse(RDOperator):
    """
    :term:`operator` for updating the :term:`robot models` after parameters changed.
    If a :term:`segment` name is given it will proceed recursively.

    **Requirements:**

    **Effects:**
    """


    @RDOperator.Postconditions(ModelSelected, ObjectMode)
    @RDOperator.OperatorLogger
    #    @RDOperator.Postconditions(ModelSelected)
    #    @Preconditions(ModelSelected)
    def execute(self, context):
        current_mode = bpy.context.object.mode

        # arm = bpy.data.armatures[armatureName]

        # armature_data_ame = bpy.data.objects[self.model_name].data.name # conversion to operator
        armature_data_ame = context.active_object.data.name

        if self.segment_name:
            segment_name = bpy.data.armatures[armature_data_ame].bones[self.segment_name].name
        else:
            segment_name = bpy.data.armatures[armature_data_ame].bones[0].name

        SelectSegment.run(segment_name=self.segment_name)

        if not bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.RD_Bone:
            self.logger.info("Not updated (not a RD segment): %s", segment_name)
            return

        # local variables for updating the constraints
        joint_axis = bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.axis
        min_rot = bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.theta.min
        max_rot = bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.theta.max
        jointMode = bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.jointMode
        jointValue = bpy.data.armatures[armature_data_ame].bones[segment_name].RobotEditor.theta.value

        matrix, joint_matrix = bpy.data.armatures[armature_data_ame].bones[
            segment_name].RobotEditor.getTransform()

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        editbone = bpy.data.armatures[armature_data_ame].edit_bones[
            bpy.data.armatures[armature_data_ame].bones[segment_name].name]
        editbone.use_inherit_rotation = True

        if editbone.parent is not None:
            transform = editbone.parent.matrix.copy()
            matrix = transform * matrix

        pos = matrix.to_translation()
        axis, roll = _mat3_to_vec_roll(matrix.to_3x3())

        editbone.head = pos
        editbone.tail = pos + axis
        editbone.roll = roll

        editbone.length = 0.1

        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

        # update pose
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        pose_bone = bpy.context.object.pose.bones[segment_name]
        pose_bone.matrix_basis = joint_matrix

        if jointMode == 'REVOLUTE':
            if 'RobotEditorConstraint' not in pose_bone.constraints:
                bpy.ops.pose.constraint_add(type='LIMIT_ROTATION')
                bpy.context.object.pose.bones[segment_name].constraints[
                    0].name = 'RobotEditorConstraint'
            constraint = \
                [i for i in pose_bone.constraints if i.type == 'LIMIT_ROTATION'][0]
            constraint.name = 'RobotEditorConstraint'
            constraint.owner_space = 'LOCAL'
            constraint.use_limit_x = True
            constraint.use_limit_y = True
            constraint.use_limit_z = True
            constraint.min_x = 0.0
            constraint.min_y = 0.0
            constraint.min_z = 0.0
            constraint.max_x = 0.0
            constraint.max_y = 0.0
            constraint.max_z = 0.0
            if joint_axis == 'X':
                constraint.min_x = radians(min_rot)
                constraint.max_x = radians(max_rot)
            elif joint_axis == 'Y':
                constraint.min_y = radians(min_rot)
                constraint.max_y = radians(max_rot)
            elif joint_axis == 'Z':
                constraint.min_z = radians(min_rot)
                constraint.max_z = radians(max_rot)
        # -------------------------------------------------------
        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

        children_names = [i.name for i in
                          bpy.data.armatures[armature_data_ame].bones[
                              segment_name].children]
        for child_name in children_names:
            UpdateSegments.run(segment_name=child_name, recurse=self.recurse)

        SelectSegment.run(segment_name=segment_name)

        return {'FINISHED'}


# # todo to be replaced completely by plugin structure
#
# @PluginManager.register_class
# class importURDF(RDOperator):
#     """
#     :ref:`operator` for ...
#
#     **Requirements:**
#
#     **Effects**
#     """
#     bl_idname = config.OPERATOR_PREFIX + "urdfimport"
#     bl_label = "Import URDF XML"
#     filepath = StringProperty(subtype='FILE_PATH')
#
#     @classmethod
#     def run(cls, filepath=""):
#         return super().run(**cls.pass_keywords())
#
#     @classmethod
#     def poll(cls, context):
#         return check_conditions(ObjectMode)
#
#     @OperatorLogger
#     @Postconditions(ModelSelected, ObjectMode)
#     def execute(self, context):
#         export.urdf.import_(self.filepath)
#         return {'FINISHED'}
#
#     def invoke(self, context, event):
#         context.window_manager.fileselect_add(self)
#         return {'RUNNING_MODAL'}
#
#
# @PluginManager.register_class
# class exportURDF(bpy.types.Operator):
#     """
#     :ref:`operator` for ...
#
#     **Requirements:**
#
#     **Effects**
#     """
#     bl_idname = config.OPERATOR_PREFIX + "urdfexport"
#     bl_label = "Export URDF XML"
#     filepath = StringProperty(subtype='FILE_PATH')
#
#     @classmethod
#     def run(cls, filepath=""):
#         return super().run(**cls.pass_keywords())
#
#     @classmethod
#     def poll(cls, context):
#         return check_conditions(ModelSelected, ObjectMode)
#
#     @OperatorLogger
#     @Postconditions(ModelSelected, ObjectMode)
#     def execute(self, context):
#         print("Mode: ", context.mode)
#         if context.mode != 'OBJECT':
#             bpy.ops.object.mode_set(mode='OBJECT') #switch_to_object_mode('INVOKE_DEFAULT')
#         export.urdf.urdf_export.export(self.filepath)
#         return {'FINISHED'}
#
#     def invoke(self, context, event):
#         context.window_manager.fileselect_add(self)
#         return {'RUNNING_MODAL'}
