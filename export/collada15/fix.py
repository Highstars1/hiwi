import xml.etree.cElementTree as etree
# Blender-specific imports (catch exception for sphinx documentation)
import bpy


def fixCollada(in_filename, out_filename, context):
    doc = etree.parse(in_filename)
    root = doc.getroot()

    for obj in [i for i in context.scene.objects if i.type == 'MESH']:
        if obj.parent is not None:
            element = root.find(
                './/{http://www.collada.org/2005/11/COLLADASchema}node[@name="%s"][@type="NODE"]' % obj.name.replace(
                    '.', '_'))
            if element is not None:  # sometimes, element is None
                # Latest discovery: bpy.types.object.matrix_local_inverse()
                # gives only the matrix at the time of parenting!
                # bpy.types.bone.matrix_local() gives the matrix of the bone at rest position!
                ns = "{http://www.collada.org/2005/11/COLLADASchema}"
                matrix = etree.Element(ns + "matrix")
                if obj.parent_bone != "":
                    bone = obj.parent.data.bones[obj.parent_bone]
                    if bone.RobotEditor.jointMode == "REVOLUTE":
                        # TODO: Place the transformation for the joint here!
                        pass

                    matrix.text = " ".join([str(j) for i in bone.matrix_local.inverted() for j in i])
                    matrix.set('sid', 'Inverted')
                    # matrix.text = " ".join([str(j) for i in list(obj.matrix_local_inverse) for j in i])
                    element.insert(0, matrix)
                if obj.parent.RobotEditor.tag == "PHYSICS_FRAME":
                    for parent in root.iter():
                        if element in parent:
                            parent.remove(element)
                            break

    doc.write(out_filename, encoding="UTF-8")
