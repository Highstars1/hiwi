import bpy
from bpy.props import StringProperty
# import mathutils

# ######
# RobotDesigner imports
from ..core import config, PluginManager, RDOperator, Condition
from .helpers import ModelSelected, NotEditMode, ObjectMode
from ..properties.globals import global_properties
from .helpers import _mat3_to_vec_roll, ModelSelected, SingleSegmentSelected, PoseMode
@RDOperator.Preconditions(ModelSelected, SingleSegmentSelected)
@PluginManager.register_class
class RenameMesh(RDOperator):
    """
    :term:`operator` for renaming the selected muscle


    """
    bl_idname = config.OPERATOR_PREFIX + "rename_muscle"
    bl_label = "Rename active muscle"

    new_name = StringProperty(name="Enter new name:")


    @RDOperator.OperatorLogger
    def execute(self, context):
        bpy.data.objects[global_properties.active_muscle.get(context.scene)].name = self.new_name
        global_properties.active_muscle.set(context.scene, self.new_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def run(cls, new_name=""):
        return super().run(**cls.pass_keywords())



