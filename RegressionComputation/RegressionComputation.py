import os, sys
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import platform
import csv
import logging
import urllib
import re
from packaging import version

def _setSectionResizeMode(header, *args, **kwargs):
  """ To be compatible with Qt4 and Qt5 """
  if version.parse(qt.Qt.qVersion()) < version.parse("5.0.0"):
    header.setResizeMode(*args, **kwargs)
  else:
    header.setSectionResizeMode(*args, **kwargs)

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
    self.parent.contributors = ["Laura Pascal (Kitware Inc.), James Fishbaugh (NYU Tandon School of Engineering), Pablo Hernandez (Kitware Inc.), Beatriz Paniagua (Kitware Inc.)"]
    self.parent.helpText = """
    Computation of time-regressed shapes in a collection of 3D shape inputs associated to a linear variable.
    This module uses shape4D CLI: https://github.com/laurapascal/shape4D.
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
    self.tabWidget_InputShapes = self.getWidget('tabWidget_InputShapes')
    self.shapeInputDirectory = self.getWidget('DirectoryButton_ShapeInput')
    self.tableWidget_inputShapeParameters = self.getWidget('tableWidget_inputShapeParameters')
    self.PathLineEdit_ShapeInputsCSV = self.getWidget('PathLineEdit_ShapeInputsCSV')

    # Times Parameters
    self.CollapsibleButton_TimeParemeters = self.getWidget('CollapsibleButton_TimeParemeters')
    self.t0 = self.getWidget('spinBox_StartingTimePoint')
    self.tn = self.getWidget('spinBox_EndingTimePoint')
    self.T = self.getWidget('spinBox_NumberOfTimepoints')
    self.t0.enabled = True
    self.tn.enabled = True
    self.defaultTimePointRange = self.getWidget('checkBox_defaultTimePointRange')
    self.defaultTimePointRange.visible = False

    self.T.setMinimum(10)
    self.T.setMaximum(9999999)

    # Deformation Parameters
    self.CollapsibleButton_DeformationParameters = self.getWidget('CollapsibleButton_DeformationParameters')
    self.defKernelWidth = self.getWidget('spinBox_DeformationKernelWidh')
    self.kernelType = self.getWidget('ComboBox_KernelType')
    self.regularityWeight = self.getWidget('doubleSpinBox_RegularityWeight')

    self.defKernelWidth.setMinimum(0)
    self.defKernelWidth.setMaximum(9999999)
    self.regularityWeight.value = 0.01

    # Output Parameters
    self.CollapsibleButton_OutputParameters = self.getWidget('CollapsibleButton_OutputParameters')
    self.outputDirectory = self.getWidget('DirectoryButton_OutputDirectory')
    self.outputPrefix = self.getWidget('lineEdit_OutputRootname')
    self.saveEveryN = self.getWidget('spinBox_SaveEveryNIterations')

    self.outputPrefix.text = 'Regression_output_'
    self.saveEveryN.value = 50

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

    #self.t0.connect('valueChanged(int)', self.onSetMaximumStartingTimePoint)
    #self.tn.connect('valueChanged(int)', self.onSetMinimumEndingTimePoint)
    #self.defaultTimePointRange.connect('clicked(bool)', self.onEnableTimePointRange)


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
    self.tableWidget_inputShapeParameters.setHorizontalHeaderLabels([' Input Shapes ', ' Time Point ', ' Kernel Width ', ' Shape Index ', ' Weight '])
    self.tableWidget_inputShapeParameters.setColumnWidth(0, 400)
    horizontalHeader = self.tableWidget_inputShapeParameters.horizontalHeader()
    horizontalHeader.setStretchLastSection(False)

    _setSectionResizeMode(horizontalHeader, 0, qt.QHeaderView.Stretch)
    _setSectionResizeMode(horizontalHeader, 1, qt.QHeaderView.ResizeToContents)
    _setSectionResizeMode(horizontalHeader, 2, qt.QHeaderView.ResizeToContents)
    _setSectionResizeMode(horizontalHeader, 3, qt.QHeaderView.ResizeToContents)
    _setSectionResizeMode(horizontalHeader, 4, qt.QHeaderView.ResizeToContents)

    #   Shape4D CLI Progress Bar Configuration
    self.CLIProgressBar_shape4D.hide()

  def enter(self):
    pass

  def onCloseScene(self, obj, event):
    # Reset Input shape parameters
    self.tabWidget_InputShapes.currentIndex = 0
    #self.shapeInputDirectory.directory
    self.PathLineEdit_ShapeInputsCSV.setCurrentPath(" ")

    # Reset the Input Parameters Table
    self.tableWidget_inputShapeParameters.clearContents()
    self.tableWidget_inputShapeParameters.setRowCount(0)

    # Reset Time Point Parameters
    #self.defaultTimePointRange.setChecked(True)
    self.t0.blockSignals(True)
    self.tn.blockSignals(True)
    self.tn.setMinimum(0)
    self.tn.value = 0
    self.t0.setMinimum(-999999)
    self.t0.setMaximum(9999999)
    self.t0.value = 0
    self.t0.blockSignals(False)
    self.tn.blockSignals(False)
    self.T.value = 20
    self.t0.enabled = True
    self.tn.enabled = True
    self.defaultTimePointRange.visible = False

    # Reset deformation parameters
    self.defKernelWidth.value = 0
    self.kernelType.setCurrentIndex(0)
    self.regularityWeight.value = 0

    # Reset Output Parameters
    self.outputPrefix.clear()
    self.saveEveryN.value = 5

    # Reset Optional Parameters
    self.estimateBaseline.setChecked(False)
    self.optimMethod.setCurrentIndex(0)
    self.breakRatio.value = 0.000001
    self.maxIters.value = 250

    # Reset push button
    self.applyButton.setText("Run Shape4D")

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

    inputShapesDirectory = self.shapeInputDirectory.directory
    # Set this directory as the default output directory as well
    self.outputDirectory.directory = str(inputShapesDirectory)

    row = 0

    allShapeSigmaWs = []

    for curFile in sorted(os.listdir(inputShapesDirectory)):

        if not (curFile.endswith(".vtk")):
          continue

        self.tableWidget_inputShapeParameters.setRowCount(row + 1)

        # Read the vtk file to set a default kernel width
        shapeFile = '%s/%s' %(inputShapesDirectory, curFile)
        polyReader = vtk.vtkPolyDataReader()
        polyReader.SetFileName(shapeFile)
        polyReader.Update()
        shape = polyReader.GetOutput()
        shapeBounds = shape.GetBounds()
        xRange = shapeBounds[1] - shapeBounds[0]
        yRange = shapeBounds[3] - shapeBounds[2]
        zRange = shapeBounds[5] - shapeBounds[4]
        smallestRange = min(xRange, yRange, zRange)
        initSigmaW = int(smallestRange*0.50)
        allShapeSigmaWs.append(initSigmaW)

        # Try to extract the time point as a suffix
        curTimePoint = 0.0
        numsInFilename = re.findall(r'[-+]?\d*\.\d+|\d+', curFile)
        if (len(numsInFilename) > 0):
          curTimePoint = numsInFilename[-1]   # We assume the final number in the filename is the time point

        # Column 0:
        #rootname = os.path.basename(curFile).split(".")[0]
        rootname = os.path.splitext(os.path.basename(curFile))[0]
        labelVTKFile = qt.QLabel(rootname)
        labelVTKFile.setAlignment(0x84)
        self.tableWidget_inputShapeParameters.setCellWidget(row, 0, labelVTKFile)

        # Column 1-2-3-4: (Time Point, Sigma W, Tris, Weight)
        # We might want to consider using different UI elements for Time Point and Kernel Width that do not have explicit ranges
        for column in range(1,5):
          widget = qt.QWidget()
          layout = qt.QHBoxLayout(widget)

          # If this is the 'Shape Index' column we limit this to an integer
          if (column == 3):
            spinBox = qt.QSpinBox()
            spinBox.setRange(0,1000)
            spinBox.value = 0
          # The rest of the columns are doubles
          else:
            spinBox = qt.QDoubleSpinBox()

            if column == 1: # Time Point
              spinBox.value = float(curTimePoint)
              spinBox.connect('valueChanged(double)', self.onSetTimePointRange)
              spinBox.setRange(-1e10, 1e10)
            if column == 2: # Kernel Width
              spinBox.setRange(0.001, 1e10)
              spinBox.value = initSigmaW
            if column == 4: # Weight
              spinBox.value = 1
              spinBox.setRange(0,1e10)
              spinBox.setSingleStep(0.1);

          layout.addWidget(spinBox)
          layout.setAlignment(0x84)
          layout.setContentsMargins(0, 0, 0, 0)
          widget.setLayout(layout)
          self.tableWidget_inputShapeParameters.setCellWidget(row, column, widget)

        row = row + 1

    # We can set a default for deformation kernel width as smallest shape kernel
    self.defKernelWidth.value = min(allShapeSigmaWs)

    # Update the time range (if time point suffixes provided initialization)
    self.onSetTimePointRange()

  # I don't see a reason for requiring a user to uncheck a box to set t0 and tn (James)

  #def onEnableTimePointRange(self):
  #  # Enable/Disable the time point range spinboxes
  #  self.t0.enabled = not self.defaultTimePointRange.checkState()
  #  self.tn.enabled = not self.defaultTimePointRange.checkState()

  #  # Enable/Disable the auto set of the time point range
  #  table = self.tableWidget_inputShapeParameters
  #  for row in range(table.rowCount):
  #    widget = table.cellWidget(row, 1)
  #    tuple = widget.children()
  #    spinbox = tuple[1]
  #    spinbox.blockSignals(not self.defaultTimePointRange.checkState())

  #  # If the default value of the time point range is checked, set them
  #  #if self.defaultTimePointRange.checkState():
  #  #  self.onDefaultTimePointRange()


  def onSetTimePointRange(self):
    self.Logic.sortInputCasesAges()
    self.t0.value = self.Logic.age_list[0]
    self.tn.value = self.Logic.age_list[-1]

  #def onSetMaximumStartingTimePoint(self):
  #  self.t0.setMaximum(self.tn.value)

  #def onSetMinimumEndingTimePoint(self):
  #  self.tn.setMinimum(self.t0.value)

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
    logging.debug("Run Shape4D")

    # Write XML driver file input
    XMLdriverfilepath = self.writeXMLdriverFile()

    # Call Shape4D
    if XMLdriverfilepath:
      parameters = {}
      logging.debug(XMLdriverfilepath)
      parameters["inputXML"] = XMLdriverfilepath
      self.addObserver(self.shape4D_cli_node, self.StatusModifiedEvent, self.onCLIModuleModified)
      slicer.cli.run(self.shape4D_module, self.shape4D_cli_node, parameters, wait_for_completion=False)
    else:
      self.interface.applyButton.setText("Run Shape4D")

  def writeXMLdriverFile(self):
    logging.debug("Write XML driver file")

    useFista = False
    if (self.interface.optimMethod.currentText == "FISTA"):
      useFista = True

    if self.interface.tabWidget_InputShapes.currentIndex == 0:
      # Write CSV file containing the parameters for each shapes
      self.pathToCSV = self.writeCSVInputshapesparameters()
    else:
      self.pathToCSV = self.interface.PathLineEdit_ShapeInputsCSV.currentPath
      if not os.path.exists(self.pathToCSV):
        self.interface.warningMessage('The CSV filepath is not existing.', None)
        return
    # Read CSV file containing the parameters for each shapes
    findInputShape = self.readCSVFile(self.pathToCSV)
    if not findInputShape:
      return False

    if sys.platform == 'win32':
      experimentName = "/ShapeRegression"
      outputDir = self.interface.outputDirectory.directory
      prefix = "/" + self.interface.outputPrefix.text
    else:
      experimentName = "ShapeRegression/"
      outputDir = self.interface.outputDirectory.directory + "/"
      prefix = self.interface.outputPrefix.text

    # Write XML file
    fileContents = ""

    fileContents += "<?xml version=\"1.0\">\n"
    fileContents += "<experiment name=\"" + experimentName + "\">\n"

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
    fileContents += "      <useInitV0> 0 </useInitV0>\n"
    fileContents += "      <v0weight> 0.0 </v0weight>\n"
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

    XMLdriverfilepath = os.path.join(self.interface.outputDirectory.directory, "driver.xml")
    f = open(XMLdriverfilepath, 'w')
    f.write(fileContents)
    f.close()
    return XMLdriverfilepath

  def sortInputCasesAges(self):
    table = self.interface.tableWidget_inputShapeParameters
    # Sort the shape input data according to their age
    age_list = list()
    for row in range(table.rowCount):
      widget = table.cellWidget(row, 1)
      tuple = widget.children()
      spinbox = tuple[1]
      age_list.append(spinbox.value)

    self.age_list = sorted(age_list)

  def writeCSVInputshapesparameters(self):
    inputShapesDirectory = self.interface.shapeInputDirectory.directory
    outputDirectory = self.interface.outputDirectory.directory
    table = self.interface.tableWidget_inputShapeParameters

    # Sort the shape input data according to their age
    self.sortInputCasesAges()

    parameters_list = list()
    for row in range(table.rowCount):
      temp_parameters = list()
      inputshaperootname = table.cellWidget(row, 0).text
      inputshapefilepath = inputShapesDirectory + "/" + inputshaperootname + ".vtk"
      temp_parameters.append(inputshapefilepath)
      for column in range(1, table.columnCount):
        widget = table.cellWidget(row, column)
        tuple = widget.children()
        spinbox = tuple[1]
        temp_parameters.append(spinbox.value)
      parameters_list.append(temp_parameters)

    parameters_sorted = sorted(parameters_list, key=lambda x: x[1])
    # Write the parameters needed in a CSV file
    CSVInputshapesparametersfilepath = os.path.join(outputDirectory, "CSVInputshapesparameters.csv")
    file = open(CSVInputshapesparametersfilepath, 'w')
    cw = csv.writer(file, delimiter=',', lineterminator='\n')
    for index in range(len(parameters_sorted)):
      parameters = parameters_sorted[index]
      cw.writerow(parameters)
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

    if len(self.shapePaths) == 0:
      self.interface.warningMessage('No shape input found', None)
      return False
    if len(self.shapePaths) == 1:
      self.interface.warningMessage('Only one shape input found. The module need at least 2 shape inputs.', None)
      return False

    return True

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
class RegressionComputationTest(ScriptedLoadableModuleTest, VTKObservationMixin):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self):
    VTKObservationMixin.__init__(self)

  def setUp(self):
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    self.setUp()
    self.delayDisplay('Starting the tests')
    self.test_RegressionComputation()

  def test_RegressionComputation(self):
    self.delayDisplay('Test : Regression Computation')

    #   Creation of input folder
    inputDirectoryPath = slicer.app.temporaryPath + '/RegressionComputationInputData'
    if not os.path.exists(inputDirectoryPath):
      os.makedirs(inputDirectoryPath)

    #   Download the shape input data
    input_downloads = (
      ('https://data.kitware.com/api/v1/file/5977a6558d777f16d01e9dd3/download', 'SphereToEllipsoid_00.vtk'),
      ('https://data.kitware.com/api/v1/file/5977a6558d777f16d01e9dd6/download', 'SphereToEllipsoid_01.vtk'),
      ('https://data.kitware.com/api/v1/file/5977a6568d777f16d01e9dd9/download', 'SphereToEllipsoid_02.vtk'),
      ('https://data.kitware.com/api/v1/file/5977a6568d777f16d01e9ddc/download', 'SphereToEllipsoid_03.vtk'),
      ('https://data.kitware.com/api/v1/file/5977a6568d777f16d01e9ddf/download', 'SphereToEllipsoid_04.vtk'),
    )
    inputRootnames = list()
    for i in range(len(input_downloads)):
      inputRootnames.append(input_downloads[i][1].split(".")[0])
    self.download_files(inputDirectoryPath, input_downloads)

    #   Creation of output folder
    outputDirectoryPath =  slicer.app.temporaryPath + '/RegressionComputationOutputData'
    if not os.path.exists(outputDirectoryPath):
      os.makedirs(outputDirectoryPath)

    moduleWidget = slicer.modules.RegressionComputationWidget

    # Parameter by default
    moduleWidget.shapeInputDirectory.directory = inputDirectoryPath
    inputShapeParameters = {'SphereToEllipsoid_00':[16,30,0,1], 'SphereToEllipsoid_01':[17,10,0,1], 'SphereToEllipsoid_02':[19,10,0,1], 'SphereToEllipsoid_03':[21,10,0,1], 'SphereToEllipsoid_04':[24,10,0,1] } #[age, sigmaW, tris, weight]

    for row in range(0, moduleWidget.tableWidget_inputShapeParameters.rowCount):
      inputshaperootname = moduleWidget.tableWidget_inputShapeParameters.cellWidget(row, 0).text
      param = inputShapeParameters[inputshaperootname]
      for column in range (0,moduleWidget.tableWidget_inputShapeParameters.columnCount - 1):
        widget = moduleWidget.tableWidget_inputShapeParameters.cellWidget(row, column + 1)
        tuple = widget.children()
        spinBox = tuple[1]
        spinBox.value = param[column]

    moduleWidget.t0.value = 16
    moduleWidget.tn.value = 24
    moduleWidget.T.value = 10

    moduleWidget.defKernelWidth.value = 70
    moduleWidget.kernelType.setCurrentIndex(1)  # p3m
    moduleWidget.regularityWeight.value = 0.01

    moduleWidget.outputDirectory.directory = outputDirectoryPath
    moduleWidget.outputPrefix.text = "regression_"
    moduleWidget.saveEveryN.value = 5

    moduleWidget.estimateBaseline.setCheckState(qt.Qt.Unchecked)
    moduleWidget.optimMethod.setCurrentIndex(0)  # Gradient descent
    moduleWidget.breakRatio.value = 0.00001
    moduleWidget.maxIters.value = 3000

    self.addObserver(moduleWidget.Logic.shape4D_cli_node, slicer.vtkMRMLCommandLineModuleNode().StatusModifiedEvent,
                     self.onLogicModifiedForTests)


    self.delayDisplay('Run Regression Computation')
    moduleWidget.applyButton.click()

  def onLogicModifiedForTests(self, logic_node, event):
    status = logic_node.GetStatusString()
    if not logic_node.IsBusy():
      if status == 'Completed with errors' or status == 'Cancelled':
        self.removeObserver(logic_node, slicer.vtkMRMLCommandLineModuleNode().StatusModifiedEvent,
                            self.onLogicModifiedForTests)
        self.delayDisplay('Tests Failed!')
      elif status == 'Completed':
        self.removeObserver(logic_node, slicer.vtkMRMLCommandLineModuleNode().StatusModifiedEvent,
                            self.onLogicModifiedForTests)

        # If Shape Analysis Module is completed without errors, then run some other tests on the generated outputs
        self.assertTrue(self.test_Shape4D())
        slicer.mrmlScene.Clear(0)
        self.delayDisplay('Tests Passed!')

  def test_Shape4D(self):
    self.delayDisplay('Test: Comparison of the outputs generated by Shape4D CLI')

    # Checking the existence of the output directory Step3_ParaToSPHARMMesh
    outputDirectoryPath = slicer.app.temporaryPath + '/RegressionComputationOutputData'

    # Downloading output data to compare with the ones generated by Shape Analysis Module during the tests
    comparison_output_downloads = (
      ('https://data.kitware.com/api/v1/file/5a66bad88d777f0649e0322c/download', 'comparison_regression_final_time_000.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e0322f/download', 'comparison_regression_final_time_001.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e03232/download', 'comparison_regression_final_time_002.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e03235/download', 'comparison_regression_final_time_003.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e03238/download', 'comparison_regression_final_time_004.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e0323b/download', 'comparison_regression_final_time_005.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bad98d777f0649e0323e/download', 'comparison_regression_final_time_006.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bada8d777f0649e03241/download', 'comparison_regression_final_time_007.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bada8d777f0649e03244/download', 'comparison_regression_final_time_008.vtk'),
      ('https://data.kitware.com/api/v1/file/5a66bada8d777f0649e03247/download', 'comparison_regression_final_time_009.vtk'),
    )
    self.download_files(outputDirectoryPath, comparison_output_downloads)

    comparison_filenames = [name for download, name in comparison_output_downloads]
    for index, comparison_filename in enumerate(comparison_filenames):
      # output_filename = "regression_final_time_0" + str(index).zfill(2) + ".vtk"
      output_filename = "regression_final_time_" + "{:03}".format(index) + ".vtk"
      output_filepath = os.path.join(outputDirectoryPath, output_filename)
      #   Checking the existence of the output files in the folder Step3_ParaToSPHARMMesh
      if not os.path.exists(output_filepath):
        logging.info("Fail: Path does not exist: {}".format(output_filepath))
        return False

      #   Loading the 2 models for comparison
      comparison_output_rootname = comparison_filename.split(".")[0]
      output_rootname = output_filename.split(".")[0]
      success, model1 = slicer.util.loadModel(os.path.join(outputDirectoryPath, comparison_filename), returnNode=True)
      model1.SetName(comparison_output_rootname)
      success, model2 = slicer.util.loadModel(output_filepath, returnNode=True)
      model2.SetName(output_rootname)

      #   Comparison
      if not self.polydata_comparison(model1.GetPolyData(), model2.GetPolyData()):
        logging.warning("Fail: Data comparison for data {}, {}.".format(index, output_filename))
        return False

    return True

  def polydata_comparison(self, polydata1, polydata2):
    # Number of points
    nbPoints1 = polydata1.GetNumberOfPoints()
    nbPoints2 = polydata2.GetNumberOfPoints()
    if not nbPoints1 == nbPoints2:
      logging.warning("Fail polydata_comparison in nbPoints. model1Points {} != model2Points {}".format(nbPoints1, nbPoints2))
      return False

    # Polydata
    data1 = polydata1.GetPoints().GetData()
    data2 = polydata2.GetPoints().GetData()

    #   Number of Components
    nbComponents1 = data1.GetNumberOfComponents()
    nbComponents2 = data2.GetNumberOfComponents()
    if not nbComponents1 == nbComponents2:
      logging.warning("Fail polydata_comparison in nbComponents. model1Components {} != model2Components {}".format(nbComponents1, nbComponents2))
      return False

    #   Points value
    for i in range(nbPoints1):
      for j in range(nbComponents1):
        if not data1.GetTuple(i)[j] == data2.GetTuple(i)[j]:
          logging.warning("Fail polydata_comparison in PointsValues. point:{}, component:{}".format(i, j))
          return False

    # Area
    nbAreas1 = polydata1.GetPointData().GetNumberOfArrays()
    nbAreas2 = polydata2.GetPointData().GetNumberOfArrays()
    if not nbAreas1 == nbAreas2:
      logging.warning("Fail polydata_comparison in nbAreas. model1Areas {} != model2Areas {}".format(nbAreas1, nbAreas2))
      return False

    for l in range(nbAreas1):
      area1 = polydata1.GetPointData().GetArray(l)
      area2 = polydata2.GetPointData().GetArray(l)

      #   Name of the area
      nameArea1 = area1.GetName()
      nameArea2 = area2.GetName()
      if not nameArea1 == nameArea2:
        logging.warning("Fail polydata_comparison in name of areas. model1AreaName {} != model2AreaName {}".format(nameArea1, nameArea2))
        return False

      # Number of Components of the area
      nbComponents1 = area1.GetNumberOfComponents()
      nbComponents2 = area2.GetNumberOfComponents()
      if not nbComponents1 == nbComponents2:
        logging.warning("Fail polydata_comparison in nbComponents of areas. model1Components {} != model2Components {}".format(nbComponents1, nbComponents2))
        return False

      # Points value in the area
      for i in range(nbPoints1):
        for j in range(nbComponents1):
          if not data1.GetTuple(i)[j] == data2.GetTuple(i)[j]:
            logging.warning("Fail polydata_comparison in areas. point:{}, component:{}".format(i, j))
            return False

    return True

  def download_files(self, directoryPath, downloads):
    self.delayDisplay('Starting download')
    for url, name in downloads:
      filePath = os.path.join(directoryPath, name)
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
    self.delayDisplay('Finished with download')
