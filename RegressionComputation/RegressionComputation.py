import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import platform
import csv
import logging
from ShapeRegressionUtilities import *
import urllib

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
    self.tabWidget_InputShapes = self.getWidget('tabWidget_InputShapes')
    self.shapeInputDirectory = self.getWidget('DirectoryButton_ShapeInput')
    self.tableWidget_inputShapeParameters = self.getWidget('tableWidget_inputShapeParameters')
    self.PathLineEdit_ShapeInputsCSV = self.getWidget('PathLineEdit_ShapeInputsCSV')

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

    if self.interface.tabWidget_InputShapes.currentIndex == 0:
      # Write CSV file containing the parameters for each shapes
      self.pathToCSV = self.writeCSVInputshapesparameters()
    else:
      self.pathToCSV = self.interface.PathLineEdit_ShapeInputsCSV.currentPath
      if not os.path.exists(self.pathToCSV):
        self.interface.warningMessage('The CSV filepath is not existing.', None)
        return
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

    table = self.interface.tableWidget_inputShapeParameters
    # Sort the shape input data according to their age
    age_list = list()
    for row in range(table.rowCount):
        widget = table.cellWidget(row, 1)
        tuple = widget.children()
        spinbox = tuple[1]
        age_list.append(spinbox.value)

    age_list = sorted(age_list)
    parameters_sorted = dict()
    for row in range(table.rowCount):
      index = age_list.index(table.cellWidget(row, 1).children()[1].value)
      parameters_sorted[index] = list()
      inputshaperootname = table.cellWidget(row, 0).text
      inputshapefilepath = inputShapesDirectory + "/" + inputshaperootname + ".vtk"
      parameters_sorted[index].append(inputshapefilepath)
      for column in range(1, table.columnCount):
        widget = table.cellWidget(row, column)
        tuple = widget.children()
        spinbox = tuple[1]
        parameters_sorted[index].append(spinbox.value)

    # Write the parameters needed in a CSV file
    CSVInputshapesparametersfilepath = os.path.join(outputDirectory, "CVSInputshapesparameters.csv")
    file = open(CSVInputshapesparametersfilepath, 'w')
    cw = csv.writer(file, delimiter=',')
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
      ('https://data.kitware.com/api/v1/file/5a5c16c98d777f5e872f84d1/download', 'SphereToEllipsoid_00.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5c16ca8d777f5e872f84d4/download', 'SphereToEllipsoid_01.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5c16ca8d777f5e872f84d7/download', 'SphereToEllipsoid_02.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5c16cc8d777f5e872f84da/download', 'SphereToEllipsoid_03.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5c16cc8d777f5e872f84dd/download', 'SphereToEllipsoid_04.vtk'),
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
    moduleWidget.optimMethod.setCurrentIndex(0)  # FISTA
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
      ('https://data.kitware.com/api/v1/file/5a5d0dd58d777f5e872f8547/download', 'comparison_regression_final_time_000.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd68d777f5e872f854a/download', 'comparison_regression_final_time_001.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd68d777f5e872f854d/download', 'comparison_regression_final_time_002.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd68d777f5e872f8550/download', 'comparison_regression_final_time_003.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd78d777f5e872f8553/download', 'comparison_regression_final_time_004.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd78d777f5e872f8556/download', 'comparison_regression_final_time_005.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd78d777f5e872f8559/download', 'comparison_regression_final_time_006.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd88d777f5e872f855c/download', 'comparison_regression_final_time_007.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd88d777f5e872f855f/download', 'comparison_regression_final_time_008.vtk'),
      ('https://data.kitware.com/api/v1/file/5a5d0dd88d777f5e872f8562/download', 'comparison_regression_final_time_009.vtk'),
    )
    self.download_files(outputDirectoryPath, comparison_output_downloads)

    for i in range(10):
      output_filename = "regression_final_time_00" + str(i) + ".vtk"
      output_filepath = os.path.join(outputDirectoryPath, output_filename)
      #   Checking the existence of the output files in the folder Step3_ParaToSPHARMMesh
      if not os.path.exists(output_filepath):
        return False

      #   Loading the 2 models for comparison
      comparison_output_rootname = comparison_output_downloads[i][1].split(".")[0]
      output_rootname = output_filename.split(".")[0]
      model1 = MRMLUtility.loadMRMLNode(comparison_output_rootname, outputDirectoryPath, comparison_output_downloads[i][1], 'ModelFile')
      model2 = MRMLUtility.loadMRMLNode(output_rootname, outputDirectoryPath, output_filename, 'ModelFile')

      #   Comparison
      if not self.polydata_comparison(model1, model2):
        print model1
        print model2
        return False

    return True

  def polydata_comparison(self, model1, model2):
    polydata1 = model1.GetPolyData()
    polydata2 = model2.GetPolyData()

    # Number of points
    nbPoints1 = polydata1.GetNumberOfPoints()
    nbPoints2 = polydata2.GetNumberOfPoints()
    if not nbPoints1 == nbPoints2:
      return False

    # Polydata
    data1 = polydata1.GetPoints().GetData()
    data2 = polydata2.GetPoints().GetData()

    #   Number of Components
    nbComponents1 = data1.GetNumberOfComponents()
    nbComponents2 = data2.GetNumberOfComponents()
    if not nbComponents1 == nbComponents2:
      return False

    #   Points value
    for i in range(nbPoints1):
      for j in range(nbComponents1):
        if not data1.GetTuple(i)[j] == data2.GetTuple(i)[j]:
          return False

    # Area
    nbAreas1 = polydata1.GetPointData().GetNumberOfArrays()
    nbAreas2 = polydata2.GetPointData().GetNumberOfArrays()
    if not nbAreas1 == nbAreas2:
      return False

    for l in range(nbAreas1):
      area1 = polydata1.GetPointData().GetArray(l)
      area2 = polydata2.GetPointData().GetArray(l)

      #   Name of the area
      nameArea1 = area1.GetName()
      nameArea2 = area2.GetName()
      if not nameArea1 == nameArea2:
        return False

      # Number of Components of the area
      nbComponents1 = area1.GetNumberOfComponents()
      nbComponents2 = area2.GetNumberOfComponents()
      if not nbComponents1 == nbComponents2:
        return False

      # Points value in the area
      for i in range(nbPoints1):
        for j in range(nbComponents1):
          if not data1.GetTuple(i)[j] == data2.GetTuple(i)[j]:
            return False

    return True

  def download_files(self, directoryPath, downloads):
    self.delayDisplay('Starting download')
    for url, name in downloads:
      filePath = os.path.join(directoryPath, name)
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print 'Requesting download %s from %s...\n' % (name, url)
        urllib.urlretrieve(url, filePath)
    self.delayDisplay('Finished with download')
