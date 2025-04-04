// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from my_robot_interfaces:msg/LedStateArray.idl
// generated code does not contain a copyright notice

#include "my_robot_interfaces/msg/detail/led_state_array__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_my_robot_interfaces
const rosidl_type_hash_t *
my_robot_interfaces__msg__LedStateArray__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x78, 0x02, 0x98, 0xed, 0x87, 0x94, 0x39, 0xb2,
      0x1a, 0xff, 0x5b, 0x20, 0x52, 0x69, 0x2c, 0x12,
      0x06, 0x8f, 0x74, 0x1c, 0xb1, 0x22, 0x24, 0x96,
      0x0c, 0x90, 0xbe, 0x80, 0x79, 0x60, 0xdc, 0x08,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char my_robot_interfaces__msg__LedStateArray__TYPE_NAME[] = "my_robot_interfaces/msg/LedStateArray";

// Define type names, field names, and default values
static char my_robot_interfaces__msg__LedStateArray__FIELD_NAME__led_states[] = "led_states";

static rosidl_runtime_c__type_description__Field my_robot_interfaces__msg__LedStateArray__FIELDS[] = {
  {
    {my_robot_interfaces__msg__LedStateArray__FIELD_NAME__led_states, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT64_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
my_robot_interfaces__msg__LedStateArray__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {my_robot_interfaces__msg__LedStateArray__TYPE_NAME, 37, 37},
      {my_robot_interfaces__msg__LedStateArray__FIELDS, 1, 1},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "int64[] led_states";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
my_robot_interfaces__msg__LedStateArray__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {my_robot_interfaces__msg__LedStateArray__TYPE_NAME, 37, 37},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 18, 18},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
my_robot_interfaces__msg__LedStateArray__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *my_robot_interfaces__msg__LedStateArray__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
