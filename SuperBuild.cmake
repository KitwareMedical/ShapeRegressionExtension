include(FetchContent)

#-----------------------------------------------------------------------------
# Bundle remote modules and extensions adding source directories.
#-----------------------------------------------------------------------------

# shape4D
set(extension_name "shape4D")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/slicersalt/shape4D.git
  GIT_TAG        67201a6aaaaacc8677180f02af5e4a8348c1b673 # slicersalt-2018-11-27-215f0b6
  GIT_PROGRESS   1
  QUIET
  )
set(shape4D_SOURCE_DIR ${${extension_name}_SOURCE_DIR})
message(STATUS "Remote - ${extension_name} [OK]")
mark_as_superbuild(shape4D_SOURCE_DIR:PATH)

set(shape4D_SUPERBUILD OFF)
mark_as_superbuild(shape4D_SUPERBUILD:BOOL)

set(shape4D_USE_SEM ON)
mark_as_superbuild(shape4D_USE_SEM:BOOL)

set(shape4D_USE_VTK ON)
mark_as_superbuild(shape4D_USE_VTK:BOOL)

list(APPEND EXTERNAL_PROJECT_ADDITIONAL_DIRS
  ${shape4D_SOURCE_DIR}/SuperBuild
  )

#-----------------------------------------------------------------------------
# Enable and setup External project global properties
#-----------------------------------------------------------------------------
set(ep_common_c_flags "${CMAKE_C_FLAGS_INIT} ${ADDITIONAL_C_FLAGS}")
set(ep_common_cxx_flags "${CMAKE_CXX_FLAGS_INIT} ${ADDITIONAL_CXX_FLAGS}")

#-----------------------------------------------------------------------------
# Top-level "external" project
#-----------------------------------------------------------------------------

foreach(dep ${EXTENSION_DEPENDS})
  mark_as_superbuild(${dep}_DIR)
endforeach()

set(proj ${SUPERBUILD_TOPLEVEL_PROJECT})

set(${proj}_DEPENDS
  FFTW
  )

# Set superbuild CMake variables
ExternalProject_Include_Dependencies(${proj}
  PROJECT_VAR proj
  SUPERBUILD_VAR ${EXTENSION_NAME}_SUPERBUILD
  )

# Superbuild
ExternalProject_Add(${proj}
  ${${proj}_EP_ARGS}
  DOWNLOAD_COMMAND ""
  INSTALL_COMMAND ""
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
  BINARY_DIR ${EXTENSION_BUILD_SUBDIRECTORY}
  CMAKE_CACHE_ARGS
    # Compiler settings
    -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
    -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
    -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
    -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
    -DCMAKE_CXX_STANDARD:STRING=${CMAKE_CXX_STANDARD}
    -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=${CMAKE_CXX_STANDARD_REQUIRED}
    -DCMAKE_CXX_EXTENSIONS:BOOL=${CMAKE_CXX_EXTENSIONS}
    # Output directories
    -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_RUNTIME_OUTPUT_DIRECTORY}
    -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_LIBRARY_OUTPUT_DIRECTORY}
    -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
    # Superbuild
    -DEXTENSION_SUPERBUILD_BINARY_DIR:PATH=${${EXTENSION_NAME}_BINARY_DIR}
    -D${PROJECT_NAME}_SUPERBUILD:BOOL=OFF # Do not forget to deactivate "Superbuild" inside "ShapeRegressionExtension-build"
  DEPENDS
    ${${proj}_DEPENDS}
  )

ExternalProject_AlwaysConfigure(${proj})
