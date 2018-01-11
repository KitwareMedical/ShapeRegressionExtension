import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import platform
import csv
import logging
from ShapeRegressionUtilities import *


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
    self.shapeInputDirectory = self.getWidget('DirectoryButton_ShapeInput')
    self.tableWidget_inputShapeParameters = self.getWidget('tableWidget_inputShapeParameters')

    # Times Parameters
    self.CollapsibleButton_TimeParemeters = self.getWidget('CollapsibleButton_TimeParemeters')
    self.t0 = self.getWidget('spinBox_StartingTimePoint')
    self.tn = self.getWidget('spinBox_EndingTimePoint')
    self.T = self.getWidget('spinBox_NumberOfTimepoints')

    # Deformation Parameters
    self.CollapsibleButton_DeformationParameters = self.getWidget('CollapsibleButton_DeformationParameters')
    self.defKernelWidth = self.getWidget('spinBox_DeformationKernelWidh')
    self.kernelType = self.getWidget('ComboBox_KernelType')
    self.regularityWeight = self.getWidget('doubleSpinBox_RegularityWeight')

    # Output Parameters
    self.CollapsibleButton_OutputParameters = self.getWidget('CollapsibleButton_OutputParameters')
    self.outputDirectory = self.getWidget('DirectoryButton_OutputDirectory')
    self.outputPrefix = self.getWidget('lineEdit_OutputRootname')
    self.saveEveryN = self.getWidget('spinBox_SaveEveryNIterations')

    # Optional Parameters
    self.CollapsibleButton_OptionalParameters = self.getWidget('CollapsibleButton_OptionalParameters')
    self.estimateBaseline = self.getWidget('checkBox_EstimateBaselineShape')
    self.optimMethod = self.getWidget('ComboBox_OptimizationMethod')
    self.breakRatio = self.getWidget('doubleSpinBox_BreakRatio')
    self.maxIters = self.getWidget('spinBox_MaxIterations')

    # Run Shape4D
    self.applyButton = self.getWidget('pushButton_RunShape4D')
    self.CLIProgressBar_shape4D = self.getWidget('CLIProgressBar_shape4D')

    # Connect Functions
    self.CollapsibleButton_RegressionComputationInput.connect('clicked()',
                                                        lambda: self.onSelectedCollapsibleButtonOpen(
                                                          self.CollapsibleButton_RegressionComputationInput))
    self.shapeInputDirectory.connect('directoryChanged(const QString &)', self.onInputShapesDirectoryChanged)

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
    #   Input Parameters Table Configuration
    self.tableWidget_inputShapeParameters.setColumnCount(5)
    self.tableWidget_inputShapeParameters.setHorizontalHeaderLabels([' Input Shapes ', ' Time Point ', ' Sigma W ', ' Tris ', ' Weight '])
    self.tableWidget_inputShapeParameters.setColumnWidth(0, 400)
    horizontalHeader = self.tableWidget_inputShapeParameters.horizontalHeader()
    horizontalHeader.setStretchLastSection(False)
    horizontalHeader.setResizeMode(0, qt.QHeaderView.Stretch)
    horizontalHeader.setResizeMode(1, qt.QHeaderView.ResizeToContents)
    horizontalHeader.setResizeMode(2, qt.QHeaderView.ResizeToContents)
    horizontalHeader.setResizeMode(3, qt.QHeaderView.ResizeToContents)
    horizontalHeader.setResizeMode(4, qt.QHeaderView.ResizeToContents)

    #   Shape4D CLI Progress Bar Configuration
    self.CLIProgressBar_shape4D.hide()

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

  def onInputShapesDirectoryChanged(self):
    inputShapesDirectory = self.shapeInputDirectory.directory.encode('utf-8')
    row = 0
    for file in os.listdir(inputShapesDirectory):
        if file.endswith(".vtk"):
          self.tableWidget_inputShapeParameters.setRowCount(row + 1)

          # Column 0:
          rootname = os.path.basename(file).split(".")[0]
          labelVTKFile = qt.QLabel(rootname)
          labelVTKFile.setAlignment(0x84)
          self.tableWidget_inputShapeParameters.setCellWidget(row, 0, labelVTKFile)

          # Column 1-2-3-4:
          for i in range(1,5):
            widget = qt.QWidget()
            layout = qt.QHBoxLayout(widget)
            spinBox = qt.QSpinBox()
            spinBox.setMinimum(0)
            layout.addWidget(spinBox)
            layout.setAlignment(0x84)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.tableWidget_inputShapeParameters.setCellWidget(row, i, widget)

          row = row + 1

  def onApplyButton(self):
    if self.applyButton.text == "Run Shape4D":
      logging.info('Widget: Running Shape4D')
      self.CLIProgressBar_shape4D.show()
      self.CLIProgressBar_shape4D.setCommandLineModuleNode(self.Logic.shape4D_cli_node)
      self.applyButton.setText("Cancel")
      self.Logic.runShape4D()
    else:
      logging.info('Cancel Shape4D')
      self.applyButton.setText("Run Shape4D")
      self.Logic.shape4D_cli_node.SetStatus(self.Logic.shape4D_cli_node.Cancelling)

#
# RegressionComputationLogic
#
class RegressionComputationLogic(ScriptedLoadableModuleLogic, VTKObservationMixin):
  """
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, interface):
    VTKObservationMixin.__init__(self)

    self.interface = interface
    self.StatusModifiedEvent = slicer.vtkMRMLCommandLineModuleNode().StatusModifiedEvent
    self.shape4D_module = slicer.modules.shape4d
    self.shape4D_cli_node = slicer.cli.createNode(self.shape4D_module)
    shape4D_cli_node_name = "Shape4D"
    self.shape4D_cli_node.SetName(shape4D_cli_node_name)

  def runShape4D(self):
    print "Run Shape4D"

    # Write XML driver file input
    XMLdriverfilepath = self.writeXMLdriverFile()

    # Call Shape4D
    parameters = {}
    print XMLdriverfilepath
    parameters["inputXML"] = XMLdriverfilepath
    self.addObserver(self.shape4D_cli_node, self.StatusModifiedEvent, self.onCLIModuleModified)
    slicer.cli.run(self.shape4D_module, self.shape4D_cli_node, parameters, wait_for_completion=False)

  def writeXMLdriverFile(self):
    print "Write XML driver file"

    useFista = False
    if (self.interface.optimMethod.currentText == "FISTA"):
      useFista = True

    # Write CSV file containing the parameters for each shapes
    self.pathToCSV = self.writeCSVInputshapesparameters()

    # Read CSV file containing the parameters for each shapes
    self.readCSVFile(self.pathToCSV)

    if sys.platform == 'win32':
      experimentName = "/ShapeRegression"
      outputDir = self.interface.outputDirectory.directory.encode('utf-8')
      prefix = "/" + self.interface.outputPrefix.text
    else:
      experimentName = "ShapeRegression/"
      outputDir = self.interface.outputDirectory.directory.encode('utf-8') + "/"
      prefix = self.interface.outputPrefix.text

    # Write XML file
    fileContents = ""

    fileContents += "<?xml version=\"1.0\">\n"
    fileContents += "<experiment name=\"" + experimentName + "\">\n"

    fileContents += "  <algorithm name=\"RegressionVelocity\">\n"
    fileContents += "    <source>\n"
    fileContents += "      <input>\n"
    fileContents += "        <shape> " + self.shapePaths[0] + " </shape>\n"
    fileContents += "      </input>\n"
    fileContents += "      <sigmaV> " + str(self.interface.defKernelWidth.value) + " </sigmaV>\n"
    fileContents += "      <gammaR> " + str(self.interface.regularityWeight.value) + " </gammaR>\n"
    fileContents += "      <t0> " + str(self.interface.t0.value) + " </t0>\n"
    fileContents += "      <tn> " + str(self.interface.tn.value) + " </tn>\n"
    fileContents += "      <T> " + str(self.interface.T.value) + " </T>\n"
    fileContents += "      <kernelType> " + self.interface.kernelType.currentText + " </kernelType>\n"
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
    fileContents += "      <sigmaV> " + str(self.interface.defKernelWidth.value) + " </sigmaV>\n"
    fileContents += "      <gammaR> " + str(self.interface.regularityWeight.value) + " </gammaR>\n"
    fileContents += "      <t0> " + str(self.interface.t0.value) + " </t0>\n"
    fileContents += "      <tn> " + str(self.interface.tn.value) + " </tn>\n"
    fileContents += "      <T> " + str(self.interface.T.value) + " </T>\n"
    fileContents += "      <kernelType> " + self.interface.kernelType.currentText + " </kernelType>\n"
    fileContents += "      <useInitV0> 1 </useInitV0>\n"
    fileContents += "      <v0weight> 1 </v0weight>\n"
    fileContents += "      <estimateBaseline> " + str(int(self.interface.estimateBaseline.checkState())) + " </estimateBaseline>\n"
    fileContents += "      <useFista> " + str(int(useFista)) + " </useFista>\n"
    fileContents += "      <maxIters> " + str(self.interface.maxIters.value) + " </maxIters>\n"
    fileContents += "      <breakRatio> " + str(self.interface.breakRatio.value) + " </breakRatio>\n"
    fileContents += "      <output>\n"
    fileContents += "        <saveProgress> " + str(self.interface.saveEveryN.value) + " </saveProgress>\n"
    fileContents += "        <dir> " + outputDir + " </dir>\n"
    fileContents += "        <prefix> " + prefix + " </prefix>\n"
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

    XMLdriverfilepath = os.path.join(self.interface.outputDirectory.directory.encode('utf-8'), "driver.xml")
    f = open(XMLdriverfilepath, 'w')
    f.write(fileContents)
    f.close()
    return XMLdriverfilepath

  def writeCSVInputshapesparameters(self):
    inputShapesDirectory = self.interface.shapeInputDirectory.directory.encode('utf-8')
    outputDirectory = self.interface.outputDirectory.directory.encode('utf-8')

    CSVInputshapesparametersfilepath = os.path.join(outputDirectory, "CVSInputshapesparameters.csv")
    print CSVInputshapesparametersfilepath
    print outputDirectory
    file = open(CSVInputshapesparametersfilepath, 'w')
    cw = csv.writer(file, delimiter=',')
    table = self.interface.tableWidget_inputShapeParameters
    for row in range(0, table.rowCount):
      listcsv = []
      inputshaperootname = table.cellWidget(row, 0)
      inputshapefilepath = inputShapesDirectory + "/" + inputshaperootname.text + ".vtk"
      listcsv.append(inputshapefilepath)
      for column in range(1, 5):
        widget = table.cellWidget(row, column)
        tuple = widget.children()
        spinbox = tuple[1]
        listcsv.append(spinbox.value)
      cw.writerow(listcsv)
    file.close()

    return CSVInputshapesparametersfilepath

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

  def onCLIModuleModified(self, cli_node, event):
    statusForNode = None
    if not cli_node.IsBusy():
      if platform.system() != 'Windows':
        self.removeObserver(cli_node, self.StatusModifiedEvent, self.onCLIModuleModified)
        statusForNode = None

      if cli_node.GetStatusString() == 'Completed':
        statusForNode = cli_node.GetStatusString()

      elif cli_node.GetStatusString() == 'Cancelled':
        self.ErrorMessage = "Shape4D cancelled"
        statusForNode = cli_node.GetStatusString()

      else:
        # Create Error Message
        if cli_node.GetStatusString() == 'Completed with errors':
          self.ErrorMessage = "Shape4D completed with errors"
          statusForNode = cli_node.GetStatusString()

      # Create Error Message
      if statusForNode == 'Completed with errors' or statusForNode == 'Cancelled':
        logging.error(self.ErrorMessage)
        qt.QMessageBox.critical(slicer.util.mainWindow(),
                                'RegressionComputation',
                                self.ErrorMessage)

      self.interface.applyButton.text = 'Run Shape4D'


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