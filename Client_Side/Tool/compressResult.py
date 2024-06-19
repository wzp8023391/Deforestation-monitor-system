import zipfile

def compress_attaches(files, out_name):
    """
    compress raster and vector data
    files:         示例   ['a.txt', 'K.result.xlsx']
    out_name;      示例  '0731-test.zip'
    compress_attaches(files, '0731-test.zip') 
    """
    f = zipfile.ZipFile(out_name, 'w', zipfile.ZIP_DEFLATED)
    for file in files:
        f.write(file)
    f.close() 