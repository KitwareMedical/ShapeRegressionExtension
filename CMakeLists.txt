cmake_minimum_required(VERSION 2.8.9)

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

set(EXTENSION_BUILD_SUBDIRECTORY ${PROJECT_NAME}-build)
set(EXTENSION_STATUS Beta)

set(SUPERBUILD_TOPLEVEL_PROJECT ${PROJECT_NAME})

find_package(Git REQUIRED)
find_package(Subversion REQUIRED)
#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)
mark_as_superbuild(PYTHON_EXECUTABLE)
mark_as_superbuild(PYTHON_INCLUDE_DIR)
mark_as_superbuild(PYTHON_LIBRARY)

#-----------------------------------------------------------------------------
# Set a default build type if none was specified
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  message(STATUS "Setting build type to 'Release' as none was specified.")
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  # Set the possible values of build type for cmake-gui
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

#-----------------------------------------------------------------------------
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(RegressionUtilities)
add_subdirectory(RegressionComputation)
add_subdirectory(RegressionVisualization)

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
# CPACK
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
include(${Slicer_EXTENSION_CPACK})