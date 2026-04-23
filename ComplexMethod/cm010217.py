def _staged_schema():
    yaml_ret: dict[str, Any] = {}
    defs = {}
    cpp_enum_defs: dict[str, str] = {}
    cpp_class_defs: dict[str, str] = {}
    cpp_type_decls: list[str] = []
    cpp_json_defs: list[str] = []
    thrift_enum_defs: list[str] = []
    thrift_type_defs: dict[str, str] = {}

    def _handle_aggregate(ty) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        def dump_type(t, level: int) -> tuple[str, str, str]:
            if getattr(t, "__name__", None) in cpp_enum_defs:
                return t.__name__, "int64_t", t.__name__
            elif t in _CPP_TYPE_MAP:
                return (t.__name__, _CPP_TYPE_MAP[t], _THRIFT_TYPE_MAP[t])
            elif isinstance(t, str):
                if t not in defs:
                    raise AssertionError(f"type {t} not in defs")
                if t in cpp_enum_defs:
                    raise AssertionError(f"type {t} unexpectedly in cpp_enum_defs")
                if "[" in t:
                    raise AssertionError(f"type {t} contains '[' which is not allowed")
                return t, f"ForwardRef<{t}>", t
            elif isinstance(t, ForwardRef):
                return (
                    t.__forward_arg__,
                    f"ForwardRef<{t.__forward_arg__}>",
                    t.__forward_arg__,
                )
            elif o := typing.get_origin(t):
                # Lemme know if there's a better way to do this.
                if o is list:
                    yaml_head, cpp_head, thrift_head, thrift_tail = (
                        "List",
                        "std::vector",
                        "list<",
                        ">",
                    )
                elif o is dict:
                    yaml_head, cpp_head, thrift_head, thrift_tail = (
                        "Dict",
                        "std::unordered_map",
                        "map<",
                        ">",
                    )
                elif o is Union or o is types.UnionType:
                    if level != 0:
                        raise AssertionError(
                            f"Optional is only supported at the top level, got level={level}"
                        )
                    args = typing.get_args(t)
                    if len(args) != 2 or args[1] is not type(None):
                        raise AssertionError(
                            f"expected Optional type with 2 args ending in None, got {args}"
                        )
                    yaml_type, cpp_type, thrift_type = dump_type(args[0], level + 1)
                    return (
                        f"Optional[{yaml_type}]",
                        f"std::optional<{cpp_type}>",
                        f"optional {thrift_type}",
                    )
                elif o is Annotated:
                    return dump_type(t.__origin__, level)
                else:
                    raise AssertionError(f"Type {t} is not supported in export schema.")
                yaml_arg_types, cpp_arg_types, thrift_arg_types = zip(
                    *[dump_type(x, level + 1) for x in typing.get_args(t)]
                )
                return (
                    (f"{yaml_head}[{', '.join(yaml_arg_types)}]"),
                    (f"{cpp_head}<{', '.join(cpp_arg_types)}>"),
                    f"{thrift_head}{', '.join(thrift_arg_types)}{thrift_tail}",
                )
            elif isinstance(t, type):
                return (t.__name__, t.__name__, t.__name__)
            else:
                raise AssertionError(f"Type {t} is not supported in export schema.")

        def dump_cpp_value(v) -> str:
            if v is None:
                return "std::nullopt"
            elif v is True:
                return "true"
            elif v is False:
                return "false"
            elif v == {}:
                return "{}"
            elif v == []:
                return "{}"
            elif v == ():
                return "{}"
            elif isinstance(v, str):
                return f'"{v}"'
            else:
                raise AssertionError(
                    f"Default value {v} is not supported yet in export schema."
                )

        def dump_field(f) -> tuple[dict[str, Any], str, str | None, str, int]:
            t, cpp_type, thrift_type = dump_type(f.type, 0)
            ret = {"type": t}
            cpp_default: str | None = None
            if typing.get_origin(f.type) is not Annotated:
                raise AssertionError(
                    f"Field {f.name} must be annotated with an integer id."
                )
            thrift_id = f.type.__metadata__[0]
            if type(thrift_id) is not int:
                raise AssertionError(
                    f"Field {f.name} must be annotated with an integer id, got {type(thrift_id)}"
                )

            value = dataclasses.MISSING
            if f.default is not dataclasses.MISSING:
                value = f.default
            elif f.default_factory is not dataclasses.MISSING:
                value = f.default_factory()

            if value is not dataclasses.MISSING:
                default = str(value)
                ret["default"] = default
                cpp_default = dump_cpp_value(value)

                if t.startswith("Optional[") and value is not None:
                    raise AssertionError(
                        f"Optional field {ty.__name__}.{f.name} must have default value to be None."
                    )

            return ret, cpp_type, cpp_default, thrift_type, thrift_id

        yaml_ret = {}
        cpp_ret = {}
        thrift_ret = {}
        thrift_ids = set()
        for f in dataclasses.fields(ty):
            yaml_res, cpp_type, cpp_default, thrift_type, thrift_id = dump_field(f)
            yaml_ret[f.name] = yaml_res
            cpp_ret[f.name] = {"cpp_type": cpp_type, "cpp_default": cpp_default}
            thrift_ret[f.name] = {"thrift_type": thrift_type, "thrift_id": thrift_id}
            if thrift_id in thrift_ids:
                raise AssertionError(
                    f"Duplicate thrift id {thrift_id} for field {f.name} in {ty.__name__}."
                )
            thrift_ids.add(thrift_id)
        return yaml_ret, cpp_ret, thrift_ret

    def _handle_int_enum(name, ty):
        yaml_ret[name] = {"kind": "enum", "fields": {x.name: x.value for x in ty}}
        cpp_enum_defs[name] = f"""
enum class {name} {{
{chr(10).join([f"  {x.name} = {x.value}," for x in ty])}
}};

inline std::string_view printEnum(const {name}& e) {{
  switch (e) {{
{chr(10).join([f"    case {name}::{x.name}: return {chr(34)}{x.name}{chr(34)};" for x in ty])}
    default:
      throw std::runtime_error("Unknown enum value");
  }}
}}

inline void parseEnum(std::string_view s, {name}& t) {{
{chr(10).join([f"  if (s == {chr(34)}{x.name}{chr(34)}) {{ t = {name}::{x.name}; return; }}" for x in ty])}
  throw std::runtime_error("Unknown enum value: " + std::string{{s}});
}}
"""
        thrift_enum_defs.append(
            f"""
enum {name} {{
{chr(10).join([f"  {x.name} = {x.value}," for x in ty])}
}}
"""
        )

    def _handle_struct(name, ty):
        fields, cpp_fields, thrift_fields = _handle_aggregate(ty)
        yaml_ret[name] = {"kind": "struct", "fields": fields}
        field_decls = "\n".join(
            f"  {f['cpp_type']} {name}{' = ' + f['cpp_default'] if f['cpp_default'] is not None else ''};"
            for name, f in cpp_fields.items()
        )

        def accessor(name, ty):
            type_name = fields[name]["type"]
            if type_name in cpp_enum_defs:
                return f"""
  {type_name} get_{name}() const {{
    return static_cast<{type_name}>({name});
  }}

  void set_{name}({type_name} def) {{
    {name} = static_cast<int64_t>(def);
  }}
"""
            return f"""
  const {ty}& get_{name}() const {{
    return {name};
  }}

  void set_{name}({ty} def) {{
    {name} = std::move(def);
  }}
"""

        to_json_decl = f"void to_json(nlohmann::json& nlohmann_json_j, const {name}& nlohmann_json_t)"
        to_json_def = f"""{{
{chr(10).join([f'  nlohmann_json_j["{name}"] = nlohmann_json_t.{name};' for name, f in cpp_fields.items()])}
}}
"""
        from_json_decl = f"void from_json(const nlohmann::json& nlohmann_json_j, {name}& nlohmann_json_t)"

        from_json_def = f"""{{
  {name} nlohmann_json_default_obj;
{
            chr(10).join(
                [
                    f'  nlohmann_json_t.{name} = nlohmann_json_j.value("{name}", nlohmann_json_default_obj.{name});'
                    for name, f in cpp_fields.items()
                ]
            )
        }
}}
"""
        cpp_class_defs[name] = f"""
class {name} {{
 private:
{field_decls}

 public:
{"".join([accessor(name, f["cpp_type"]) for name, f in cpp_fields.items()])}
  friend {to_json_decl};
  friend {from_json_decl};
}};
"""
        cpp_json_defs.append(f"inline {to_json_decl} {to_json_def}")
        cpp_json_defs.append(f"inline {from_json_decl} {from_json_def}")
        cpp_type_decls.append(f"class {name};")

        thrift_type_defs[name] = f"""
struct {name} {{
{chr(10).join(f"  {f['thrift_id']}: {f['thrift_type']} {n};" for n, f in thrift_fields.items())}
}}"""

    def _handle_union(name, ty):
        fields, cpp_fields, thrift_fields = _handle_aggregate(ty)
        yaml_ret[name] = {"kind": "union", "fields": fields}

        def accessor(name, ty, idx):
            return f"""
  const {ty}& get_{name}() const {{
    return std::get<{idx + 1}>(variant_);
  }}

  void set_{name}({ty} def) {{
    variant_.emplace<{idx + 1}>(std::move(def));
    tag_ = Tag::{name.upper()};
  }}
"""

        to_json_branches = "".join(
            [
                f"""
    if (nlohmann_json_t.tag_ == Tag::{name.upper()}) {{
      nlohmann_json_j["{name}"] = nlohmann_json_t.get_{name}();
      return;
    }}"""
                for idx, (name, f) in enumerate(cpp_fields.items())
            ]
        )
        from_json_branches = "".join(
            [
                f"""
    if (nlohmann_json_j.contains("{name}")) {{
      nlohmann_json_t.variant_.emplace<{idx + 1}>(nlohmann_json_j.at("{name}").template get<{f["cpp_type"]}>());
      nlohmann_json_t.tag_ = Tag::{name.upper()};
      return;
    }}"""
                for idx, (name, f) in enumerate(cpp_fields.items())
            ]
        )

        cpp_class_defs[name] = f"""
class {name} {{
  struct Void {{}};

 public:
  enum class Tag {{
    {", ".join([name.upper() for name in cpp_fields])}
  }};

 private:
  std::variant<Void, {", ".join(f["cpp_type"] for f in cpp_fields.values())}> variant_;
  Tag tag_;

 public:
  Tag tag() const {{
    return tag_;
  }}
{"".join([accessor(name, f["cpp_type"], idx) for idx, (name, f) in enumerate(cpp_fields.items())])}
  friend void to_json(nlohmann::json& nlohmann_json_j, const {name}& nlohmann_json_t) {{
{to_json_branches}
  }}

  friend void from_json(const nlohmann::json& nlohmann_json_j, {name}& nlohmann_json_t) {{
{from_json_branches}
  }}
}};

inline std::string_view printEnum(const {name}::Tag& e) {{
  switch (e) {{
{chr(10).join([f"    case {name}::Tag::{x.upper()}: return {chr(34)}{x.upper()}{chr(34)};" for x in cpp_fields])}
    default:
      throw std::runtime_error("Unknown enum value");
  }}
}}

inline void parseEnum(std::string_view s, {name}::Tag& t) {{
{chr(10).join([f"  if (s == {chr(34)}{x.upper()}{chr(34)}) {{ t = {name}::Tag::{x.upper()}; return; }}" for x in cpp_fields])}
  throw std::runtime_error("Unknown enum value: " + std::string{{s}});
}}

"""
        cpp_type_decls.append(f"class {name};")

        thrift_type_defs[name] = f"""
union {name} {{
{chr(10).join(f"  {f['thrift_id']}: {f['thrift_type']} {n};" for n, f in thrift_fields.items())}
}}"""

    for name in dir(schema):
        if name.startswith("_"):
            continue

        value = getattr(schema, name)

        if hasattr(value, "__module__") and value.__module__ != schema.__name__:
            continue

        defs[name] = value

    class_ordering = {}
    for name, value in defs.items():
        if isinstance(value, type):
            if issubclass(value, IntEnum):
                _handle_int_enum(name, value)
            elif dataclasses.is_dataclass(value):
                class_ordering[name] = inspect.findsource(value)[1]
                if issubclass(value, _Union):
                    _handle_union(name, value)
                else:
                    _handle_struct(name, value)
            else:
                raise AssertionError(f"Unknown schema type {name}: {value}")
        elif isinstance(value, (int, tuple)):
            if name not in ("SCHEMA_VERSION", "TREESPEC_VERSION"):
                raise AssertionError(
                    f"expected SCHEMA_VERSION or TREESPEC_VERSION, got {name}"
                )
        elif isinstance(value, dict):
            # Skip mapping dictionaries used for codegen
            pass
        else:
            raise AssertionError(f"Unknown variable {name}: {value}")

    yaml_ret["SCHEMA_VERSION"] = list(defs["SCHEMA_VERSION"])
    if not all(x > 0 for x in yaml_ret["SCHEMA_VERSION"]):
        raise AssertionError(
            f"all SCHEMA_VERSION values must be > 0, got {yaml_ret['SCHEMA_VERSION']}"
        )
    yaml_ret["TREESPEC_VERSION"] = defs["TREESPEC_VERSION"]
    if yaml_ret["TREESPEC_VERSION"] <= 0:
        raise AssertionError(
            f"TREESPEC_VERSION must be > 0, got {yaml_ret['TREESPEC_VERSION']}"
        )

    cpp_header = f"""
#pragma once

#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <variant>
#include <vector>

#include <nlohmann/json.hpp>

#ifndef NLOHMANN_JSON_NAMESPACE_BEGIN
#define NLOHMANN_JSON_NAMESPACE_BEGIN namespace nlohmann {{
#endif

#ifndef NLOHMANN_JSON_NAMESPACE_END
#define NLOHMANN_JSON_NAMESPACE_END }}
#endif

// https://github.com/nlohmann/json/pull/2117
NLOHMANN_JSON_NAMESPACE_BEGIN
template <typename T>
struct adl_serializer<std::optional<T>> {{
  static void to_json(json& j, const std::optional<T>& opt) {{
    if (opt == std::nullopt) {{
      j = nullptr;
    }} else {{
      j = *opt; // this will call adl_serializer<T>::to_json which will
                // find the free function to_json in T's namespace!
    }}
  }}

  static void from_json(const json& j, std::optional<T>& opt) {{
    if (j.is_null()) {{
      opt = std::nullopt;
    }} else {{
      opt = j.template get<T>(); // same as above, but with
                                 // adl_serializer<T>::from_json
    }}
  }}
}};
NLOHMANN_JSON_NAMESPACE_END

namespace torch {{
namespace _export {{

template <typename T>
class ForwardRef {{
  static_assert(!std::is_reference_v<T>, "ForwardRef cannot be a reference type");

 public:
  ForwardRef(): ptr_(std::make_unique<T>()) {{}}
  ForwardRef(ForwardRef<T>&&);
  ForwardRef(const ForwardRef<T>& other): ptr_(std::make_unique<T>(*other.ptr_)) {{}}
  ForwardRef<T>& operator=(ForwardRef<T>&&);
  ForwardRef<T>& operator=(const ForwardRef<T>& other) {{
    ptr_ = std::make_unique<T>(*other.ptr_);
    return *this;
  }}
  ~ForwardRef();
  const T& operator*() const {{
    return *ptr_;
  }}

  const T* operator->() const {{
    return ptr_.get();
  }}

  void emplace(T&& t) {{
    ptr_ = std::make_unique<T>(std::move(t));
  }}

 private:
  std::unique_ptr<T> ptr_;
}};

template <typename T>
void to_json(nlohmann::json& j, const ForwardRef<T>& p) {{
  j = *p;
}}

template <typename T>
void from_json(const nlohmann::json& j, ForwardRef<T>& p) {{
  p.emplace(j.template get<T>());
}}

class F64 {{
 public:
  double get() const {{
    return value_;
  }}

  void set(double value) {{
    value_ = value;
  }}

 private:
  double value_;
}};

inline void to_json(nlohmann::json& j, const F64& f) {{
  if (std::isinf(f.get())) {{
    j = "Infinity";
  }} else if (std::isinf(-f.get())) {{
    j = "-Infinity";
  }} else if (std::isnan(f.get())) {{
    j = "NaN";
  }} else {{
    j = f.get();
  }}
}}

inline void from_json(const nlohmann::json& j, F64& f) {{
  if (j == "Infinity") {{
    f.set(std::numeric_limits<double>::infinity());
  }} else if (j == "-Infinity") {{
    f.set(-std::numeric_limits<double>::infinity());
  }} else if (j == "NaN") {{
    f.set(std::numeric_limits<double>::quiet_NaN());
  }} else {{
    f.set(j.get<double>());
  }}
}}

{chr(10).join(cpp_type_decls)}
{"".join(cpp_enum_defs.values())}
{"".join(dict(sorted(cpp_class_defs.items(), key=lambda x: class_ordering[x[0]])).values())}
{chr(10).join(cpp_json_defs)}

template <typename T> ForwardRef<T>::ForwardRef(ForwardRef<T>&&) = default;
template <typename T> ForwardRef<T>& ForwardRef<T>::operator=(ForwardRef<T>&&) = default;
template <typename T> ForwardRef<T>::~ForwardRef() = default;
}} // namespace _export
}} // namespace torch
"""
    thrift_schema = f"""
namespace py3 torch._export
namespace cpp2 torch._export.schema
{chr(10).join(thrift_enum_defs)}
{chr(10).join(dict(sorted(thrift_type_defs.items(), key=lambda x: class_ordering[x[0]])).values())}
"""
    return yaml_ret, cpp_header, thrift_schema