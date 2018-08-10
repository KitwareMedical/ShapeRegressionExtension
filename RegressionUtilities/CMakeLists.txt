#-----------------------------------------------------------------------------
set(MODULE_NAME RegressionUtilities)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ShapeRegressionUtilities/__init__.py
  ShapeRegressionUtilities/utility.py
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  )
