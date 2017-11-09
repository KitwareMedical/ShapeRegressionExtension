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

class colorMapStruct(object):
  def __init__(self):
    self.colormapName = None
    self.numberOfComponents = None
    self.colormapTypes = []
    self.sequenceRange = dict()
    self.initialSequenceRange = dict()
    self.colorbars = dict()

class colorBarPointStruct(object):
  def __init__(self):
    self.pos = None
    self.r = None
    self.g = None
    self.b = None

class colorBarStruct(object):
  def __init__(self):
    self.colorPointList = []

  def setInitialColorBarPointList(self):
    initialColorBarPoint = {0:qt.QColor(qt.Qt.blue), 0.5:qt.QColor(qt.Qt.white), 1:qt.QColor(qt.Qt.red)}
    for position, color in initialColorBarPoint.items():
      colorbarpoint = colorBarPointStruct()
      colorbarpoint.r = color.red()/255
      colorbarpoint.g = color.green()/255
      colorbarpoint.b = color.blue()/255
      colorbarpoint.pos = position
      self.colorPointList.append(colorbarpoint)

  # {Magnitude:[colorBarPoint1, colorBarPoint2, colorBarPoint3], X:, ...}

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
    self.commonColorMapInformation = dict()
    self.colorNodeDict = dict()
    self.currentSequenceColorMap = None

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
    self.comboBox_ColorMapChoice = self.getWidget('comboBox_ColorMapChoice')
    self.comboBox_3DColorMapChoice = self.getWidget('comboBox_3DColorMapChoice')
    self.lineEdit_ColorMapSequenceMin = self.getWidget('lineEdit_ColorMapSequenceMin')
    self.lineEdit_ColorMapSequenceMax = self.getWidget('lineEdit_ColorMapSequenceMax')
    ##      Custom Coloring
    self.stackedWidget_CustomColoring = self.getWidget('stackedWidget_CustomColoring')
    self.page_ColorMapCustom = self.getWidget('page_ColorMapCustom')
    ###       Custom Color Map
    self.CollapsibleGroupBox_CustomColorBar = self.getWidget('CollapsibleGroupBox_CustomColorBar')
    self.doubleSpinBox_ColorSequenceMin = self.getWidget('doubleSpinBox_ColorSequenceMin')
    self.doubleSpinBox_ColorSequenceMax = self.getWidget('doubleSpinBox_ColorSequenceMax')
    self.pushButton_ResetColorSequenceRange = self.getWidget('pushButton_ResetColorSequenceRange')
    self.ScalarsToColorsWidget = self.getWidget('ScalarsToColorsWidget')
    self.CollapsibleGroupBox_CustomScalarBar = self.getWidget('CollapsibleGroupBox_CustomScalarBar')
    self.checkBox_DisplayScalarBar = self.getWidget('checkBox_DisplayScalarBar')
    self.lineEdit_TitleScalarBar = self.getWidget('lineEdit_TitleScalarBar')
    self.ColorPickerButton_LabelsColorScalarBar = self.getWidget('ColorPickerButton_LabelsColorScalarBar')
    self.checkBox_LabelBoldStyleScalarBar = self.getWidget('checkBox_LabelBoldStyleScalarBar')
    self.checkBox_LabelShadowStyleScalarBar = self.getWidget('checkBox_LabelShadowStyleScalarBar')
    self.checkBox_LabelItalicStyleScalarBar = self.getWidget('checkBox_LabelItalicStyleScalarBar')
    ###       Custom Solid Color
    self.ColorPickerButton_startingColor = self.getWidget('ColorPickerButton_startingColor')
    self.ColorPickerButton_endingColor = self.getWidget('ColorPickerButton_endingColor')
    self.groupBox_SequenceBrowser = self.getWidget('groupBox_SequenceBrowser')

    # Connect Functions
    self.CollapsibleButton_ShapeRegressionInput.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_ShapeRegressionInput))
    self.pushbutton_CreationSequence.connect('clicked()', self.onSequenceCreation)

    self.CollapsibleButton_SequenceVisualizationOption.connect('clicked()',
                                                  lambda: self.onSelectedCollapsibleButtonOpen(
                                                    self.CollapsibleButton_SequenceVisualizationOption))

    self.comboBox_ColorMapChoice.connect('currentIndexChanged(int)', self.onUpdateSequenceColorMap)
    self.comboBox_3DColorMapChoice.connect('currentIndexChanged(int)', self.onUpdateSequence3DColorMap)
    self.doubleSpinBox_ColorSequenceMin.connect('valueChanged(double)', self.onModificationSequenceRange)
    self.doubleSpinBox_ColorSequenceMax.connect('valueChanged(double)', self.onModificationSequenceRange)
    self.pushButton_ResetColorSequenceRange.connect('clicked()', self.onResetSequenceRange)
    self.checkBox_DisplayScalarBar.connect('stateChanged(int)', self.onDisplayScalarBar)
    self.lineEdit_TitleScalarBar.connect('editingFinished()', self.onUpdateTitleScalarBar)
    self.ColorPickerButton_LabelsColorScalarBar.connect('clicked()', self.onUpdateColorLabelsScalarBar)
    self.checkBox_LabelBoldStyleScalarBar.connect('clicked(bool)', self.onUpdateLabelsStyleScalarBar)
    self.checkBox_LabelShadowStyleScalarBar.connect('clicked(bool)', self.onUpdateLabelsStyleScalarBar)
    self.checkBox_LabelItalicStyleScalarBar.connect('clicked(bool)', self.onUpdateLabelsStyleScalarBar)
    self.ColorPickerButton_startingColor.connect('clicked()', self.onUpdateSequenceSolidColor)
    self.ColorPickerButton_endingColor.connect('clicked()', self.onUpdateSequenceSolidColor)

    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # Widget Configuration
    #     Sequence Browser Play Widget Configuration
    self.sequenceBrowserPlayWidget = slicer.qMRMLSequenceBrowserPlayWidget()
    self.groupBox_SequenceBrowser.layout().addWidget(self.sequenceBrowserPlayWidget)

    ## Sequence Browser Seek Widget Configuration
    self.sequenceBrowserSeekWidget = slicer.qMRMLSequenceBrowserSeekWidget()
    self.groupBox_SequenceBrowser.layout().addWidget(self.sequenceBrowserSeekWidget)

    # Global Variable Initialization
    self.modelsequence = MRMLUtility.createNewMRMLNode("modelsequence", slicer.vtkMRMLSequenceNode())
    self.sequencebrowser = MRMLUtility.createNewMRMLNode("sequencebrowser", slicer.vtkMRMLSequenceBrowserNode())
    self.displaynodesequence = MRMLUtility.createNewMRMLNode("displaynodesequence", slicer.vtkMRMLSequenceNode())
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

    # Configuration of the color maps of the models contained in the sequence
    self.colorMapsConfiguration()

    # Creation of the sequence
    self.sequenceCreation()

    # Remove the models in Slicer
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

  def colorMapsConfiguration(self):
    ColorMapNameInCommon = self.Logic.findColorMapInCommon(self.RegressionModels)

    for colormapName in ColorMapNameInCommon:
      ##  Add the color map name to the combobox
      self.comboBox_ColorMapChoice.addItem(colormapName)

      ##  Store of the information about each color map (name, number of components, sequence range, etc ...)
      self.commonColorMapInformation[colormapName] = self.Logic.storeColormapInformation(colormapName, self.RegressionModels)

  def sequenceCreation(self):
    print "Sequence Creation"

    for number, model in self.RegressionModels.items():

      # Adding of the models to the model sequence
      self.modelsequence.SetDataNodeAtValue(model, str(number))
      MRMLUtility.removeMRMLNode(model)

      # Adding of the model display nodes to the model display node sequence
      modeldisplay = MRMLUtility.createNewMRMLNode(model.GetName() + "-displayNode", slicer.vtkMRMLModelDisplayNode())

      startingColor = self.ColorPickerButton_startingColor.color
      endingColor = self.ColorPickerButton_endingColor.color
      red = float((startingColor.red() + float((number * (endingColor.red() - startingColor.red()) ) / float(len(self.InputShapes))))/255)
      green = float((startingColor.green() + float((number * (endingColor.green() - startingColor.green()) ) / float(len(self.InputShapes))))/255)
      blue = float((startingColor.blue() + float((number * (endingColor.blue() - startingColor.blue()) ) / float(len(self.InputShapes))))/255)
      modeldisplay.SetColor(red, green, blue)

      MRMLUtility.removeMRMLNode(modeldisplay)
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))

    # Adding of the sequences to the Sequence Browser
    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.modelsequence.GetID())
    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace default display node that is created automatically
    # by the display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    MRMLUtility.removeMRMLNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

    # Set the sequence browser for the sequence browser seek widget
    self.sequenceBrowserSeekWidget.setMRMLSequenceBrowserNode(self.sequencebrowser)
    self.sequenceBrowserPlayWidget.setMRMLSequenceBrowserNode(self.sequencebrowser)
    self.sequencebrowser.SetRecording(self.modelsequence, True)

  ### Update Sequence Color Functions

  def onUpdateSequenceColorMap(self):
    if self.comboBox_ColorMapChoice.currentText == "Solid Color":
      self.removeColorNodes()
      # UI
      self.CollapsibleGroupBox_CustomColorBar.setChecked(False)
      self.CollapsibleGroupBox_CustomScalarBar.setChecked(False)
      self.stackedWidget_CustomColoring.setCurrentIndex(1)
      self.comboBox_3DColorMapChoice.blockSignals(True)
      self.comboBox_3DColorMapChoice.clear()
      self.comboBox_3DColorMapChoice.enabled = False
      self.comboBox_3DColorMapChoice.blockSignals(False)
      self.lineEdit_ColorMapSequenceMin.setText("")
      self.lineEdit_ColorMapSequenceMax.setText("")
      self.checkBox_DisplayScalarBar.setCheckState(qt.Qt.Unchecked)
      # # Update colors of the models contained in the sequence
      self.onUpdateSequenceSolidColor()
      self.currentSequenceColorMap = None
    else:
      colormapName = self.comboBox_ColorMapChoice.currentText
      self.stackedWidget_CustomColoring.setCurrentIndex(0)
      self.CollapsibleGroupBox_CustomColorBar.setChecked(True)
      self.CollapsibleGroupBox_CustomScalarBar.setChecked(True)
      if self.commonColorMapInformation[self.comboBox_ColorMapChoice.currentText].numberOfComponents == 3:
        self.comboBox_3DColorMapChoice.blockSignals(True)
        self.comboBox_3DColorMapChoice.enabled = True
        self.comboBox_3DColorMapChoice.clear()
        colormapTypes = self.commonColorMapInformation[self.comboBox_ColorMapChoice.currentText].colormapTypes
        self.comboBox_3DColorMapChoice.addItems(colormapTypes)
        self.comboBox_3DColorMapChoice.blockSignals(False)
        colormapType = self.comboBox_3DColorMapChoice.currentText
      else:
        self.comboBox_3DColorMapChoice.blockSignals(True)
        self.comboBox_3DColorMapChoice.enabled = False
        self.comboBox_3DColorMapChoice.clear()
        self.comboBox_3DColorMapChoice.blockSignals(False)
        colormapType = self.commonColorMapInformation[self.comboBox_ColorMapChoice.currentText].colormapTypes[0]

      # Update Sequence Range
      self.setColorMapSequenceRangeSpinBoxes(colormapName, colormapType)
      self.setColorMapInitialSequenceRangeSpinBoxes(colormapName, colormapType)

      # Save colorbar
      if not self.currentSequenceColorMap == None:
        self.SaveColorBarInformation(self.currentSequenceColorMap)
      self.currentSequenceColorMap = colormapName + "-" + colormapType

      # Update the color transfer function of the sequence
      DistanceMapTFunc = self.UpdateColorTransferFunction(colormapName, colormapType)
      # Update colors of the models contained in the sequence
      self.UpdateSequenceColorMap(colormapName, colormapType, DistanceMapTFunc)
      # Update Color Bar
      self.UpdateColorBar(DistanceMapTFunc)
      # Update scalar bar if already displayed
      self.UpdateScalarBar()

  def onUpdateSequence3DColorMap(self):
    colormapName = self.comboBox_ColorMapChoice.currentText
    colormapType = self.comboBox_3DColorMapChoice.currentText
    self.setColorMapSequenceRangeSpinBoxes(colormapName, colormapType)
    self.setColorMapInitialSequenceRangeSpinBoxes(colormapName, colormapType)
    # Save ColorBar
    if not self.currentSequenceColorMap == None:
      self.SaveColorBarInformation(self.currentSequenceColorMap)
    self.currentSequenceColorMap = colormapName + "-" + colormapType
    # Update the color transfer function of the sequence
    DistanceMapTFunc = self.UpdateColorTransferFunction(colormapName, colormapType)
    # Update colors of the models contained in the sequence
    self.UpdateSequenceColorMap(colormapName, colormapType, DistanceMapTFunc)
    # Update Color Bar
    self.UpdateColorBar(DistanceMapTFunc)
    # Update scalar bar if already displayed
    self.UpdateScalarBar()

  # Update the models' color contained in the sequence according
  def onUpdateSequenceSolidColor(self):
    # Update the color of the model contained in the sequence
    self.sequencebrowser.RemoveSynchronizedSequenceNode(self.displaynodesequence.GetID())
    for number, model in self.RegressionModels.items():
      modeldisplay = MRMLUtility.createNewMRMLNode(model.GetName() + "-displayNode", slicer.vtkMRMLModelDisplayNode())

      startingColor = self.ColorPickerButton_startingColor.color
      endingColor = self.ColorPickerButton_endingColor.color
      red = float((startingColor.red() + float((number * (endingColor.red() - startingColor.red()) ) / float(len(self.InputShapes))))/255)
      green = float((startingColor.green() + float((number * (endingColor.green() - startingColor.green()) ) / float(len(self.InputShapes))))/255)
      blue = float((startingColor.blue() + float((number * (endingColor.blue() - startingColor.blue()) ) / float(len(self.InputShapes))))/255)
      modeldisplay.SetColor(red, green, blue)
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))
      MRMLUtility.removeMRMLNode(modeldisplay)

    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace display node that is previously created by the new display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    MRMLUtility.removeMRMLNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

  def removeColorNodes(self):
    MRMLUtility.removeMRMLNodes(self.colorNodeDict.values())

  # Update the color transfer function of the sequence
  def UpdateColorTransferFunction(self, colormapName, colormapType):
    colorbar = self.commonColorMapInformation[colormapName].colorbars[colormapType]
    sequenceRange = self.commonColorMapInformation[colormapName].sequenceRange[colormapType]
    DistanceMapTFunc = vtk.vtkColorTransferFunction()
    for colorbarpoint in colorbar.colorPointList:
      x = sequenceRange[0] + (sequenceRange[1] - sequenceRange[0]) * colorbarpoint.pos
      DistanceMapTFunc.AddRGBPoint(x, colorbarpoint.r, colorbarpoint.g, colorbarpoint.b)
    DistanceMapTFunc.AdjustRange(sequenceRange)
    DistanceMapTFunc.SetColorSpaceToRGB()
    DistanceMapTFunc.SetVectorModeToMagnitude()
    return DistanceMapTFunc

  def UpdateSequenceColorMap(self, colormapName, colormapType, DistanceMapTFunc):

    # Update the title of the scalar bar
    self.lineEdit_TitleScalarBar.setText(colormapName + " - " + colormapType)

    # Update the color map of the model contained in the sequence
    if self.commonColorMapInformation[colormapName].numberOfComponents == 3:
      colormapName = colormapType + colormapName
    self.sequencebrowser.RemoveSynchronizedSequenceNode(self.displaynodesequence.GetID())
    self.removeColorNodes()
    for number, model in self.RegressionModels.items():
      modeldisplay = MRMLUtility.createNewMRMLNode(model.GetName() + "-displayNode", slicer.vtkMRMLModelDisplayNode())
      modeldisplay.ScalarVisibilityOn()
      modeldisplay.SetActiveScalarName(colormapName)
      self.colorNodeDict[number] = MRMLUtility.createNewMRMLNode("BlueWhiteRed", slicer.vtkMRMLProceduralColorNode())
      self.colorNodeDict[number].SetAndObserveColorTransferFunction(DistanceMapTFunc)
      modeldisplay.SetScalarRangeFlag(slicer.vtkMRMLModelDisplayNode.UseColorNodeScalarRange)
      modeldisplay.SetAndObserveColorNodeID(self.colorNodeDict[number].GetID())
      self.displaynodesequence.SetDataNodeAtValue(modeldisplay, str(number))
      MRMLUtility.removeMRMLNode(modeldisplay)

    self.sequencebrowser.AddSynchronizedSequenceNodeID(self.displaynodesequence.GetID())

    # Replace display node that is previously created by the new display proxy node
    modelProxyNode = self.sequencebrowser.GetProxyNode(self.modelsequence)
    modelDisplayProxyNode = self.sequencebrowser.GetProxyNode(self.displaynodesequence)
    MRMLUtility.removeMRMLNode(modelProxyNode.GetDisplayNode())
    modelProxyNode.SetAndObserveDisplayNodeID(modelDisplayProxyNode.GetID())

  ### Sequence Range Functions

  def onModificationSequenceRange(self):
    colormapName = self.comboBox_ColorMapChoice.currentText
    colormapType = self.comboBox_3DColorMapChoice.currentText
    # Save colorbar
    self.SaveColorBarInformation(self.currentSequenceColorMap)
    # Update the sequence Range according of the
    self.UpdateSequenceRange(colormapName, colormapType)
    # Update the color transfer function of the sequence
    DistanceMapTFunc = self.UpdateColorTransferFunction(colormapName, colormapType)
    # Update colors of the models contained in the sequence
    self.UpdateSequenceColorMap(colormapName, colormapType, DistanceMapTFunc)
    # Update Color Bar
    self.UpdateColorBar(DistanceMapTFunc)
    # Update scalar bar if already displayed
    self.UpdateScalarBar()

  def setColorMapSequenceRangeSpinBoxes(self, colormapName, colormapType):
    sequencerange = self.commonColorMapInformation[colormapName].sequenceRange[colormapType]
    self.doubleSpinBox_ColorSequenceMin.blockSignals(True)
    self.doubleSpinBox_ColorSequenceMin.setMaximum(99999999999)
    self.doubleSpinBox_ColorSequenceMin.value = sequencerange[0]
    self.doubleSpinBox_ColorSequenceMin.setMaximum(sequencerange[1])
    self.doubleSpinBox_ColorSequenceMin.blockSignals(False)

    self.doubleSpinBox_ColorSequenceMax.blockSignals(True)
    self.doubleSpinBox_ColorSequenceMax.setMinimum(-99999999999)
    self.doubleSpinBox_ColorSequenceMax.value = sequencerange[1]
    self.doubleSpinBox_ColorSequenceMax.setMinimum(sequencerange[0])
    self.doubleSpinBox_ColorSequenceMax.blockSignals(False)

  def setColorMapInitialSequenceRangeSpinBoxes(self, colormapName, colormapType):
    sequencerange = self.commonColorMapInformation[colormapName].initialSequenceRange[colormapType]
    self.lineEdit_ColorMapSequenceMin.setText(sequencerange[0])
    self.lineEdit_ColorMapSequenceMax.setText(sequencerange[1])

  def onResetSequenceRange(self):
    sequencerange = self.commonColorMapInformation[self.comboBox_ColorMapChoice.currentText].initialSequenceRange[self.comboBox_3DColorMapChoice.currentText]
    self.doubleSpinBox_ColorSequenceMin.setMaximum(99999999999)
    self.doubleSpinBox_ColorSequenceMin.value = sequencerange[0]
    self.doubleSpinBox_ColorSequenceMin.setMaximum(sequencerange[1])

    self.doubleSpinBox_ColorSequenceMax.setMinimum(-99999999999)
    self.doubleSpinBox_ColorSequenceMax.value = sequencerange[1]
    self.doubleSpinBox_ColorSequenceMax.setMinimum(sequencerange[0])

  def UpdateSequenceRange(self, colormapName, colormapType):
    # Update SpinBoxes in UI
    sequencerange = []
    sequencerange.append(self.doubleSpinBox_ColorSequenceMin.value)
    sequencerange.append(self.doubleSpinBox_ColorSequenceMax.value)
    self.commonColorMapInformation[colormapName].sequenceRange[colormapType] = sequencerange
    self.doubleSpinBox_ColorSequenceMin.setMaximum(sequencerange[1])
    self.doubleSpinBox_ColorSequenceMax.setMinimum(sequencerange[0])

  ### Color Bar Functions

  def SaveColorBarInformation(self, previousColormapName):
    colormapName = previousColormapName.split("-")[0]
    colormapType = previousColormapName.split("-")[1]
    sequenceRange = self.commonColorMapInformation[colormapName].sequenceRange[colormapType]
    PointIdSpinBox = slicer.util.findChildren(self.ScalarsToColorsWidget, name='PointIdSpinBox')[0]
    ColorPickerButton = slicer.util.findChildren(self.ScalarsToColorsWidget, name='ColorPickerButton')[0]
    XSpinBox = slicer.util.findChildren(self.ScalarsToColorsWidget, name='XSpinBox')[0]
    colorbar = colorBarStruct()
    for index in range(PointIdSpinBox.maximum + 1):
      PointIdSpinBox.value = index
      colorbarpoint = colorBarPointStruct()
      color = ColorPickerButton.color
      colorbarpoint.r = color.red() / float(255)
      colorbarpoint.g = color.green() / float(255)
      colorbarpoint.b = color.blue() / float(255)
      colorbarpoint.pos = (XSpinBox.value  - sequenceRange[0]) / (sequenceRange[1] - sequenceRange[0])
      colorbar.colorPointList.append(colorbarpoint)
      self.commonColorMapInformation[colormapName].colorbars[colormapType] = colorbar

  def UpdateColorBar(self, DistanceMapTFunc):
    self.ScalarsToColorsWidget.delete()
    self.ScalarsToColorsWidget = ctk.ctkVTKScalarsToColorsWidget()
    self.ScalarsToColorsWidget.minimumSize.setHeight(120)
    self.ScalarsToColorsWidget.horizontalSliderVisible = False
    self.ScalarsToColorsWidget.verticalSliderVisible = False
    ExpandButton = slicer.util.findChildren(self.ScalarsToColorsWidget, name='ExpandButton')[0]
    ExpandButton.hide()
    ctkVTKScalarsToColorsView = slicer.util.findChildren(self.ScalarsToColorsWidget, name='View')[0]
    ctkVTKScalarsToColorsView.setMinimumHeight(120)
    ctkVTKScalarsToColorsView.addColorTransferFunction(DistanceMapTFunc)
    ctkVTKScalarsToColorsView.setVisible(True)
    self.ScalarsToColorsWidget.setEnabled(True)
    self.ScalarsToColorsWidget.update()
    self.CollapsibleGroupBox_CustomColorBar.layout().addWidget(self.ScalarsToColorsWidget)

  ### Scalar Bar Functions

  def onDisplayScalarBar(self):

    # Set the Scalar Bar
    colorWidget = slicer.modules.colors.widgetRepresentation()
    ctkScalarBarWidget = slicer.util.findChildren(colorWidget, name='VTKScalarBar')[0]

    if self.checkBox_DisplayScalarBar.checkState():
      activeColorNodeSelector = slicer.util.findChildren(colorWidget, 'ColorTableComboBox')[0]
      colorNode = slicer.mrmlScene.GetNodesByName("BlueWhiteRed").GetItemAsObject(0)
      activeColorNodeSelector.setCurrentNodeID(colorNode.GetID())

      TitleTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='TitleTextPropertyWidget')[0]
      TextLineEdit = slicer.util.findChildren(TitleTextPropertyWidget, name='TextLineEdit')[0]
      TextLineEdit.setText(self.lineEdit_TitleScalarBar.text)
      TitleColorPickerButton = slicer.util.findChildren(TitleTextPropertyWidget, name='ColorPickerButton')[0]
      TitleColorPickerButton.color = self.ColorPickerButton_LabelsColorScalarBar.color
      TitleBoldCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='BoldCheckBox')[0]
      TitleItalicCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='ItalicCheckBox')[0]
      TitleShadowCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='ShadowCheckBox')[0]
      TitleBoldCheckBox.setCheckState(self.checkBox_LabelBoldStyleScalarBar.checkState())
      TitleItalicCheckBox.setCheckState(self.checkBox_LabelItalicStyleScalarBar.checkState())
      TitleShadowCheckBox.setCheckState(self.checkBox_LabelShadowStyleScalarBar.checkState())

      LabelsTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='LabelsTextPropertyWidget')[0]
      LablesColorPickerButton = slicer.util.findChildren(LabelsTextPropertyWidget, name='ColorPickerButton')[0]
      LablesColorPickerButton.color = self.ColorPickerButton_LabelsColorScalarBar.color
      LabelsBoldCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='BoldCheckBox')[0]
      LabelsItalicCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='ItalicCheckBox')[0]
      LabelsShadowCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='ShadowCheckBox')[0]
      LabelsBoldCheckBox.setCheckState(self.checkBox_LabelBoldStyleScalarBar.checkState())
      LabelsItalicCheckBox.setCheckState(self.checkBox_LabelItalicStyleScalarBar.checkState())
      LabelsShadowCheckBox.setCheckState(self.checkBox_LabelShadowStyleScalarBar.checkState())

    # show/hide the scalar bar widget
    ctkScalarBarWidget.setDisplay(self.checkBox_DisplayScalarBar.checkState())

  # Update scalar bar if already displayed
  def UpdateScalarBar(self):
    if self.checkBox_DisplayScalarBar.checkState():
      self.checkBox_DisplayScalarBar.setCheckState(qt.Qt.Unchecked)
      self.checkBox_DisplayScalarBar.setCheckState(qt.Qt.Checked)

  def onUpdateTitleScalarBar(self):
    # Modify the title of the scalar bar widget
    colorWidget = slicer.modules.colors.widgetRepresentation()
    ctkScalarBarWidget = slicer.util.findChildren(colorWidget, name='VTKScalarBar')[0]
    TitleTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='TitleTextPropertyWidget')[0]
    TextLineEdit = slicer.util.findChildren(TitleTextPropertyWidget, name='TextLineEdit')[0]
    TextLineEdit.setText(self.lineEdit_TitleScalarBar.text)

  def onUpdateColorLabelsScalarBar(self):
    # Modify the title color and lable colors of the scalar bar widget
    colorWidget = slicer.modules.colors.widgetRepresentation()
    ctkScalarBarWidget = slicer.util.findChildren(colorWidget, name='VTKScalarBar')[0]

    TitleTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='TitleTextPropertyWidget')[0]
    TitleColorPickerButton = slicer.util.findChildren(TitleTextPropertyWidget, name='ColorPickerButton')[0]
    TitleColorPickerButton.color = self.ColorPickerButton_LabelsColorScalarBar.color

    LabelsTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='LabelsTextPropertyWidget')[0]
    ColorPickerButton = slicer.util.findChildren(LabelsTextPropertyWidget, name='ColorPickerButton')[0]
    ColorPickerButton.color = self.ColorPickerButton_LabelsColorScalarBar.color

  def onUpdateLabelsStyleScalarBar(self):
    colorWidget = slicer.modules.colors.widgetRepresentation()
    ctkScalarBarWidget = slicer.util.findChildren(colorWidget, name='VTKScalarBar')[0]

    TitleTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='TitleTextPropertyWidget')[0]
    TitleBoldCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='BoldCheckBox')[0]
    TitleItalicCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='ItalicCheckBox')[0]
    TitleShadowCheckBox = slicer.util.findChildren(TitleTextPropertyWidget, name='ShadowCheckBox')[0]
    TitleBoldCheckBox.setCheckState(self.checkBox_LabelBoldStyleScalarBar.checkState() )
    TitleItalicCheckBox.setCheckState(self.checkBox_LabelItalicStyleScalarBar.checkState() )
    TitleShadowCheckBox.setCheckState(self.checkBox_LabelShadowStyleScalarBar.checkState() )

    LabelsTextPropertyWidget = slicer.util.findChildren(ctkScalarBarWidget, name='LabelsTextPropertyWidget')[0]
    LabelsBoldCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='BoldCheckBox')[0]
    LabelsItalicCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='ItalicCheckBox')[0]
    LabelsShadowCheckBox = slicer.util.findChildren(LabelsTextPropertyWidget, name='ShadowCheckBox')[0]
    LabelsBoldCheckBox.setCheckState(self.checkBox_LabelBoldStyleScalarBar.checkState())
    LabelsItalicCheckBox.setCheckState(self.checkBox_LabelItalicStyleScalarBar.checkState())
    LabelsShadowCheckBox.setCheckState(self.checkBox_LabelShadowStyleScalarBar.checkState())

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

  def storeColormapInformation(self, colormapName, RegressionModels):
    colorMapInfo = colorMapStruct()

    #     Color Map Name
    colorMapInfo.colormapName = colormapName

    #     Number of components of the color map
    model = RegressionModels[0]
    numberOfComponents = model.GetPolyData().GetPointData().GetScalars(colormapName).GetNumberOfComponents()
    colorMapInfo.numberOfComponents = numberOfComponents

    #     Type of Colors Maps
    colormapTypes = []
    if numberOfComponents == 3:
      colormapTypes = ["Magnitude", "X", "Y", "Z"]
      self.creation3DColorMaps(colormapName, RegressionModels)
    elif numberOfComponents == 1:
      colormapTypes = ["Magnitude"]
    colorMapInfo.colormapTypes = colormapTypes

    for colormapType in colormapTypes:
      #     Computes Sequences Ranges
      if numberOfComponents == 3:
        color3DmapName = colormapType + colormapName
        colorMapInfo.sequenceRange[colormapType] = self.computeSequenceRange(color3DmapName, RegressionModels)
        colorMapInfo.initialSequenceRange[colormapType] = self.computeSequenceRange(color3DmapName, RegressionModels)
      elif numberOfComponents == 1:
        colorMapInfo.sequenceRange[colormapType] = self.computeSequenceRange(colormapName, RegressionModels)
        colorMapInfo.initialSequenceRange[colormapType] = self.computeSequenceRange(colormapName, RegressionModels)

      #     Initialization of colorBars' Point for each color maps
      colorbar = colorBarStruct()
      colorbar.setInitialColorBarPointList()
      colorMapInfo.colorbars[colormapType] = colorbar

    # Store the color map information
    return colorMapInfo

  def findColorMapInCommon(self, RegressionModels):
    # Color Map in common for each models containing in the Sequence
    ColorMapNameInCommon = []
    for number, model in RegressionModels.items():
      numOfArray = model.GetPolyData().GetPointData().GetNumberOfArrays()
      ColorMapNameslist = []
      for i in range(0, numOfArray):
        if number == 0:
          ColorMapNameInCommon.append(model.GetPolyData().GetPointData().GetArray(i).GetName())
        ColorMapNameslist.append(model.GetPolyData().GetPointData().GetArray(i).GetName())
      ColorMapNameInCommon = set(ColorMapNameslist) & set(ColorMapNameInCommon)
    return ColorMapNameInCommon

  def creation3DColorMaps(self, color3DmapName, RegressionModels):
    colormapTypes = ["Magnitude","X","Y","Z"]
    for number, model in RegressionModels.items():
      color3Dmap = model.GetPolyData().GetPointData().GetScalars(color3DmapName)
      numPts = model.GetPolyData().GetPoints().GetNumberOfPoints()

      for colormapType in colormapTypes:
        colormap = vtk.vtkDoubleArray()
        colormapName = colormapType + color3DmapName
        colormap.SetName(colormapName)
        colormap.SetNumberOfComponents(1)
        colormap.SetNumberOfTuples(numPts)
        for i in range(numPts):
          xyz = color3Dmap.GetTuple(i)
          if colormapType == "Magnitude":
            tuple = (vtk.vtkMath.Normalize([xyz[0], xyz[1], xyz[2]]))
          elif colormapType == "X":
            tuple = xyz[0]
          elif colormapType == "Y":
            tuple = xyz[1]
          elif colormapType == "Z":
            tuple = xyz[2]
          colormap.InsertTuple1(i, tuple)
        model.GetPolyData().GetPointData().AddArray(colormap)

  def computeSequenceRange(self, colormapName, RegressionModels):
    sequencerange = [99999999999, -99999999999]
    for number, model in RegressionModels.items():
      modelrange = model.GetPolyData().GetPointData().GetScalars(colormapName).GetRange(-1)
      if modelrange[0] < sequencerange[0]:
        sequencerange[0] = modelrange[0]
      if modelrange[1] > sequencerange[1]:
        sequencerange[1] = modelrange[1]
    return sequencerange

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