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