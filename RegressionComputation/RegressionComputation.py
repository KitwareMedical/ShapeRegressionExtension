import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import csv

#
# RegressionComputation
#

class RegressionComputation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "RegressionComputation"
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
# RegressionComputationWidget
#

class RegressionComputationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    #   Global variables
    #
    self.Logic = RegressionComputationLogic(self)

    #
    #  Interface
    #
    loader = qt.QUiLoader()
    self.moduleName = 'RegressionComputation'
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
    # Input Shapes
    self.CollapsibleButton_RegressionComputationInput = self.getWidget('CollapsibleButton_RegressionComputationInput')
    self.PathLineEdit_RegressionComputationInput = self.getWidget('PathLineEdit_RegressionComputationInput')

    # Times Parameters
    self.CollapsibleButton_TimeParemeters = self.getWidget('CollapsibleButton_TimeParemeters')
    self.t0Input = self.getWidget('spinBox_StartingTimePoint')
    self.tnInput = self.getWidget('spinBox_EndingTimePoint')
    self.TInput = self.getWidget('spinBox_NumberOfTimepoints')

    # Deformation Parameters
    self.CollapsibleButton_DeformationParameters = self.getWidget('CollapsibleButton_DeformationParameters')
    self.deformationKernelInput = self.getWidget('spinBox_DeformationKernelWidh')
    self.kernelTypeInput = self.getWidget('ComboBox_KernelType')
    self.regularityInput = self.getWidget('doubleSpinBox_RegularityWeight')

    # Output Parameters
    self.CollapsibleButton_OutputParameters = self.getWidget('CollapsibleButton_OutputParameters')
    self.outputDirectory = self.getWidget('DirectoryButton_OutputDirectory')
    self.outputRootnameInput = self.getWidget('lineEdit_OutputRootname')
    self.saveTempInput = self.getWidget('spinBox_SaveEveryNIterations')

    # Optional Parameters
    self.CollapsibleButton_OptionalParameters = self.getWidget('CollapsibleButton_OptionalParameters')
    self.estimateBaselineCheckBox = self.getWidget('checkBox_EstimateBaselineShape')
    self.optimizationMethodInput = self.getWidget('ComboBox_OptimizationMethod')
    self.breakRatioInput = self.getWidget('doubleSpinBox_BreakRatio')
    self.maxItersInput = self.getWidget('spinBox_MaxIterations')

    # Run Shape4D
    self.applyButton = self.getWidget('pushButton_RunShape4D')

    # Connect Functions
    self.CollapsibleButton_RegressionComputationInput.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_RegressionComputationInput))
    self.CollapsibleButton_TimeParemeters.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_TimeParemeters))
    self.CollapsibleButton_DeformationParameters.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_DeformationParameters))
    self.CollapsibleButton_OutputParameters.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_OutputParameters))
    self.CollapsibleButton_OptionalParameters.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_OptionalParameters))
    self.applyButton.connect('clicked(bool)', self.onApplyButton)



    slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    # Widget Configuration
    # TODO


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
      collapsibleButtonList = [self.CollapsibleButton_RegressionComputationInput,
                               self.CollapsibleButton_TimeParemeters,
                               self.CollapsibleButton_DeformationParameters,
                               self.CollapsibleButton_OutputParameters,
                               self.CollapsibleButton_OptionalParameters]
      for collapsibleButton in collapsibleButtonList:
        collapsibleButton.setChecked(False)
      selectedCollapsibleButton.setChecked(True)

  def warningMessage(self, text, informativeText):
      messageBox = ctk.ctkMessageBox()
      messageBox.setWindowTitle(' /!\ WARNING /!\ ')
      messageBox.setIcon(messageBox.Warning)
      messageBox.setText(text)
      if not informativeText == None:
        messageBox.setInformativeText(informativeText)
      messageBox.setStandardButtons(messageBox.Ok)
      messageBox.exec_()

  def onApplyButton(self):
    self.Logic.parameters.updateShape4DParameters()
    self.Logic.runShape4D()


#
# RegressionComputationLogic
#
class RegressionComputationLogic(ScriptedLoadableModuleLogic):
  """
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, interface):
    self.interface = interface
    self.parameters = RegressionComputationParameters(interface)

  def runShape4D(self):
    print "Run Shape4D"

    # Write XML driver file input
    XMLdriverfilepath = self.writeXMLdriverFile()

    # Call Shape4D
    parameters = {}
    print XMLdriverfilepath
    parameters["inputXML"] = XMLdriverfilepath
    shape4D = slicer.modules.shape4d
    slicer.cli.run(shape4D, None, parameters, wait_for_completion=True)

    return True

  def writeXMLdriverFile(self):
    print "Write XML driver file"

    useFista = False
    if (self.parameters.optimMethod == "FISTA"):
      useFista = True

    # Read CSV file containing the parameters for each shapes
    self.readCSVFile(self.parameters.pathToCSV)

    # Write XML file
    fileContents = ""

    fileContents += "<?xml version=\"1.0\">\n"
    fileContents += "<experiment name=\"ShapeRegression\">\n"

    fileContents += "  <algorithm name=\"RegressionVelocity\">\n"
    fileContents += "    <source>\n"
    fileContents += "      <input>\n"
    fileContents += "        <shape> " + self.shapePaths[0] + " </shape>\n"
    fileContents += "      </input>\n"
    fileContents += "      <sigmaV> " + str(self.parameters.defKernelWidth) + " </sigmaV>\n"
    fileContents += "      <gammaR> " + str(self.parameters.regularityWeight) + " </gammaR>\n"
    fileContents += "      <t0> " + str(self.parameters.t0) + " </t0>\n"
    fileContents += "      <tn> " + str(self.parameters.tn) + " </tn>\n"
    fileContents += "      <T> " + str(self.parameters.T) + " </T>\n"
    fileContents += "      <kernelType> " + self.parameters.kernelType + " </kernelType>\n"
    fileContents += "      <estimateBaseline> 0 </estimateBaseline>\n"
    fileContents += "      <useFista> 0 </useFista>\n"
    fileContents += "      <maxIters> 250 </maxIters>\n"
    fileContents += "      <breakRatio> 1e-6 </breakRatio>\n"
    fileContents += "    </source>\n"
    fileContents += "    <targets>\n"
    fileContents += "      <target>\n"
    fileContents += "        <shape> " + self.shapePaths[len(self.shapePaths)-1] + " </shape>\n"
    fileContents += "        <type> SURFACE </type>\n"
    fileContents += "        <tris> 0 </tris>\n"
    fileContents += "        <sigmaW> " + self.sigmaWs[len(self.sigmaWs)-1] + " </sigmaW>\n"
    fileContents += "        <timept> " + self.timepts[len(self.timepts)-1] + " </timept>\n"
    fileContents += "        <weight> 1.0 </weight>\n"
    fileContents += "      </target>\n"
    fileContents += "    </targets>\n"
    fileContents += "  </algorithm>\n"

    fileContents += "  <algorithm name=\"RegressionAccel\">\n"
    fileContents += "    <source>\n"
    fileContents += "      <input>\n"
    fileContents += "        <shape> " + self.shapePaths[0] + " </shape>\n"
    fileContents += "      </input>\n"
    fileContents += "      <sigmaV> " + str(self.parameters.defKernelWidth) + " </sigmaV>\n"
    fileContents += "      <gammaR> " + str(self.parameters.regularityWeight) + " </gammaR>\n"
    fileContents += "      <t0> " + str(self.parameters.t0) + " </t0>\n"
    fileContents += "      <tn> " + str(self.parameters.tn) + " </tn>\n"
    fileContents += "      <T> " + str(self.parameters.T) + " </T>\n"
    fileContents += "      <kernelType> " + self.parameters.kernelType + " </kernelType>\n"
    fileContents += "      <useInitV0> 1 </useInitV0>\n"
    fileContents += "      <v0weight> 1 </v0weight>\n"
    fileContents += "      <estimateBaseline> " + str(int(self.parameters.estimateBaseline)) + " </estimateBaseline>\n"
    fileContents += "      <useFista> " + str(int(useFista)) + " </useFista>\n"
    fileContents += "      <maxIters> " + str(self.parameters.maxIters) + " </maxIters>\n"
    fileContents += "      <breakRatio> " + str(self.parameters.breakRatio) + " </breakRatio>\n"
    fileContents += "      <output>\n"
    fileContents += "        <saveProgress> " + str(self.parameters.saveEveryN) + " </saveProgress>\n"
    fileContents += "        <dir> " + self.parameters.outputDir + "/ </dir>\n"
    fileContents += "        <prefix> " + self.parameters.outputPrefix + " </prefix>\n"
    fileContents += "      </output>\n"
    fileContents += "    </source>\n"
    fileContents += "    <targets>\n"

    for i in range(0, len(self.shapePaths)):

      fileContents += "      <target>\n"
      fileContents += "        <shape> " + self.shapePaths[i] + " </shape>\n"
      fileContents += "        <type> SURFACE </type>\n"
      fileContents += "        <tris> " + self.shapeIndices[i] + " </tris>\n"
      fileContents += "        <sigmaW> " + self.sigmaWs[i] + " </sigmaW>\n"
      fileContents += "        <timept> " + self.timepts[i] + " </timept>\n"
      fileContents += "        <weight> " + self.weights[i] + " </weight>\n"
      fileContents += "      </target>\n"

    fileContents += "    </targets>\n"
    fileContents += "  </algorithm>\n"
    fileContents += "</experiment>\n"

    XMLdriverfilepath = os.path.join(self.parameters.outputDir, "driver.xml")
    f = open(XMLdriverfilepath, 'w')
    f.write(fileContents)
    f.close()
    return XMLdriverfilepath

  def readCSVFile(self, pathToCSV):

    self.shapePaths = []
    self.timepts = []
    self.sigmaWs = []
    self.shapeIndices = []
    self.weights = []

    with open(pathToCSV) as csvfile:
      allRows = csv.reader(csvfile, delimiter=',', quotechar='|')
      for row in allRows:
        self.shapePaths.append(row[0].strip())
        self.timepts.append(row[1].strip())
        self.sigmaWs.append(row[2].strip())
        self.shapeIndices.append(row[3].strip())
        self.weights.append(row[4].strip())

    # print self.shapePaths
    # print self.timepts
    # print self.sigmaWs
    # print self.shapeIndices
    # print self.weights

#
# RegressionComputationParameters
#
class RegressionComputationParameters(object):
  def __init__(self, interface):
    self.interface = interface

    # Parameters by default

    self.pathToCSV = " "

    self.t0 = 0
    self.tn = 0
    self.T = 0

    self.defKernelWidth = 0
    self.kernelType = "exact"
    self.regularityWeight = 0

    self.outputDir = " "
    self.outputPrefix = " "
    self.saveEveryN = 0

    self.estimateBaseline = False
    self.optimMethod = "FISTA"
    self.breakRatio = 0
    self.maxIters = 0

  def updateShape4DParameters(self):
    self.pathToCSV = self.interface.PathLineEdit_RegressionComputationInput.currentPath

    self.t0 = self.interface.t0Input.value
    self.tn = self.interface.tnInput.value
    self.T = self.interface.TInput.value

    self.defKernelWidth = self.interface.deformationKernelInput.value
    self.kernelType = self.interface.kernelTypeInput.currentText
    self.regularityWeight = self.interface.regularityInput.value

    self.outputDir = self.interface.outputDirectory.directory.encode('utf-8')
    self.outputPrefix = self.interface.outputRootnameInput.text
    self.saveEveryN = self.interface.saveTempInput.value

    self.estimateBaseline = self.interface.estimateBaselineCheckBox.isChecked()
    self.optimMethod = self.interface.optimizationMethodInput.currentText
    self.breakRatio = self.interface.breakRatioInput.value
    self.maxIters = self.interface.maxItersInput.value


#
# RegressionComputationTest
#
class RegressionComputationTest(ScriptedLoadableModuleTest):
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
    self.test_RegressionComputation()

  def test_RegressionComputation(self):
    pass