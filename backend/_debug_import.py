import traceback
try:
    import run
    print('IMPORT_OK')
except BaseException:
    traceback.print_exc()
