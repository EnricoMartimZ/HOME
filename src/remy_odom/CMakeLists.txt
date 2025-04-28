cmake_minimum_required(VERSION 3.8)
project(remy_odom)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

ament_python_install_package(${PROJECT_NAME})

find_package(ament_cmake REQUIRED)
find_package(serial REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(numpy REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(math REQUIRED)
find_package(tf_transformations REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(PROGRAMS
  ${PROJECT_NAME}/estado_motores_pub.py
  ${PROJECT_NAME}/odom_pub.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
