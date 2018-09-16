cmake_minimum_required(VERSION 3.5)

project(ShapeRegressionExtension)
set(PROJECT_NAME ShapeRegressionExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "")
set(EXTENSION_CATEGORY "Shape Regression")
set(EXTENSION_CONTRIBUTORS "Laura Pascal (Kitware Inc.), Beatriz Paniagua (Kitware Inc.), James Fishbaugh (University of North Carolina)")
set(EXTENSION_DESCRIPTION "Computation and visualization of time-regressed shapes in a collection of 3D shape inputs associated to a linear variable")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "Sequences")
set(EXTENSION_STATUS Beta)
set(EXTENSION_BUILD_SUBDIRECTORY ${PROJECT_NAME}-build)

set(SUPERBUILD_TOPLEVEL_PROJECT ${PROJECT_NAME})

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer 4.9 REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(RegressionComputation)
add_subdirectory(RegressionVisualization)
## NEXT_MODULE

#-----------------------------------------------------------------------------
# Copy the shape4D’s executable in the package 

set(shape4D_LIB_DIR ${EXTENSION_SUPERBUILD_BINARY_DIR}/shape4D-build/shape4D-build/${Slicer_CLIMODULES_LIB_DIR})
if(WIN32)
  set(DIRECTORY_shape4D ${shape4D_LIB_DIR}/$<CONFIG>/.)
else()
  set(DIRECTORY_shape4D ${shape4D_LIB_DIR}/.)
endif()

install(
  DIRECTORY ${DIRECTORY_shape4D}
  DESTINATION ${Slicer_INSTALL_CLIMODULES_LIB_DIR}/
  USE_SOURCE_PERMISSIONS
  COMPONENT Runtime
)

#-----------------------------------------------------------------------------
set(EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS)
set(${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS "${EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS}" CACHE STRING "List of external projects to install" FORCE)

#-----------------------------------------------------------------------------
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS}")
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
