import datetime
import os
import re
from typing import List, Optional


STEAMAPP_EXLUSIONS = [
    'unins.*',
    'UnityCrashHandler.*',
    'EasyAntiCheat.*',
    'crashmsg',
    'dxsetup',
    'directx.*',
    'vcredist.*',
    'bspzip',
    'hammer',
    'height2normal',
    'height2ssbump',
    'hlfaceposer',
    'shadercompile',
    'splitskybox',
    'CrashSender.*',
    'RemoteCrashSender.*',
    'addoninstaller',
    'capture',
    'hook-helper.*',
    'LIV\.App.*',
    'idevice\w+',
    'idevice_id',
    'ios_webskit_debug_proxy',
    'iproxy',
    'irecovery',
    'plist.+',
    'Updater',
    'D3D.+',
    'msedgewebview.*',
    'notification_helper',
    'vbsp',
    'vpk',
    'vrad',
    'vtex',
    'vtfdiff',
    'vtfscrew',
    'vvis',
    'SymbolStoreUpdate',
    'ShaderAPITest',
    'mksheet',
    'motionmapper',
    'normal2ssbump',
    'slices2volumetex',
    'ohworkshopuploader',
    'pfm2tgas',
    'QC_Eyes',
    'captioncompiler',
    'demoinfo',
    'dmxconvert',
    'dmxedit',
    'elementviewer',
    'glview',
    'IPA',
    'ActivationUI',
    'Cleanup',
    'Touchup',
    'overlayinjector',
    'QuickEditDisable',
    'resourcecompiler',
    'steamutil.*',
    'ui32',
    'mod_uploader',
    'asset_packer',
    'asset_unpacker',
    'apputil.*',
    'diagnostics.*',
    '.*server',
    '.*launcher',
    '.*setup',
    '.*launch',
    '.*installer',
    '.*install',
    'dump_versioned_json',
    'make_versioned_json',
    'start_protected_game',
    'DumpTool',
    '.*WebHelper',
    'wallpaperservice.*',
    'applicationwallpaperinject.*',
    'webwallpaper.*',
    'Steam360VideoPlayer',
    'dotNet.*',
    'planet_mapgen',
    'steam',
    'steamwebhelper'
]

def re_check_list(s: str, expr_list: List[str]):
    for expr in expr_list:
        if re.match(expr, s, re.IGNORECASE) is not None:
            return True
    return False

def find_steam_games(path: str, additional_exlusions: List[str]) -> List[str]:
    l = []
    p = os.path.join(path, 'steamapps', 'common')
    for root, _, files in os.walk(p):
        if root[len(p):].count(os.sep) < 3:
            for file in files:
                if file.endswith('.exe'):
                    file = file[:-4]
                    if not re_check_list(file, STEAMAPP_EXLUSIONS + additional_exlusions):
                        if file not in l:
                            l.append(file.lower())
    return l

def find_and_write_steamgames_cache(library_folders: List[str], file_name: str, additional_exlusions: List[str]):
    steam_games = []
    for folder in library_folders:
        steam_games.extend(find_steam_games(folder, additional_exlusions))
    with open(file_name, 'w') as file:
        dt = datetime.datetime.now().isoformat()
        file.write(dt + '\n' + '\n'.join(steam_games))
    return steam_games

def read_steamgames_cache(file_name: str, cache_expiration: int) -> Optional[List[str]]:
    with open(file_name, 'r') as file:
        s = file.read()
        steam_games = [ _s.lower() for _s in s.split('\n') if len(_s) > 1 ]
        dt = datetime.datetime.fromisoformat(steam_games[0])
        delta = datetime.datetime.now() - dt
        if delta.seconds > cache_expiration * 60:
            return None
        return steam_games[1:]