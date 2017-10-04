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
    self.CollapsibleButton_Sequence = self.getWidget('CollapsibleButton_Sequence')
    self.lineEdit_shapesRootname = self.getWidget('lineEdit_ShapeRegressionInputRootname')
    self.pushbutton_CreationSequence = self.getWidget('pushButton_CreationSequence')

    # Connect Functions
    self.CollapsibleButton_ShapeRegressionInput.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_ShapeRegressionInput))
    self.pushbutton_CreationSequence.connect('clicked()', self.onSequenceCreation)

    self.CollapsibleButton_Sequence.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_Sequence))


    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # Widget Configuration
    #     Sequence Browser Play Widget Configuration
    self.sequenceBrowserPlayWidget = slicer.qMRMLSequenceBrowserPlayWidget()
    self.CollapsibleButton_Sequence.layout().addWidget(self.sequenceBrowserPlayWidget)
    self.sequenceBrowserPlayWidget.enabled = False
    self.sequenceBrowserPlay_pushButton_VcrFirst = self.sequenceBrowserPlayWidget.children()[1]
    self.sequenceBrowserPlay_pushButton_VcrPrevious = self.sequenceBrowserPlayWidget.children()[2]
    self.sequenceBrowserPlay_pushButton_VcrPlayPause = self.sequenceBrowserPlayWidget.children()[3]
    self.sequenceBrowserPlay_pushButton_VcrNext = self.sequenceBrowserPlayWidget.children()[4]
    self.sequenceBrowserPlay_pushButton_VcrLast = self.sequenceBrowserPlayWidget.children()[5]
    self.sequenceBrowserPlay_pushButton_VcrPlayPause.connect('clicked()', self.playpauseSequence)
    self.play = False
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
                               self.CollapsibleButton_Sequence]
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

    # Enable the sequence Browser Play Widget GUI
    self.sequenceBrowserPlayWidget.enabled = True

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

    for number, shapeBasename in self.InputShapes.items():
      shapeRootname = shapeBasename.split(".vtk")[0]
      model = MRMLUtility.loadMRMLNode(shapeRootname, inputDirectory, shapeBasename, 'ModelFile')
      self.RegressionModels[number] = model


  def sequenceCreation(self):
    print "Sequence Creation"

    for number, model in self.RegressionModels.items():

      # Adding of the models to the model sequence
      self.modelsequence.SetDataNodeAtValue(model, str(number))
      slicer.mrmlScene.RemoveNode(model)

      # Adding of the model display nodes to the model display node sequence
      modeldisplay = slicer.mrmlScene.AddNode(slicer.vtkMRMLModelDisplayNode())
      color = float(number / float(len(self.InputShapes)))
      modeldisplay.SetColor(1, 0, color)
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

# Play/Pause the sequence thank to the sequence browser play widget
  def playpauseSequence(self):
    print "Play/Pause the Sequence"

    self.play = not self.play
    self.sequenceBrowserPlayWidget.enabled = True

    if self.play :
      # Play the sequence
      self.sequencebrowser.PlaybackActiveOn()
    elif not self.play:
      # Pause the sequence
      self.sequencebrowser.PlaybackActiveOff()

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