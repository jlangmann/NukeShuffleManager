# Remove all knobs
thisNode = nuke.thisNode()
allKnobs = thisNode.knobs()
for knob in allKnobs:
    knobObj = allKnobs[knob]
    if knobObj.Class() == "Boolean_Knob" or knobObj.name() in ("Characters", "Parts"):
        try:
            thisNode.removeKnob(allKnobs[knob])
        except Exception:
            pass

knob = nuke.Text_Knob("Characters", "Characters", "")
thisNode.addKnob(knob)

knobList = []
allLayers = nuke.layers()
chars = [x for x in allLayers if x.startswith("geoMatte_")]
parts = [x for x in allLayers if x.startswith("matteID")]


for layer in chars:
    knob = nuke.Boolean_Knob(layer, layer, layer)
    knob.setFlag(0x1000)
    knob.setValue(0)
    nuke.thisNode().addKnob(knob)
    knobList.append(knob)


knob = nuke.Text_Knob("Parts", "Parts", "")
thisNode.addKnob(knob)


for layer in parts:
    knob = nuke.Boolean_Knob(layer, layer, layer)
    knob.setFlag(0x1000)
    knob.setValue(0)
    nuke.thisNode().addKnob(knob)
    knobList.append(knob)


def doSomething():
     
    thisNode.begin()
    mask = nuke.thisKnob().name()
    if nuke.thisKnob().name() not in nuke.layers():
        thisNode.end()
        return

    matches = [x for x in nuke.allNodes() if x.Class() == "Shuffle" and x["label"].value() == mask]
    if not nuke.thisKnob().value() and matches:
        # deselected mask. Delete it
        node = matches[0]
        # delete all inputs
        for i in range(node.inputs()):
            node.setInput(i, None)

        nuke.delete(node)
        thisNode.end()
        return

    # CHeck to see if it already exists
    if matches:
        return

    mergeNodes = [x for x in nuke.allNodes() if x.Class() == "Merge2"]
    char = True
    if char:
         intermediateMerge = [x for x in mergeNodes if x["type"].value() == "char"][0]
    else:
         intermediateMerge = [x for x in mergeNodes if x["type"].value() == "part"][0]

    newNode = nuke.nodes.Shuffle(label=mask)
    newNode["in"].setValue(mask)
    intermediateMerge.connectInput(0, newNode)
    inputNode = [x for x in nuke.allNodes() if x.Class() == "Input"][0]
    newNode.connectInput(0, inputNode)

    thisNode.end()
   

thisNode.begin()
name="mainMerge"
allNodes = nuke.allNodes()
if name not in [x.name() for x in allNodes]:

    merge = nuke.nodes.Merge2(name=name)
    knob = nuke.Text_Knob("type", "type", "main")
    merge.addKnob(knob)

    charMerge = nuke.nodes.Merge2(label="character")
    charMerge["operation"].setValue("plus")
    knob = nuke.Text_Knob("type", "type", "char")
    charMerge.addKnob(knob)

    partMerge = nuke.nodes.Merge2(label="part")
    partMerge["operation"].setValue("plus")
    knob = nuke.Text_Knob("type", "type", "part")
    partMerge.addKnob(knob)

    outputNodes = [x for x in allNodes if x.Class() == "Output"]
    output = outputNodes[0]
    output.connectInput(0, merge)
    
    merge.setInput(0, None)
    merge.connectInput(0, charMerge)
    merge.connectInput(0, partMerge)


thisNode.end()


nuke.addKnobChanged(doSomething, node=thisNode)