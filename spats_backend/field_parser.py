"""Form Field parser"""
import math
from collections import namedtuple
from datetime import MAXYEAR, MINYEAR, datetime

from .suid import Suid


class Error(Exception):
    """Base class for module exceptions"""

    def __init__(self, message):
        super().__init__()
        self.message = message


class BooleanNameError(Error):
    """Boolean value passed in not in valid"""


class InvalidDecimalError(Error):
    """Number passed is invalid decimal number"""


class InvalidLengthError(Error):
    """String value not within length bounds"""


class InvalidSuidError(Error):
    """Suid is invalid"""


class OutOfBoundsError(Error):
    """Number not within bounds"""


class UnknownFieldError(Error):
    """Field type not recognized"""


Decimal = namedtuple("Decimal", ("whole", "fraction"))


class FieldParser:
    """Form field parser"""

    def __init__(self):
        self.truthy = ["t", "true"]
        self.falsey = ["f", "false"]
        self.list_types = [
            "boolean",
            "string",
            "integer",
            "decimal",
            "date",
            "reference",
        ]
        self.suid = Suid()

    def parse(self, field, value, params):
        """Parse filed and get back dict"""
        return_value = None
        if field == "boolean":
            return_value = self.boolean_field(value, params)
        elif field == "string":
            return_value = self.string_field(value, params)
        elif field == "integer":
            return_value = self.integer_field(value, params)
        elif field == "decimal":
            return_value = self.decimal_field(value, params)
        elif field == "date":
            return_value = self.date_field(value, params)
        elif field == "list":
            return_value = self.list_field(value, params)
        elif field == "reference":
            return_value = self.reference_field(value, params)
        else:
            raise UnknownFieldError(f'Field type of "{field}" is undefined')
        return return_value

    def decode(self, field, value, params):
        """Convert value from form value to python value"""
        return_value = None
        if field in ["boolean", "string", "integer", "reference"]:
            return_value = value
        elif field == "decimal":
            if not isinstance(value, dict):
                value = self.decimal_field(value, params)
            precision = int(params.get("precision", 0))
            whole = str(value["whole"])
            fraction = str(value["fraction"])
            if precision is not None and len(fraction) != precision:
                fraction = fraction.ljust(precision, "0")[:precision]
            if fraction.startswith("-"):
                fraction = fraction[1:]
            return_value = f"{whole}.{fraction}"
        elif field == "date":
            if not isinstance(value, datetime):
                value = self.date_field(value, params)
            date_format = params.get("date_format", "%Y-%m-%d")
            return_value = datetime.strftime(value, date_format)
        elif field == "list":
            list_type = params.get("list_type", "string")
            ordered = params.get("ordered", False)
            decoded_list = [self.decode(list_type, v, params) for v in value]
            if ordered:
                decoded_list.sort()
            return_value = decoded_list
        else:
            raise UnknownFieldError(f'Field type of "{field}" is undefined')
        return return_value

    def boolean_field(self, value, _):
        """Verify boolean field"""
        value = str(value).lower()
        if value not in self.truthy or value not in self.falsey:
            raise BooleanNameError(
                (
                    "Boolean is not of right type. "
                    f'"{value}" needs to be one of the following: '
                    f"{self.truthy} or {self.falsey}"
                )
            )
        return value in self.truthy

    @staticmethod
    def string_field(value, params):
        """Verify string field"""
        str_value = str(value)
        min_length = params.get("min_length")
        max_length = params.get("max_length")
        if (min_length is not None and (len(str_value) < min_length)) or (
            max_length is not None and len(str_value) > max_length
        ):
            raise InvalidLengthError(
                f'"{value}" does is either under {min_length} or over {max_length}'
            )
        return str_value

    @staticmethod
    def integer_field(value, params):
        """Verify integer field"""
        new_value = int(value)
        min_value = params.get("min_value", -math.inf)
        max_value = params.get("max_value", math.inf)
        if not min_value <= new_value <= max_value:
            raise OutOfBoundsError(
                f'"{value}" does not fall into required range of {min_value} and {max_value}'
            )
        return new_value

    @staticmethod
    def _split_decimal(decimal, precision=None):
        str_value = str(decimal)
        point = str_value.count(".")
        whole = "0"
        fraction = "0"
        if point == 1:
            whole, fraction = str_value.split(".")
        elif point == 0:
            whole = str_value
        else:
            raise InvalidDecimalError(
                f'Decimal value "{str_value}" has too many decimal points'
            )
        if precision is not None and len(fraction) != precision:
            precision = int(precision)
            fraction = fraction.ljust((precision), "0")[:precision]
        if whole.startswith("-"):
            fraction = "-" + fraction
        return {"whole": int(whole), "fraction": int(fraction)}

    def decimal_field(self, value, params):
        """Verify decimal field"""
        str_value = str(value)
        precision = params.get("precision")

        new_dic = self._split_decimal(str_value, precision)
        new_value = Decimal(**new_dic)

        param_min = params.get("min_value")
        min_dic = (
            self._split_decimal(param_min, precision)
            if param_min is not None
            else {"whole": -math.inf, "fraction": -math.inf}
        )
        min_value = Decimal(**min_dic)

        param_max = params.get("max_value")
        max_dic = (
            self._split_decimal(param_max, precision)
            if param_max is not None
            else {"whole": math.inf, "fraction": math.inf}
        )
        max_value = Decimal(**max_dic)

        if not min_value <= new_value <= max_value:
            raise OutOfBoundsError(
                f'"{value}" does not fall into required range of {min_value} and {max_value}'
            )
        return {"whole": new_value.whole, "fraction": new_value.fraction}

    @staticmethod
    def date_field(value, params):
        """Verify date field"""
        date_format = params.get("date_format", "%Y-%m-%d")
        date_value = datetime.strptime(str(value), date_format)
        min_value = params.get("min_value", datetime(MINYEAR, 1, 1))
        max_value = params.get("max_value", datetime(MAXYEAR, 12, 31))
        if not min_value <= date_value <= max_value:
            raise OutOfBoundsError(
                f'"{value}" does not fall into required range of {min_value} and {max_value}'
            )
        return date_value

    def list_field(self, value, params):
        """Verify list field"""
        list_type = params.get("list_type", "string")
        ordered = params.get("ordered", False)
        if not isinstance(value, list):
            value = [value]
        values = [self.parse(list_type, val, params) for val in value]
        if ordered:
            values.sort()
        return values

    def reference_field(self, value, _):
        """Verify reference field"""
        str_value = str(value)
        if not self.suid.validate(str_value):
            raise InvalidSuidError(f"{value} is not a valid suuid")
        return str_value


if __name__ == "__main__":
    field_parser = FieldParser()
