
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
  shape4D
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
