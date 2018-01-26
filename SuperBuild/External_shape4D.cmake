#============================================================================
#
# Copyright (c) Kitware, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#============================================================================
#
# External project for the project.
#

set(proj shape4D)

# Set dependency list
set(${proj}_DEPENDENCIES "")

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED ${proj}_DIR AND NOT EXISTS ${${proj}_DIR})
  message(FATAL_ERROR "${proj}_DIR variable is defined but corresponds to non-existing directory")
endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(NOT DEFINED git_protocol)
    set(git_protocol "git")
  endif()

  set(config ${CMAKE_BUILD_TYPE})
  if(DEFINED CMAKE_CONFIGURATION_TYPES)
    set(config ${CMAKE_CFG_INTDIR})
  endif()

  set(${proj}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)
  set(${proj}_PACKAGE_DIR ${${proj}_DIR}/${proj}-build)

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${git_protocol}://github.com/laurapascal/shape4D.git"
    GIT_TAG "5eca96de59ed4c27fcabec88effa2d7af82c3af9"
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    BINARY_DIR ${${proj}_DIR}
    INSTALL_COMMAND ${CMAKE_COMMAND} --build ${${proj}_PACKAGE_DIR} --config ${config} --target package
    CMAKE_CACHE_ARGS
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DSlicer_DIR:PATH=${Slicer_DIR}
      -D${proj}_BUILD_SLICER_EXTENSION:BOOL=ON
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDENCIES})
endif()
