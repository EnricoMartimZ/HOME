# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_remy_odom_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED remy_odom_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(remy_odom_FOUND FALSE)
  elseif(NOT remy_odom_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(remy_odom_FOUND FALSE)
  endif()
  return()
endif()
set(_remy_odom_CONFIG_INCLUDED TRUE)

# output package information
if(NOT remy_odom_FIND_QUIETLY)
  message(STATUS "Found remy_odom: 0.0.0 (${remy_odom_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'remy_odom' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${remy_odom_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(remy_odom_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${remy_odom_DIR}/${_extra}")
endforeach()
