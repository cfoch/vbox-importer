import argparse
import os
import sys
import logging

from misc import check_virtual_box_installed
from vbox import VirtualBoxImporter

DEFAULT_LOG_LEVEL = logging.DEBUG


def get_log_level():
    level = os.environ.get('EOS_VBOX_IMPORTER_LOGLEVEL')
    if not level:
        return DEFAULT_LOG_LEVEL
    try:
        level = int(level)
    except ValueError:
        level = logging.__dict__.get(level)
    if isinstance(level, int):
        return level
    return DEFAULT_LOG_LEVEL


logger = logging.getLogger(__name__)
logging.basicConfig()
level = get_log_level()
logger.setLevel(level)


if __name__ == "__main__":
    if not check_virtual_box_installed():
        logger.error("VirtualBox is not installed.")
        sys.exit(1)

    try:
        import vboxapi
    except ImportError:
        logger.error("vboxapi is not installed.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Import an EOS disk image into VirtualBox as a VM with '
                    'appropriate system configuration.')
    parser.add_argument('--image-path', type=str,
                        help='Path to the image file to import (.vdi)')
    parser.add_argument('--machine-name', type=str, default=None,
                        help='Name of the virtual machine.')
    args = parser.parse_args()

    importer = VirtualBoxImporter(logger, args.image_path, args.machine_name)
    importer.run()
