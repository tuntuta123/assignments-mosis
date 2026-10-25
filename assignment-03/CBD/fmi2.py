"""Minimal Co-simulation FMI 2.0 loader.

The FMU is a zip file. This module unpacks it, reads modelDescription.xml
for the GUID and the value references, and calls the C API in the platform
binary through ctypes.
"""

import ctypes # to call the C API in the platform binary
import platform # to pick the binaries/ directory for this operating system
import tempfile # to hold the unzipped FMU
import xml.etree.ElementTree as ET # to read modelDescription.xml.
import zipfile # to unpack the .fmu archive
from pathlib import Path


# fmi2Status value for a successful call.
FMI2_OK = 0
# fmi2Status value for a call that succeeded with a warning.
FMI2_WARNING = 1
# fmi2Type value that selects co-simulation rather than model exchange.
FMI2_COSIMULATION = 1

# C type of the logger callback. The FMU calls it; this loader ignores it.
_LOGGER = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p
)
# C type of the allocateMemory callback: count and size in, pointer out.
_ALLOCATE = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t)
# C type of the freeMemory callback.
_FREE = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
# C type of the stepFinished callback. This loader does not use asynchronous steps.
_STEP_FINISHED = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int)

class _CallbackFunctions(ctypes.Structure):
    # Field order must match the struct in the FMI 2.0 header.
    _fields_ = [
        ("logger", _LOGGER),
        ("allocateMemory", _ALLOCATE),
        ("freeMemory", _FREE),
        ("stepFinished", _STEP_FINISHED),
        ("componentEnvironment", ctypes.c_void_p),
    ]


# Return the binaries/ directory name and the shared-library suffix for this OS.
def _platform_dir():
    # platform.system() is "Linux", "Windows", or "Darwin".
    system = platform.system()
    # Linux FMUs ship a .so under binaries/linux64.
    if system == "Linux":
        return "linux64", ".so"
    # Windows FMUs ship a .dll under binaries/win64.
    if system == "Windows":
        return "win64", ".dll"
    # macOS FMUs ship a .dylib under binaries/darwin64.
    if system == "Darwin":
        return "darwin64", ".dylib"
    # Any other OS has no layout this loader knows.
    raise OSError("No FMI binary layout for platform %s." % system)


class FMU2CoSimulation:
    """One loaded co-simulation FMU with a scalar input and a scalar output."""

    def __init__(self, fmu_path):
        # Keep the path of the .fmu zip.
        self.fmu_path = Path(fmu_path)
        # Create a temporary directory that will hold the unpacked archive.
        self._tmpdir = tempfile.TemporaryDirectory(prefix="fmu_")
        # Root of that directory.
        self._root = Path(self._tmpdir.name)
        # Open the FMU and extract every file into the temporary directory.
        with zipfile.ZipFile(str(self.fmu_path)) as archive:
            archive.extractall(str(self._root))
        # Parse modelDescription.xml. The root element is fmiModelDescription.
        description = ET.parse(str(self._root / "modelDescription.xml")).getroot()
        # The GUID must be passed unchanged to fmi2Instantiate.
        self.guid = description.get("guid")
        # modelIdentifier is the file name of the shared library, without the suffix.
        self.model_identifier = description.find("CoSimulation").get("modelIdentifier")
        # Map each ScalarVariable name to the integer used by setReal and getReal.
        self.value_references = {}
        for variable in description.iter("ScalarVariable"):
            self.value_references[variable.get("name")] = int(variable.get("valueReference"))
        # fmi2Component pointer. None until instantiate succeeds.
        self._component = None
        # Loaded shared library. None until instantiate succeeds.
        self._library = None
        # Callback struct kept alive for the C library.
        self._callbacks = None

    def binary_path(self):
        # Directory name and suffix for this operating system.
        directory, suffix = _platform_dir()
        # binaries/<platform>/<modelIdentifier>.so (or .dll / .dylib).
        path = self._root / "binaries" / directory / (self.model_identifier + suffix)
        # A model-exchange-only FMU, or the wrong platform, has no file here.
        if not path.is_file():
            raise FileNotFoundError("FMU has no binary at %s." % path)
        return path

    def instantiate(self):
        # A second call must not instantiate a second FMU.
        if self._component is not None:
            return
        # calloc and free come from the C library. Windows uses the C runtime DLL.
        libc = ctypes.CDLL("libc.so.6" if platform.system() != "Windows" else "msvcrt.dll")
        # calloc returns a pointer.
        libc.calloc.restype = ctypes.c_void_p
        # calloc takes a count and a size in bytes.
        libc.calloc.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        # free takes the pointer calloc returned.
        libc.free.argtypes = [ctypes.c_void_p]
        # The callbacks must stay referenced: ctypes does not keep them alive.
        self._keep = (
            # Logger: discard every message.
            _LOGGER(lambda *args: None),
            # allocateMemory: the FMU's own heap, backed by calloc.
            _ALLOCATE(lambda count, size: libc.calloc(count, size)),
            # freeMemory: release a block from that heap.
            _FREE(lambda pointer: libc.free(pointer)),
        )
        # Fill the callback struct. stepFinished is unused, so it is a null function pointer.
        self._callbacks = _CallbackFunctions(
            self._keep[0], self._keep[1], self._keep[2], ctypes.cast(None, _STEP_FINISHED), None
        )
        # Load the platform binary extracted from the FMU.
        self._library = ctypes.CDLL(str(self.binary_path()))
        library = self._library
        # fmi2Instantiate returns the component pointer.
        library.fmi2Instantiate.restype = ctypes.c_void_p
        # instance name, fmi2Type, GUID, resource location, callbacks, visible, loggingOn.
        library.fmi2Instantiate.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(_CallbackFunctions),
            ctypes.c_int,
            ctypes.c_int,
        ]
        # component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime.
        library.fmi2SetupExperiment.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_int,
            ctypes.c_double,
        ]
        # Enter initialization: one component pointer.
        library.fmi2EnterInitializationMode.argtypes = [ctypes.c_void_p]
        # Leave initialization: one component pointer.
        library.fmi2ExitInitializationMode.argtypes = [ctypes.c_void_p]
        # component, value references, count, values to write.
        library.fmi2SetReal.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
        ]
        # component, value references, count, array the FMU fills.
        library.fmi2GetReal.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_double),
        ]
        # component, current communication time, step size, noSetFMUStatePriorToCurrentPoint.
        library.fmi2DoStep.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_int]
        # Terminate the co-simulation.
        library.fmi2Terminate.argtypes = [ctypes.c_void_p]
        # Release the component.
        library.fmi2FreeInstance.argtypes = [ctypes.c_void_p]
        # Resource path as a file URL. The FMU reads tables and such from here.
        resources = "file://" + str(self._root / "resources")
        # Create the component. visible=0 and loggingOn=0.
        self._component = library.fmi2Instantiate(
            b"plant",
            FMI2_COSIMULATION,
            self.guid.encode(),
            resources.encode(),
            ctypes.byref(self._callbacks),
            0,
            0,
        )
        # A null pointer means the GUID, the binary, or the callbacks were rejected.
        if not self._component:
            raise RuntimeError("fmi2Instantiate returned no component for %s." % self.fmu_path)

    def setup(self, start=0.0, stop=None):
        # Instantiate first if the caller has not done it.
        self.instantiate()
        # No stop time: stopTimeDefined is 0 and the stop value is ignored.
        if stop is None:
            status = self._library.fmi2SetupExperiment(self._component, 0, 0.0, start, 0, 0.0)
        # A stop time is defined, so the last flag is 1.
        else:
            status = self._library.fmi2SetupExperiment(self._component, 0, 0.0, start, 1, float(stop))
        # Reject any status other than ok or warning.
        self._check(status, "fmi2SetupExperiment")
        # Initialization mode is where start values may be set. This plant needs none.
        self._check(self._library.fmi2EnterInitializationMode(self._component), "fmi2EnterInitializationMode")
        # After this call the FMU accepts doStep.
        self._check(self._library.fmi2ExitInitializationMode(self._component), "fmi2ExitInitializationMode")

    def set_real(self, value_reference, value):
        # One value reference, as an array of length 1. The pointer must outlive the call.
        reference = (ctypes.c_uint * 1)(int(value_reference))
        # The value to write, also an array of length 1.
        values = (ctypes.c_double * 1)(float(value))
        # nvr is 1: one reference and one value.
        self._check(
            self._library.fmi2SetReal(self._component, reference, 1, values),
            "fmi2SetReal",
        )

    def get_real(self, value_reference):
        # Which variable to read.
        reference = (ctypes.c_uint * 1)(int(value_reference))
        # Empty array the FMU writes into.
        values = (ctypes.c_double * 1)()
        self._check(
            self._library.fmi2GetReal(self._component, reference, 1, values),
            "fmi2GetReal",
        )
        # The single double the FMU stored.
        return values[0]

    def do_step(self, time, step):
        # Advance the FMU from time by step. The last 1 means no earlier state must be kept.
        self._check(
            self._library.fmi2DoStep(self._component, float(time), float(step), 1),
            "fmi2DoStep",
        )

    def terminate(self):
        # Nothing to terminate if instantiate never ran, or free already ran.
        if self._component is not None and self._library is not None:
            self._library.fmi2Terminate(self._component)

    def free(self):
        # Free the C component before dropping the library handle.
        if self._component is not None and self._library is not None:
            self._library.fmi2FreeInstance(self._component)
        # Forget the component so a later call does not free it twice.
        self._component = None
        # Drop the library handle.
        self._library = None
        # Delete the unpacked FMU. TemporaryDirectory.cleanup removes the directory.
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None

    def _check(self, status, name):
        # ok and warning are both accepted. Anything else, including discard and error, stops the run.
        if status not in (FMI2_OK, FMI2_WARNING):
            raise RuntimeError("%s failed with status %s." % (name, status))
