cmake_minimum_required(VERSION 3.5)

project(ShapeRegressionExtension)
set(PROJECT_NAME ShapeRegressionExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://salt.slicer.org/")
set(EXTENSION_CATEGORY "Shape Regression")
set(EXTENSION_CONTRIBUTORS "Laura Pascal (Kitware Inc.), Beatriz Paniagua (Kitware Inc.), James Fishbaugh (University of North Carolina)")
set(EXTENSION_DESCRIPTION "Computation and visualization of time-regressed shapes in a collection of 3D shape inputs associated to a linear variable")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/slicersalt/slicersalt.github.io/master/img/favicons/favicon-128.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/slicersalt/slicersalt.github.io/b34f1452faf111175b203d0172b6f45807d996e2/img/about-section/regression.gif")
set(EXTENSION_DEPENDS "NA")
set(EXTENSION_STATUS Beta)
set(EXTENSION_BUILD_SUBDIRECTORY ${PROJECT_NAME}-build)

set(SUPERBUILD_TOPLEVEL_PROJECT ${PROJECT_NAME})

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# Build option(s)
if(NOT DEFINED ShapeRegressionExtension_BUILD_TESTING)
  set(ShapeRegressionExtension_BUILD_TESTING ${BUILD_TESTING})
endif()
mark_as_superbuild(ShapeRegressionExtension_BUILD_TESTING:BOOL)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

if(NOT DEFINED Slicer_SOURCE_DIR)
  find_package(shape4D REQUIRED)
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(RegressionComputation)
add_subdirectory(RegressionVisualization)
## NEXT_MODULE

# XXX Packaging an extension within an extension is not supported on macOS
#if(APPLE)
#  set(${EXTENSION_NAME}_FIXUP_BUNDLE_LIBRARY_DIRECTORIES ${shape4D_FIXUP_BUNDLE_LIBRARY_DIRECTORIES} CACHE STRING "List of fixup bundle library directories" FORCE)
#endif()

#-----------------------------------------------------------------------------
set(EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS)
# XXX Packaging an extension within an extension is not supported on macOS
#list(APPEND EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS "${shape4D_DIR};shape4D;RuntimeLibraries;/")
set(${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS "${EXTENSION_CPACK_INSTALL_CMAKE_PROJECTS}" CACHE STRING "List of external projects to install" FORCE)

#-----------------------------------------------------------------------------
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
list(APPEND CPACK_INSTALL_CMAKE_PROJECTS "${${EXTENSION_NAME}_CPACK_INSTALL_CMAKE_PROJECTS}")
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
