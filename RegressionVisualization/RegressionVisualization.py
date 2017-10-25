import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import csv
from slicer.util import VTKObservationMixin
import platform
import time
import urllib
import shutil
from CommonUtilities import *

#
# RegressionVisualization
#

class RegressionVisualization(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "RegressionVisualization"
    self.parent.categories = ["Shape Regression"]
    self.parent.dependencies = []
    self.parent.contributors = ["Laura Pascal (Kitware Inc.), Beatriz Paniagua (Kitware Inc.)"]
    self.parent.helpText = """
    """
    self.parent.acknowledgementText = """
      This work was supported by NIH NIBIB R01EB021391
      (Shape Analysis Toolbox for Medical Image Computing Projects).
    """

#
# RegressionVisualizationWidget
#

class RegressionVisualizationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    #   Global variables
    #
    self.Logic = RegressionVisualizationLogic()
    self.InputShapes = dict()
    self.RegressionModels = dict()

    #
    #  Interface
    #
    loader = qt.QUiLoader()
    self.moduleName = 'RegressionVisualization'
    scriptedModulesPath = eval('slicer.modules.%s.path' % self.moduleName.lower())
    scriptedModulesPath = os.path.dirname(scriptedModulesPath)
    path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' % self.moduleName)
    qfile = qt.QFile(path)
    qfile.open(qt.QFile.ReadOnly)
    widget = loader.load(qfile, self.parent)
    self.layout = self.parent.layout()
    self.widget = widget
    self.layout.addWidget(widget)

    # Global variables of the Interface
    #   Shape Regression Input
    self.CollapsibleButton_ShapeRegressionInput = self.getWidget('CollapsibleButton_ShapeRegressionInput')
    self.inputDirectoryButton = self.getWidget('DirectoryButton_ShapeRegressionInputDirectory')
    self.lineEdit_shapesRootname = self.getWidget('lineEdit_ShapeRegressionInputRootname')
    self.pushbutton_CreationSequence = self.getWidget('pushButton_CreationSequence')

    #   Sequence Visualization Option
    self.CollapsibleButton_SequenceVisualizationOption = self.getWidget('CollapsibleButton_SequenceVisualizationOption')
    self.selectionOfmodeldisplayoption = self.getWidget('comboBox_selectionOfmodeldisplayoption')
    self.widget_coloroption = self.getWidget('widget_coloroption')
    self.ColorPickerButton_startingColor = self.getWidget('ColorPickerButton_startingColor')
    self.ColorPickerButton_endingColor = self.getWidget('ColorPickerButton_endingColor')
    self.CollapsibleGroupBox_SequenceBrowser = self.getWidget('CollapsibleGroupBox_SequenceBrowser')

    # Connect Functions
    self.CollapsibleButton_ShapeRegressionInput.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_ShapeRegressionInput))
    self.pushbutton_CreationSequence.connect('clicked()', self.onSequenceCreation)

    self.CollapsibleButton_SequenceVisualizationOption.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_SequenceVisualizationOption))

    self.selectionOfmodeldisplayoption.connect('currentIndexChanged(int)', self.onUpdateSequence)
    self.ColorPickerButton_startingColor.connect('clicked()', self.onUpdateColorSequence)
    self.ColorPickerButton_endingColor.connect('clicked()', self.onUpdateColorSequence)

    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # Widget Configuration
    #     Sequence Browser Play Widget Configuration
    self.sequenceBrowserPlayWidget = slicer.qMRMLSequenceBrowserPlayWidget()
    self.CollapsibleGroupBox_SequenceBrowser.layout().addWidget(self.sequenceBrowserPlayWidget)

    ## Sequence Browser Seek Widget Configuration
    self.sequenceBrowserSeekWidget = slicer.qMRMLSequenceBrowserSeekWidget()
    self.CollapsibleGroupBox_SequenceBrowser.layout().addWidget(self.sequenceBrowserSeekWidget)

    ##
    self.modelsequence = slicer.mrmlScene.AddNode(slicer.vtkMRMLSequenceNode())
    self.sequencebrowser = slicer.mrmlScene.AddNode(slicer.vtkMRMLSequenceBrowserNode())
    self.displaynodesequence = slicer.mrmlScene.AddNode(slicer.vtkMRMLSequenceNode())
    self.displaynodesequence.SetHideFromEditors(0)

  def enter(self):
    pass

  def onCloseScene(self, obj, event):
    pass

  # Functions to recover the widget in the .ui file
  def getWidget(self, objectName):
    return self.findWidget(self.widget, objectName)

  def findWidget(self, widget, objectName):
    if widget.objectName == objectName:
      return widget
    else:
      for w in widget.children():
        resulting_widget = self.findWidget(w, objectName)
        if resulting_widget:
          return resulting_widget
    return None

  # Only one tab can be displayed at the same time:
  #   When one tab is opened all the other tabs are closed
  def onSelectedCollapsibleButtonOpen(self, selectedCollapsibleButton):
    if selectedCollapsibleButton.isChecked():
      collapsibleButtonList = [self.CollapsibleButton_ShapeRegressionInput,
                               self.CollapsibleButton_SequenceVisualizationOption]
      for collapsibleButton in collapsibleButtonList:
        collapsibleButton.setChecked(False)
      selectedCollapsibleButton.setChecked(True)


  def onSequenceCreation(self):
    # Remove any sequence already existing
    # TODO

    # Store the shapes in a dictionary
    self.InputShapes = dict()
    inputDirectory = self.inputDirectoryButton.directory.encode('utf-8')
    shapesRootname = self.lineEdit_shapesRootname.text
    if shapesRootname == "":
      warningMessagetext = "No rootname specify!"
      self.warningMessage(warningMessagetext, None)
      return
    for shapeBasename in os.listdir(inputDirectory):
      if not shapeBasename.find(shapesRootname) == -1 and not shapeBasename.find(".vtk") == -1:
        # Store the shape
        number_string = shapeBasename.split(shapesRootname)[1].split(".vtk")[0]
        if number_string.isdigit():
          number_integer = int(number_string)
          self.InputShapes[number_integer] = shapeBasename
        else:
          # TODO: Message to improve
          warningMessagetext = "Rootname not good"
          self.warningMessage(warningMessagetext, None)
          return
    if self.InputShapes == {}:
      # TODO: Message to improve
      warningMessagetext = "No shape found in the folder " + inputDirectory + " with the following rootname " + str(shapesRootname)
      self.warningMessage(warningMessagetext, None)
      return

    # Enable the sequence visualization tab
    self.CollapsibleButton_SequenceVisualizationOption.enabled = True

    # Load the models in Slicer
    self.loadModels()

    # Creation of the sequence
    self.sequenceCreation()

    # Remove the models copied in Slicer
    MRMLUtility.removeMRMLNodes(self.RegressionModels.values())

  def warningMessage(self, text, informativeText):
      messageBox = ctk.ctkMessageBox()
      messageBox.setWindowTitle(' /!\ WARNING /!\ ')
      messageBox.setIcon(messageBox.Warning)
      messageBox.setText(text)
      if not informativeText == None:
        messageBox.setInformativeText(informativeText)
      messageBox.setStandardButtons(messageBox.Ok)
      messageBox.exec_()

  def loadModels(self):
    inputDirectory = self.inputDirectoryButton.directory.encode('utf-8')

    colormapsInCommon = []
    for number, shapeBasename in self.InputShapes.items():
      shapeRootname = shapeBasename.split(".vtk")[0]
      model = MRMLUtility.loadMRMLNode(shapeRootname, inputDirectory, shapeBasename, 'ModelFile')
      self.RegressionModels[number] = model

      numOfArray = model.GetPolyData().GetPointData().GetNumberOfArrays()
      colormapslist = []
      for i in range(0, numOfArray):
        if len(self.RegressionModels) == 1:
          colormapsInCommon.append(model.GetPolyData().GetPointData().GetArray(i).GetName())
        colormapslist.append(model.GetPolyData().GetPointData().GetArray(i).GetName())

      colormapsInCommon = set(colormapslist) & set(colormapsInCommon)

    for colormapInCommon in colormapsInCommon:
      self.selectionOfmodeldisplayoption.addItem(colormapInCommon)

  def sequenceCreation(self):
    print "Sequence Creation"

    for number, model in self.RegressionModels.items():

      # Adding of the models to the model sequence
      self.modelsequence.SetDataNodeAtValue(model, str(number))
      slicer.mrmlScene.RemoveNode(model)

      # Adding of the model display nodes to the model display node sequence
      modeldisplay = slicer.mrmlScene.AddNode(slicer.vtkMRMLModelDisplayNode())

      startingColor = self.ColorPickerButton_startingColor.color
      endingColor = self.ColorPickerButton_endingColor.color
      red = float((startingColor.red() + float((number * (endingColor.red() - startingColor.red()) ) / float(len(self.InputShapes))))/255)
      green = float((startingColor.green() + float((number * (endingColor.green() - startingColor.green()) ) / float(len(self.InputShapes))))/255)
      blue = float((startingColor.blue() + float((number * (endingColor.blue() - startingColor.blue()) ) / float(len(self.InputShapes))))/255)
      modeldisplay.SetColor(red, green, blue)

      slicer.mrmlScene.RemoveNode(modeldisplay)
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))

    # Adding of the sequences to the Sequence Browser
    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.modelsequence.GetID())
    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace default display node that is created automatically
    # by the display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    slicer.mrmlScene.RemoveNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

    # Set the sequence browser for the sequence browser seek widget
    self.sequenceBrowserSeekWidget.setMRMLSequenceBrowserNode(self.sequencebrowser)
    self.sequenceBrowserPlayWidget.setMRMLSequenceBrowserNode(self.sequencebrowser)
    self.sequencebrowser.SetRecording(self.modelsequence, True)

  def onUpdateSequence(self):
    if self.selectionOfmodeldisplayoption.currentText == "Color":
      self.widget_coloroption.show()
      self.onUpdateColorSequence()
    else:
      self.widget_coloroption.hide()
      self.UpdateColorMapSequence()

  def onUpdateColorSequence(self):
    # Update the color of the model contained in the sequence
    self.sequencebrowser.RemoveSynchronizedSequenceNode(self.displaynodesequence.GetID())
    for number, model in self.RegressionModels.items():
      modeldisplay = slicer.mrmlScene.AddNode(slicer.vtkMRMLModelDisplayNode())

      startingColor = self.ColorPickerButton_startingColor.color
      endingColor = self.ColorPickerButton_endingColor.color
      red = float((startingColor.red() + float((number * (endingColor.red() - startingColor.red()) ) / float(len(self.InputShapes))))/255)
      green = float((startingColor.green() + float((number * (endingColor.green() - startingColor.green()) ) / float(len(self.InputShapes))))/255)
      blue = float((startingColor.blue() + float((number * (endingColor.blue() - startingColor.blue()) ) / float(len(self.InputShapes))))/255)
      modeldisplay.SetColor(red, green, blue)
      slicer.mrmlScene.RemoveNode(modeldisplay)
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))

    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace display node that is previously created by the new display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    slicer.mrmlScene.RemoveNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

  def UpdateColorMapSequence(self):
    # Update the color map of the model contained in the sequence
    self.sequencebrowser.RemoveSynchronizedSequenceNode(self.displaynodesequence.GetID())
    for number, model in self.RegressionModels.items():
      modeldisplay = slicer.mrmlScene.AddNode(slicer.vtkMRMLModelDisplayNode())
      modeldisplay.ScalarVisibilityOn()
      modeldisplay.SetActiveScalarName(self.selectionOfmodeldisplayoption.currentText)
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))

    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace display node that is previously created by the new display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    slicer.mrmlScene.RemoveNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

#
# RegressionVisualizationLogic
#
class RegressionVisualizationLogic(ScriptedLoadableModuleLogic):
  """
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self):
    pass

#
# RegressionVisualizationTest
#
class RegressionVisualizationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    self.setUp()
    self.delayDisplay('Starting the tests')
    self.test_RegressionVisualization()

  def test_RegressionVisualization(self):
    pass