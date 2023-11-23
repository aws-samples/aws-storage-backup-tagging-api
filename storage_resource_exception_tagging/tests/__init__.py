"""
base init file
"""
# pylint:disable=wrong-import-position,wrong-import-order, import-error, W0703
import logging
from entconfig import entconfigmgr

# sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../app')))
try:
    _config_mgr = entconfigmgr.get_ent_config_mgr()
    config = _config_mgr.get_app_config('resource-tagging')
    shared_config = _config_mgr.get_shared_config()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
except Exception as err:
    print(f'{type(err).__name__}: {err}')