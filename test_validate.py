import re
import sys
import unittest

from vtjson import (
    SchemaError,
    ValidationError,
    _keys,
    complement,
    date,
    date_time,
    domain_name,
    email,
    intersect,
    interval,
    ip_address,
    lax,
    make_type,
    number,
    quote,
    regex,
    set_name,
    strict,
    time,
    union,
    url,
    validate,
)


def show(mc):
    exception = mc.exception
    print(f"{exception.__class__.__name__}: {str(mc.exception)}")


class TestValidation(unittest.TestCase):
    def test_keys(self):
        schema = {"a?": 1, "b": 2, "c?": 3}
        keys = _keys(schema)
        self.assertEqual(keys, {"a", "b", "c"})

    def test_strict(self):
        with self.assertRaises(ValidationError) as mc:
            schema = {"a?": 1, "b": 2}
            object = {"b": 2, "c": 3}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = {"a": 1, "c": 3}
            validate(schema, object)
        show(mc)

        object = {"a": 1, "b": 2}
        validate(schema, object)

        object = {"b": 2}
        validate(schema, object)

    def test_missing_keys(self):
        schema = {"a?": 1, "b": 2}
        object = {"b": 2, "c": 3}
        validate(schema, object, strict=False)

        with self.assertRaises(ValidationError) as mc:
            object = {"a": 1, "c": 3}
            validate(schema, object, strict=False)
        show(mc)

        object = {"a": 1, "b": 2}
        validate(schema, object, strict=False)

        object = {"b": 2}
        validate(schema, object, strict=False)

        schema = {"a?": 1, "b": 2}
        object = {"b": 2, "c": 3}
        validate(schema, object, strict=False)

        with self.assertRaises(ValidationError) as mc:
            object = {"a": 1, "c": 3}
            validate(schema, object, strict=False)
        show(mc)

        object = {"a": 1, "b": 2}
        validate(schema, object, strict=False)

        object = {"b": 2}
        validate(schema, object, strict=False)

        with self.assertRaises(ValidationError) as mc:
            schema = ["a", "b"]
            object = ["a"]
            validate(schema, object, strict=False)

        object = ["a", "b"]
        validate(schema, object, strict=False)

        object = ["a", "b", "c"]
        validate(schema, object, strict=False)

        with self.assertRaises(ValidationError) as mc:
            object = ["a", "b", "c"]
            validate(schema, object, strict=True)
        show(mc)

    def test_union(self):
        schema = {"a?": 1, "b": union(2, 3)}
        object = {"b": 2, "c": 3}
        validate(schema, object, strict=False)

        with self.assertRaises(ValidationError) as mc:
            object = {"b": 4, "c": 3}
            validate(schema, object)
        show(mc)

    def test_quote(self):
        with self.assertRaises(ValidationError) as mc:
            schema = str
            object = str
            validate(schema, object)
        show(mc)

        schema = quote(str)
        validate(schema, object)

        schema = {1, 2}
        object = 1
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = quote({1, 2})
            object = 1
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = {1, 2}
            object = {1, 2}
            validate(schema, object)
        show(mc)

        schema = quote({1, 2})
        validate(schema, object)

    @unittest.skipUnless(
        sys.version_info.major == 3 and sys.version_info.minor >= 7,
        "datetime.datetime.fromisoformat was introduced in Python 3.7",
    )
    def test_date_time(self):
        with self.assertRaises(ValidationError) as mc:
            schema = date_time
            object = "2000-30-30"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "2000-12-300"
            validate(schema, object)
        show(mc)

        object = "2000-12-30"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = date_time("%Y^%m^%d")
            object = "2000^12^300"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "2000^12-30"
            validate(schema, object)
        show(mc)

        object = "2000^12^30"
        validate(schema, object)

    @unittest.skipUnless(
        sys.version_info.major == 3 and sys.version_info.minor >= 7,
        "datetime.date.fromisoformat was introduced in Python 3.7",
    )
    def test_date(self):
        schema = date
        object = "2023-10-10"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "2023-10-10T01:01:01"
            validate(schema, object)
        show(mc)

    @unittest.skipUnless(
        sys.version_info.major == 3 and sys.version_info.minor >= 7,
        "datetime.time.fromisoformat was introduced in Python 3.7",
    )
    def test_time(self):
        schema = time
        object = "01:01:01"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "2023-10-10T01:01:01"
            validate(schema, object)
        show(mc)

    def test_set(self):
        with self.assertRaises(ValidationError) as mc:
            schema = {2, 3}
            object = 5
            validate(schema, object, strict=False)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = {int, str}
            object = 1.0
            validate(schema, object, strict=False)
        show(mc)

    def test_intersect(self):
        with self.assertRaises(ValidationError) as mc:
            schema = intersect(url, regex(r"^https", fullmatch=False))
            object = "ftp://example.com"
            validate(schema, object)
        show(mc)

        object = "https://example.com"
        validate(schema, object)

        def ordered_pair(o):
            return o[0] <= o[1]

        with self.assertRaises(ValidationError) as mc:
            schema = intersect((int, int), ordered_pair)
            object = (3, 2)
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = (1, 3, 2)
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = ("a", "b")
            validate(schema, object)
        show(mc)

        object = (1, 2)
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = intersect(
                (int, int), set_name(lambda o: o[0] <= o[1], "ordered_pair")
            )
            object = (3, 2)
            validate(schema, object)
        show(mc)

    def test_complement(self):
        schema = intersect(url, complement(regex(r"^https", fullmatch=False)))
        object = "ftp://example.com"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "https://example.com"
            validate(schema, object)
        show(mc)

    def test_set_name(self):
        schema = set_name("a", "dummy")
        self.assertTrue(schema.__name__ == "dummy")

        with self.assertRaises(ValidationError) as mc:
            object = "b"
            validate(schema, object)
        show(mc)

        object = "a"
        validate(schema, object)

    def test_lax(self):
        schema = lax(["a", "b", "c"])
        object = ["a", "b", "c", "d"]
        validate(schema, object)

    def test_strict_wrapper(self):
        with self.assertRaises(ValidationError) as mc:
            schema = strict(["a", "b", "c"])
            object = ["a", "b", "c", "d"]
            validate(schema, object, strict=False)
        show(mc)

    def test_make_type(self):
        global url
        schema = {"a": 1}
        t = make_type(schema, "example", debug=True)
        self.assertTrue(t.__name__ == "example")
        self.assertFalse(isinstance({"a": 2}, t))
        self.assertTrue(isinstance({"a": 1}, t))
        self.assertFalse(isinstance({"a": 1, "b": 1}, t))

        t = make_type(schema, "example", strict=False, debug=True)
        self.assertTrue(t.__name__ == "example")
        self.assertTrue(isinstance({"a": 1, "b": 1}, t))

        url_ = make_type(url, debug=True)
        self.assertTrue(url_.__name__ == "url")
        self.assertFalse(isinstance("google.com", url_))
        self.assertTrue(isinstance("https://google.com", url_))

        country_code = make_type(regex("[A-ZA-Z]", "country_code"), debug=True)
        self.assertTrue(country_code.__name__ == "country_code")
        self.assertFalse(isinstance("BEL", country_code))

        t = make_type({}, debug=True)
        self.assertTrue(t.__name__ == "schema")

    def test_generics(self):
        with self.assertRaises(ValidationError) as mc:
            schema = [str, ...]
            object = ("a", "b")
            validate(schema, object)
        show(mc)

        object = ["a", "b"]
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = ["a", 10]
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = ["a", ["b", "c"]]
            validate(schema, object)
        show(mc)

        schema = [...]
        object = ["a", "b", 1, 2]
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = ["a", ...]
            object = ["a", "b"]
            validate(schema, object)
        show(mc)

        object = []
        validate(schema, object)

        object = ["a", "a"]
        validate(schema, object)

        object = ["a", "a", "a", "a", "a"]
        validate(schema, object)

        schema = ["a", "b", ...]
        object = ["a", "b"]
        validate(schema, object)

        schema = ["a", "b", "c", ...]
        object = ["a", "b"]
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = ["a", "b", "c", "d", ...]
            object = ["a", "b"]
            validate(schema, object)
        show(mc)

        schema = [(str, int), ...]
        object = [("a", 1), ("b", 2)]
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = [(str, int), ...]
            object = [("a", 1), ("b", "c")]
            validate(schema, object)

        schema = [email, ...]
        object = ["user1@example.com", "user2@example.com"]
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = [email, ...]
            object = ["user1@example.com", "user00@user00.user00"]
            validate(schema, object)
        show(mc)

    def test_sequence(self):
        with self.assertRaises(ValidationError) as mc:
            schema = {"a": 1}
            object = []
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = []
            object = (1, 2)
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = ["a", "b", None, "c"]
            object = ["a", "b"]
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = ["a", "b"]
            object = ["a", "b", None, "c"]
            validate(schema, object)
        show(mc)

    def test_validate(self):
        class lower_case_string:
            @staticmethod
            def __validate__(object, name, strict):
                if not isinstance(object, str):
                    return f"{name} (value:{object}) is not of type str"
                for c in object:
                    if not ("a" <= c <= "z"):
                        return (
                            f"{c}, contained in the string {name} "
                            + f"(value: {repr(object)}) is not a lower case letter"
                        )
                return ""

        with self.assertRaises(ValidationError) as mc:
            schema = lower_case_string
            object = 1
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "aA"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "aA"
            validate(schema, object)
        show(mc)

        object = "ab"
        validate(schema, object)

        schema = {"a": lower_case_string}
        object = {"a": "ab"}
        validate(schema, object)

        class lower_case_string:
            def __validate__(self, object, name, strict):
                if not isinstance(object, str):
                    return f"{name} (value:{object}) is not of type str"
                for c in object:
                    if not ("a" <= c <= "z"):
                        return (
                            f"{c}, contained in the string {name} "
                            + f"(value: {repr(object)}) is not a lower case letter"
                        )
                return ""

        schema = {"a": lower_case_string}
        object = {"a": "ab"}
        validate(schema, object)

    def test_regex(self):
        with self.assertRaises(SchemaError) as cm:
            regex({})
        show(cm)

        with self.assertRaises(SchemaError) as cm:
            regex({}, name="test")
        show(cm)

        with self.assertRaises(SchemaError) as cm:
            schema = regex
            object = "a"
            validate(schema, object)
        show(cm)

        ip_address = regex(r"(?:[\d]+\.){3}(?:[\d]+)", name="ip_address")
        schema = {"ip": ip_address}
        object = {"ip": "123.123.123.123"}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123.123"}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123.123.abc"}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123..123"}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123.123.123.123"}
            validate(schema, object)
        show(mc)

        object = {"ip": "123.123.123.1000000"}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": ""}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = regex(".")
            object = "\n"
            validate(schema, object)
        show(mc)

        schema = regex(".", flags=re.DOTALL)
        object = "\n"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            schema = regex(".", flags=re.ASCII | re.MULTILINE)
            object = "\n"
            validate(schema, object)
        show(mc)

    def test_interval(self):
        with self.assertRaises(SchemaError) as mc:
            schema = interval
            object = "a"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = interval(1, 10)
            object = "a"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = interval(1, 9)
            object = "a"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = -1
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = 10
            validate(schema, object)
        show(mc)

        object = 5
        validate(schema, object)

        schema = interval(0, ...)
        object = 5
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = -1
            validate(schema, object)
        show(mc)

        schema = interval(..., 0)
        object = -5
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = 1
            validate(schema, object)
        show(mc)

        schema = interval(..., ...)
        object = "0"
        validate(schema, object)

        with self.assertRaises(SchemaError) as cm:
            interval(0, "z")
        show(cm)

    def test_email(self):
        schema = email
        object = "user00@user00.com"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "user00@user00.user00"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "@user00.user00"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = email(check_deliverability=True)
            object = "user@example.com"
            validate(schema, object)
        show(mc)

        object = "user@google.com"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "user@ffdfsdfsdfsasddasdadasad.com"
            validate(schema, object)
        show(mc)

    def test_ip_address(self):
        schema = {"ip": ip_address}
        object = {"ip": "123.123.123.123"}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123.123"}
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "123.123.123.256"}
            validate(schema, object)
        show(mc)

        object = {"ip": "2001:db8:3333:4444:5555:6666:7777:8888"}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"ip": "2001:db8:3333:4444:5555:6666:7777:"}
            validate(schema, object)
        show(mc)

    def test_url(self):
        schema = {"url": url}
        object = {"url": "https://google.com"}
        validate(schema, object)

        object = {"url": "https://google.com?search=chatgpt"}
        validate(schema, object)

        object = {"url": "https://user:pass@google.com?search=chatgpt"}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"url": "google.com"}
            validate(schema, object)
        show(mc)

    def test_domain_name(self):
        schema = domain_name
        object = "www.example.com"
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "www.éxample.com"
            validate(schema, object)
        show(mc)

        schema = domain_name(ascii_only=False)
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = "-www.éxample.com"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            object = "www.é_xample.com"
            validate(schema, object)
        show(mc)

        with self.assertRaises(ValidationError) as mc:
            schema = domain_name(resolve=True)
            object = "www.exaaaaaaaaaaaaaaaaaaaaaaaaample.com"
            validate(schema, object)
        show(mc)

        object = "www.example.com"
        validate(schema, object)

    def test_number(self):
        schema = {"number": number}
        object = {"number": 1}
        validate(schema, object)

        object = {"number": 1.0}
        validate(schema, object)

        with self.assertRaises(ValidationError) as mc:
            object = {"number": "a"}
            validate(schema, object)
        show(mc)

    def test_truncation(self):
        with self.assertRaises(ValidationError) as mc:
            schema = "a"
            object = 1000 * "abc"
            validate(schema, object)
        show(mc)

        valid = str(mc.exception)

        self.assertTrue(r"...'" in valid)
        self.assertTrue("TRUNCATED" in valid)
        self.assertTrue(r"value:'" in valid)

        with self.assertRaises(ValidationError) as mc:
            object = 50 * "a"
            validate(schema, object)
        show(mc)

        valid = str(mc.exception)

        self.assertTrue(r"value:'" in valid)
        self.assertFalse("TRUNCATED" in valid)

        with self.assertRaises(ValidationError) as mc:
            object = 1000 * ["abcdefgh"]
            validate(schema, object)
        show(mc)

        valid = str(mc.exception)

        self.assertTrue(r"value:[" in valid)
        self.assertTrue(r"...]" in valid)
        self.assertTrue("TRUNCATED" in valid)

        with self.assertRaises(ValidationError) as mc:
            object = {}
            for i in range(1000):
                object[i] = 7 * i
            validate(schema, object)
        show(mc)

        valid = str(mc.exception)

        self.assertTrue(r"value:{" in valid)
        self.assertTrue("...}" in valid)
        self.assertTrue("TRUNCATED" in valid)

    def test_float_equal(self):
        with self.assertRaises(ValidationError) as mc:
            schema = 2.94
            object = 2.95
            validate(schema, object)
        show(mc)

        object = schema + 1e-10
        validate(schema, object)

    @unittest.skipUnless(
        sys.version_info.major == 3 and sys.version_info.minor >= 9,
        "Parametrized types were introduced in Python 3.9",
    )
    def test_type(self):
        with self.assertRaises(SchemaError) as cm:
            schema = list[str]
            object = ["a", "b"]
            validate(schema, object)
        show(cm)

    def test_callable(self):
        def even(x):
            return x % 2 == 0

        with self.assertRaises(ValidationError) as mc:
            schema = even
            object = 1
            validate(schema, object)
        show(mc)

        object = 2
        validate(schema, object)

        def fails(x):
            return 1 / x == 0

        with self.assertRaises(ValidationError) as mc:
            schema = fails
            object = 0
            validate(schema, object)
        show(mc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
