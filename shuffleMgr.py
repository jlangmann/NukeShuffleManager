import nuke
import os
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from PySide2.QtWidgets import *
from pyside2uic import compileUi

from nukescripts import panels


# compile a Qt Designer '.ui' file
def loadUiType(uiFilepath):
    import xml.etree.ElementTree as xml
    from cStringIO import StringIO

    # load a .ui file in memory
    parsed = xml.parse(uiFilepath)

    form_class_name = parsed.find('class').text
    base_class_name = parsed.find('widget').get('class')

    # convert the UI file into Python code
    o = StringIO()
    with open(uiFilepath, 'r') as f:
        compileUi(f, o, indent=0)

    # copy over some variables so any import commands are in the correct context
    frame = {}
    for v in ['__file__', '__name__', '__package__']:
        frame[v] = eval(v)
        
    # byte compile and execute the Python code
    exec (compile(o.getvalue(), '<string>', 'exec')) in frame

    # Fetch the base_class and form class based on their type
    # in the xml from designer
    form_class = frame['Ui_%s' % form_class_name]
    base_class = eval(base_class_name)

    return base_class, form_class




base_class, form_class = loadUiType(os.path.join(os.path.dirname(__file__), "maskMgrWidget.ui"))


class ShuffleMgrWindow(base_class, form_class):

    def __init__(self, groupNode=None):
        super(ShuffleMgrWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Manage Shuffle Masks")

        allLayers = nuke.layers()

        self.charComboBox.addItems(allLayers)
        self.cmptComboBox.addItems(allLayers)

        self.addCharBtn.clicked.connect(lambda x: self.addMask(True))
        self.addCmpBtn.clicked.connect(lambda x: self.addMask(False))
        self.delBtn.clicked.connect(self.deleteMask)

        self.__maskList = []
        self.__group = groupNode

        self.__group.begin()
        inputNodes = [x for x in nuke.allNodes() if x.Class() == "Input"]
        self.__input = inputNodes[0]
        # delete the temp shuffle node
        nuke.delete(nuke.toNode("Temp"))
        self.__group.end()


        self.updateUI()


    def makeUI(self):
        return self

    def updateValue(self):
        pass


    def updateUI(self):
        # Get a list of all shuffle nodes
        self.__group.begin()
        shuffleNodes = [x for x in nuke.allNodes() if x.Class() == "Shuffle"]

        self.__maskList = []

        for node in shuffleNodes:
            connections = node.dependent()
            type_ = connections[0]["type"].value() if connections else ""

            self.__maskList.append((node["in"].value(), node.name(), type_))

        characters = []
        parts = []
        for node in shuffleNodes:
            connections = node.dependent()
            type_ = connections[0]["type"].value()
            if type_ == "char":
                characters.append(node)
            elif type_ == "part":
                parts.append(node)

        self.charListWidget.clear()
        self.partListWidget.clear()
        for node in characters:
            item = QListWidgetItem(node["in"].value())
            item.setData(QtCore.Qt.ToolTipRole, node.name())
            self.charListWidget.addItem(item)

        for node in parts:
            item = QListWidgetItem(node["in"].value())
            item.setData( QtCore.Qt.ToolTipRole, node.name())
            self.partListWidget.addItem(item)
        self.__group.end()


    def addMask(self, isChar=True):

        # create shuffle node with selected mask
        self.__group.begin()

        # Connect shuffle to char or cmpt merge
        mergeNodes = [x for x in nuke.allNodes() if x.Class() == "Merge2"]

        if isChar:
            maskVal = self.charComboBox.currentText()
            charMerges = [x for x in mergeNodes if x["type"].value() == "char"]
            if not charMerges:
                # Create node
                intermediateMerge = nuke.nodes.Merge2(label="character")
                intermediateMerge["operation"].setValue("plus")
                knob = nuke.Text_Knob("type", "type", "char")
                intermediateMerge.addKnob(knob)

            else:
                intermediateMerge = charMerges[0]

        else:
            maskVal = self.cmptComboBox.currentText()
            charMerges = [x for x in mergeNodes if x["type"].value() == "part"]
            if not charMerges:
                # Create node
                intermediateMerge = nuke.nodes.Merge2(label="part")
                intermediateMerge["operation"].setValue("plus")
                knob = nuke.Text_Knob("type", "type", "part")
                intermediateMerge.addKnob(knob)

            else:
                intermediateMerge = charMerges[0]

        newNode = nuke.nodes.Shuffle(label=maskVal)
        newNode["in"].setValue(maskVal)
        intermediateMerge.setInput(intermediateMerge.inputs(), newNode)

        newNode.setInput(newNode.inputs(), self.__input)

        mergeNode = [x for x in mergeNodes if x["type"].value() == "main"][0]
        mergeNode.setInput(mergeNode.inputs(), intermediateMerge)

        self.__group.end()

        self.updateUI()

    def deleteMask(self):
        chars = self.charListWidget.selectedItems()
        parts = self.partListWidget.selectedItems()

        self.__group.begin()
        for item in chars + parts:

            name = item.data(QtCore.Qt.ToolTipRole)
            nuke.delete(nuke.toNode(name))
        self.__group.end()

        self.updateUI()


def deselectAll():
    for n in nuke.selectedNodes():
        n['selected'].setValue(False)


def initializeNode():
    deselectAll()
    # Add shuffle to ensure there's only 1 input
    shuffle = nuke.createNode("Shuffle")
    shuffle["name"].setValue("Temp")
    merge = nuke.createNode("Merge2")
    merge.setInput(0, shuffle)
    merge["operation"].setValue("in")
    knob = nuke.Text_Knob("type", "type", "main")
    merge.addKnob(knob)
    merge.setSelected(True)
    shuffle.setSelected(True)
    group = nuke.collapseToGroup()
    customKnob = nuke.PyCustom_Knob("ShuffleTable", "", "shuffleMgr.ShuffleMgrWindow(nuke.thisNode())")
    group.addKnob(customKnob)

"""
import tableModel
reload(tableModel)
reload(shuffleMgr)
import shuffleMgr

a = shuffleMgr.NukeTestWindow()
a.show()
"""









