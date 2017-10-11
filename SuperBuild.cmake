#-----------------------------------------------------------------------------
# Git protocol option
#-----------------------------------------------------------------------------
option(Slicer_USE_GIT_PROTOCOL "If behind a firewall turn this off to use http instead." ON)

set(git_protocol "git")
if(NOT Slicer_USE_GIT_PROTOCOL)
  set(git_protocol "http")
endif()

#-----------------------------------------------------------------------------
# Enable and setup External project global properties
#-----------------------------------------------------------------------------
set(ep_common_c_flags "${CMAKE_C_FLAGS_INIT} ${ADDITIONAL_C_FLAGS}")
set(ep_common_cxx_flags "${CMAKE_CXX_FLAGS_INIT} ${ADDITIONAL_CXX_FLAGS}")

#-----------------------------------------------------------------------------
# Project dependencies
#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

include(ExternalProject)

foreach(dep ${EXTENSION_DEPENDS})
  mark_as_superbuild(${dep}_DIR)
endforeach()

set(proj ${SUPERBUILD_TOPLEVEL_PROJECT})
list(APPEND ${proj}_DEPENDS shape4D)

#-----------------------------------------------------------------------------
# Windows configuration parameters
#-----------------------------------------------------------------------------
set(${proj}_config_parameters "")
if (WIN32)
  list(APPEND ${proj}_config_parameters "-DCMAKE_CONFIGURATION_TYPES:PATH=${CMAKE_CONFIGURATION_TYPES}")
endif()

#-----------------------------------------------------------------------------
# Slicer extension
#-----------------------------------------------------------------------------
if(${EXTENSION_NAME}_BUILD_SLICER_EXTENSION)
  # The inner build needs to know this to run 'make Experimental' from
  # the inner build folder (packaging is done in ShapeRegressionExtension-build).
  set(EXTENSION_SUPERBUILD_BINARY_DIR ${${EXTENSION_NAME}_BINARY_DIR})
  mark_as_superbuild(EXTENSION_SUPERBUILD_BINARY_DIR)
  # Inside the inner build, we need to know if we are building a Slicer extension
  # to know if we define the CMake `EXTENSION_*` variables.
  mark_as_superbuild(${EXTENSION_NAME}_BUILD_SLICER_EXTENSION:BOOL)
endif()

#-----------------------------------------------------------------------------
# Set superbuild CMake variables
#-----------------------------------------------------------------------------
ExternalProject_Include_Dependencies(${proj}
  PROJECT_VAR proj
  SUPERBUILD_VAR ${EXTENSION_NAME}_SUPERBUILD
  )

#-----------------------------------------------------------------------------
# Superbuild
#-----------------------------------------------------------------------------
ExternalProject_Add(${proj}
  ${${proj}_EP_ARGS}
  DOWNLOAD_COMMAND ""
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
  BINARY_DIR ${EXTENSION_BUILD_SUBDIRECTORY}
  BUILD_ALWAYS 1
  CMAKE_CACHE_ARGS
    ${${proj}_config_parameters}
    -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
    -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
    -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
    -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
    -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
    -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_RUNTIME_OUTPUT_DIRECTORY}
    -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_LIBRARY_OUTPUT_DIRECTORY}
    -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
    -DEXTENSION_SUPERBUILD_BINARY_DIR:PATH=${${EXTENSION_NAME}_BINARY_DIR}
    # Do not forget to deactivate "Superbuild" inside "ShapeRegressionExtension-build"
    -D${PROJECT_NAME}_SUPERBUILD:BOOL=OFF
    # We need to use Slicer to use `ExternalProject_Include_Dependencies()`
    # so we might as well use VTK and SEM
    -DUSE_VTK:BOOL=ON
    -DUSE_SEM:BOOL=ON
  INSTALL_COMMAND ""
  DEPENDS
    ${${proj}_DEPENDS}
  )
