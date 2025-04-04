// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from my_robot_interfaces:srv/CatchTurtle.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "my_robot_interfaces/srv/catch_turtle.hpp"


#ifndef MY_ROBOT_INTERFACES__SRV__DETAIL__CATCH_TURTLE__BUILDER_HPP_
#define MY_ROBOT_INTERFACES__SRV__DETAIL__CATCH_TURTLE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "my_robot_interfaces/srv/detail/catch_turtle__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace my_robot_interfaces
{

namespace srv
{

namespace builder
{

class Init_CatchTurtle_Request_name
{
public:
  Init_CatchTurtle_Request_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::my_robot_interfaces::srv::CatchTurtle_Request name(::my_robot_interfaces::srv::CatchTurtle_Request::_name_type arg)
  {
    msg_.name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::my_robot_interfaces::srv::CatchTurtle_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::my_robot_interfaces::srv::CatchTurtle_Request>()
{
  return my_robot_interfaces::srv::builder::Init_CatchTurtle_Request_name();
}

}  // namespace my_robot_interfaces


namespace my_robot_interfaces
{

namespace srv
{

namespace builder
{

class Init_CatchTurtle_Response_success
{
public:
  Init_CatchTurtle_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::my_robot_interfaces::srv::CatchTurtle_Response success(::my_robot_interfaces::srv::CatchTurtle_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return std::move(msg_);
  }

private:
  ::my_robot_interfaces::srv::CatchTurtle_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::my_robot_interfaces::srv::CatchTurtle_Response>()
{
  return my_robot_interfaces::srv::builder::Init_CatchTurtle_Response_success();
}

}  // namespace my_robot_interfaces


namespace my_robot_interfaces
{

namespace srv
{

namespace builder
{

class Init_CatchTurtle_Event_response
{
public:
  explicit Init_CatchTurtle_Event_response(::my_robot_interfaces::srv::CatchTurtle_Event & msg)
  : msg_(msg)
  {}
  ::my_robot_interfaces::srv::CatchTurtle_Event response(::my_robot_interfaces::srv::CatchTurtle_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::my_robot_interfaces::srv::CatchTurtle_Event msg_;
};

class Init_CatchTurtle_Event_request
{
public:
  explicit Init_CatchTurtle_Event_request(::my_robot_interfaces::srv::CatchTurtle_Event & msg)
  : msg_(msg)
  {}
  Init_CatchTurtle_Event_response request(::my_robot_interfaces::srv::CatchTurtle_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_CatchTurtle_Event_response(msg_);
  }

private:
  ::my_robot_interfaces::srv::CatchTurtle_Event msg_;
};

class Init_CatchTurtle_Event_info
{
public:
  Init_CatchTurtle_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CatchTurtle_Event_request info(::my_robot_interfaces::srv::CatchTurtle_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_CatchTurtle_Event_request(msg_);
  }

private:
  ::my_robot_interfaces::srv::CatchTurtle_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::my_robot_interfaces::srv::CatchTurtle_Event>()
{
  return my_robot_interfaces::srv::builder::Init_CatchTurtle_Event_info();
}

}  // namespace my_robot_interfaces

#endif  // MY_ROBOT_INTERFACES__SRV__DETAIL__CATCH_TURTLE__BUILDER_HPP_
