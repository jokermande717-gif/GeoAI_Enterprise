# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('app_icon.ico', '.'), ('src', 'src')]
binaries = []
hiddenimports = [
    'src', 'src.ai', 'src.core', 'src.gis', 'src.gui',
    'src.ai.lidar_engine', 'src.ai.feature_extractor',
    'src.core.geodesy_engine', 'src.core.bundeslaender',
    'src.core.okstra_engine', 'src.core.sustainability',
    'src.core.file_exporter', 'src.gis.basemap_layers',
    'src.gui.main_window'
]

tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['app_launcher.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GeoAI_Overlord_2026_Setup',
    debug=False,
    console=False,
    icon='app_icon.ico',
)
