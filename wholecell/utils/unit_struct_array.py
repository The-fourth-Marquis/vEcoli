"""
UnitStructArray

Wraps Numpy struct arrays using Unum units. Will assure that correct units are
being used while loading constants.

TODO: Unum is a defunct project. Its source repo is no longer online. Either
switch to a newer package like Pint or copy and improve the Unum source code
from its Python package.
"""

import numpy as np
import numpy.typing as npt
import unum
from typing import Optional

from wholecell.utils import units as units_pkg


class UnitStructArray(object):
    """Wraps Numpy structured arrays using Unum units. Will assure that correct
    units are being used while loading constants.
    """

    def __init__(
        self, struct_array: npt.NDArray, units: dict[str, Optional[unum.Unum]]
    ):
        self._validate(struct_array, units)

        self.struct_array = struct_array
        self.units = units

    def _validate(self, struct_array, units):
        s = ""
        if not isinstance(struct_array, np.ndarray):
            s += "UnitStructArray must be initialized with a numpy array!\n"
        elif not isinstance(units, dict):
            s += "UnitStructArray must be initialized with a dict storing units!\n"
        elif set([x[0] for x in struct_array.dtype.descr]) != set(units.keys()):
            s += "Struct array fields do not match unit fields!\n"
        if len(s):
            raise Exception(s)

    def _field(self, fieldname):
        if not units_pkg.hasUnit(self.units[fieldname]):
            if self.units[fieldname] is None:
                return self.struct_array[fieldname]
            else:
                raise Exception("Field has incorrect units or unitless designation!\n")
        else:
            return self.units[fieldname] * self.struct_array[fieldname]

    def fullArray(self):
        return self.struct_array

    def fullUnits(self):
        return self.units

    def __getitem__(self, key):
        if isinstance(key, slice):
            return UnitStructArray(self.struct_array[key], self.units)
        elif isinstance(key, np.ndarray) or isinstance(key, list):
            return UnitStructArray(self.struct_array[key], self.units)
        elif isinstance(key, int):
            return self.struct_array[key]
        else:
            return self._field(key)

    def __setitem__(self, key, value):
        if units_pkg.hasUnit(value):
            try:
                self.units[key].matchUnits(value)
            except unum.IncompatibleUnitsError:
                raise Exception("Units do not match!\n")

            self.struct_array[key] = value.asNumber()
            self.units[key] = units_pkg.getUnit(value)

        elif isinstance(value, list) or isinstance(value, np.ndarray):
            if units_pkg.hasUnit(self.units[key]):
                raise Exception(
                    "Units do not match! Quantity has units your input does not!\n"
                )
            self.struct_array[key] = value
            self.units[key] = None

        else:
            raise Exception(
                "Can't assign data-type other than unum datatype or list/numpy array!\n"
            )

    def __len__(self):
        return len(self.struct_array)

    def __repr__(self):
        return "STRUCTURED ARRAY:\n{}\nUNITS:\n{}".format(
            self.struct_array.__repr__(), self.units
        )

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        elif self.struct_array.dtype != other.struct_array.dtype:
            return False
        elif not all(self.struct_array == other.struct_array):
            return False
        elif self.units != other.units:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)
