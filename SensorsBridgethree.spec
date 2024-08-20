# -*- mode: python -*-

block_cipher = None


a = Analysis(['main_v3.py'],
             pathex=['C:\\temp\\sensors_bridge_send_data_test\\send_data_tk_compile\\'],
             binaries=[],
             datas=[('favicon.ico', ',')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='SensorsBridgePortable_v1.0.3',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='favicon.ico')
