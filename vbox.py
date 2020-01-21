import os

from contextlib import contextmanager
from misc import gb_to_byte_size
from misc import vboxapi_constant
from vboxapi import VirtualBoxManager


VIRTUAL_BOX_EXTENSION_PACK = "Oracle VM VirtualBox Extension Pack"


class VirtualBoxImporter:
    DEFAULT_MACHINE_NAME = "Hack OS"
    DEFAULT_HDD_SIZE = gb_to_byte_size(60)
    DEFAULT_RAM_SIZE = 3072
    DEFAULT_VRAM_SIZE = 128

    def __init__(self, logger, image_path, name=None):
        self.logger = logger
        self._manager = VirtualBoxManager(None, None)
        self._vbox = self._manager.getVirtualBox()
        self._extension_pack_manager = self._vbox.extensionPackManager

        self._session = self._manager.mgr.getSessionObject(self._vbox)
        self._name = name or self.DEFAULT_MACHINE_NAME
        self._image_path = image_path

    def run(self, destroy_existing=True):
        if not self.check_valid_image():
            self.logger.info("Image file at '%s' invalid or does not exist.",
                             self.image_path)
            return

        machine = self.find_machine()
        if machine is not None:
            self.logger.info("Machine '%s' with name '%s' already exists.",
                             machine.id, self.name)
            if destroy_existing:
                self.logger.info("Removing existing machine with name '%s'",
                                 self.name)
                self.remove_machine(machine)

        self.logger.info("Creating new machine with name '%s'", self.name)

        machine = self.create_machine()
        machine.memorySize = self.DEFAULT_RAM_SIZE

        machine.graphicsAdapter.VRAMSize = self.DEFAULT_VRAM_SIZE
        machine.graphicsAdapter.accelerate3DEnabled = True
        machine.graphicsAdapter.accelerate2DVideoEnabled = True

        machine.audioAdapter.enabled = True
        machine.audioAdapter.enabledIn = True
        machine.audioAdapter.enabledOut = True

        machine.BIOSSettings.IOAPICEnabled = True

        machine.clipboardMode = vboxapi_constant("ClipboardMode", "Bidirectional")
        machine.pointingHIDType = vboxapi_constant("PointingHIDType", "USBTablet")
        machine.RTCUseUTC = True

        medium = self.prepare_hack_medium()
        storage_controller = self.add_storage_controller(machine)

        ext_pack_names = [e.name for e in self._extension_pack_manager.installedExtPacks]
        if VIRTUAL_BOX_EXTENSION_PACK in ext_pack_names:
            self.add_usb_controller(machine)
        else:
            self.logger.warning("USB 3.0 support not enabled. Install extension pack '%s'",
                                VIRTUAL_BOX_EXTENSION_PACK)

        self.register_machine(machine)
        self.attach_device(machine, storage_controller, medium)

    def create_machine(self):
        try:
            machine = self._vbox.CreateMachine("", self.name, [], "Linux_64", "")
        except Exception as ex:
            self.logger.debug(ex)
            return None
        return machine

    def register_machine(self, machine):
        self._vbox.RegisterMachine(machine)

    def remove_machine(self, machine):
        full = vboxapi_constant("CleanupMode", "Full")
        mediums = machine.Unregister(full)
        machine.DeleteConfig(mediums)

    def find_machine(self):
        try:
            machine = self._vbox.FindMachine(self.name)
        except Exception as ex:
            self.logger.debug(ex)
            return None
        return machine

    def prepare_hack_medium(self):
        device_type = vboxapi_constant("DeviceType", "HardDisk")
        access_mode = vboxapi_constant("AccessMode", "ReadWrite")
        medium = self._vbox.OpenMedium(self.image_path, device_type, access_mode, False)
        medium.resize(self.DEFAULT_HDD_SIZE)
        return medium

    def add_storage_controller(self, machine):
        sata = vboxapi_constant("StorageBus", "SATA")
        controller = machine.AddStorageController("SATA Controller", sata)

        controller_type = vboxapi_constant("StorageControllerType", "IntelAhci") 
        controller.controllerType = controller_type

        return controller

    def add_usb_controller(self, machine):
        usb_xhci = vboxapi_constant("USBControllerType", "XHCI")
        controller = machine.addUSBController("USB Controller", usb_xhci)
        return controller

    def attach_device(self, machine, controller, medium):
        IDE_port = 0
        master_device = 0
        device_type = vboxapi_constant("DeviceType", "HardDisk")
        with self.acquire_machine(machine) as session_machine:
            session_machine.AttachDevice(controller.name, IDE_port, master_device,
                                         device_type, medium)

    def check_valid_image(self):
        return self.image_path.endswith(".vdi") and os.path.exists(self.image_path)

    @contextmanager
    def acquire_machine(self, machine, save_settings=True):
        machine.LockMachine(self._session, vboxapi_constant("LockType", "Write"))
        try:
            yield self._session.machine
        finally:
            if save_settings:
                self._session.machine.SaveSettings()
            self._session.UnlockMachine()

    @property
    def name(self):
        return self._name

    @property
    def image_path(self):
        return self._image_path
