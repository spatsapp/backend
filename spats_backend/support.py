"""Some support classes and methods for the backend"""


class TupleNoneCompare:
    """Compare Class than can be None or a valid tuple"""

    def __init__(self, x):
        self.x = x

    @staticmethod
    def _not_same(x, y):
        return (
            (x is None and y is not None)
            or (x is not None and y is None)
            or (not isinstance(x, type(y)))
        )

    def __len__(self):
        return len(self.x)

    def __getitem__(self, y):
        return self.x[y]

    def __lt__(self, y):
        x = self.x
        len_x = len(x)
        len_y = len(y)
        for i in range(max(len_x, len_y)):
            # pylint: disable=too-many-boolean-expressions
            if (
                self._not_same(x[i], y[i])
                or (len_x > i and len_y == i)
                or ((x[i] is not None or y[i] is not None) and (x[i] > y[i]))
            ):
                return False
            if (len_x == i and len_y > i) or (
                (x[i] is not None or y[i] is not None) and (x[i] < y[i])
            ):
                return True
        return False

    def __le__(self, y):
        return self.__lt__(y) or self.__eq__(y)

    def __eq__(self, y):
        x = self.x
        if (
            (len(x) != len(y))
            or self._not_same(x[0], y[0])
            or (x[0] != y[0])
            or self._not_same(x[1], y[1])
            or (x[1] != y[1])
        ):
            return False
        len_x = len(x)
        for i in range(2, len_x):
            if self._not_same(x[i], y[i]) or (x[i] != y[i]):
                return False
        return True

    def __ne__(self, y):
        return not self.__eq__(y)

    def __gt__(self, y):
        return not self.__lt__(y)

    def __ge__(self, y):
        return self.__gt__(y) or self.__eq__(y)


def from_keys(dict_, keys):
    for key in keys:
        if key in dict_:
            return dict_[key]
    raise ValueError("No key in list exists in dictionary")


def jsonerror(error, document, **kwargs):
    if isinstance(error, Exception):
        msg = f"{error.__class__.__qualname__}: {error.message}"
    else:
        msg = str(error)
    doc = {
        "error": msg,
        "document": document,
    }
    for key, value in kwargs.items():
        doc[key] = value
    return doc


def json2list(json):
    if isinstance(json, dict):
        return [json] if json.keys() else []
    if isinstance(json, list):
        return json
    return []


def list2dict(key, json_list):
    res = {}
    for json in json2list(json_list):
        _id = json[key]
        del json[key]
        res[_id] = json
    return res
