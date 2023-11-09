# coding:utf-8
# Author:Mr Zhipan wang and Mr Zhongwu Wang, if you have any question, Email:1044625113@qq.com,Date:2022-8-2
import os
import onnxruntime
from osgeo import gdal, osr, ogr
import numpy as np
import cv2
from skimage import morphology as mp
from tqdm import tqdm



def imagexy2geo(dataset, row, col):

    trans = dataset.GetGeoTransform()
    px = trans[0] + col * trans[1] + row * trans[2]
    py = trans[3] + col * trans[4] + row * trans[5]
    return px, py


def geo2imagexy(dataset, x, y):

    trans = dataset.GetGeoTransform()
    dTemp = trans[1] * trans[5] - trans[2] * trans[4]
    dCol = (trans[5] * (x - trans[0]) -
            trans[2] * (y - trans[3])) / dTemp + 0.5
    dRow = (trans[1] * (y - trans[3]) -
            trans[4] * (x - trans[0])) / dTemp + 0.5

    iCol = int(dCol)
    iRow = int(dRow)
    return iCol, iRow


def get_xy(imgPath):

    dataset = gdal.Open(imgPath)
    col = dataset.RasterXSize
    row = dataset.RasterYSize
    ul = imagexy2geo(dataset, 0, 0)  
    lr = imagexy2geo(dataset, row, col)  

    return ul, lr


def getUion(imgCo_T1, imgCo_T2):

    x = np.array([imgCo_T1[0][0], imgCo_T1[1][0], imgCo_T2[0][0], imgCo_T2[1][0]])
    y = np.array([imgCo_T1[0][1], imgCo_T1[1][1], imgCo_T2[0][1], imgCo_T2[1][1]])

    x = sorted(x)  
    y = sorted(y)

    ulx = x[1]  
    uly = y[2]
    lrx = x[2]
    lry = y[1]


    return [ulx, uly], [lrx, lry]


def checkProject(imgPath_t1, imgPath_t2, reProjectImgPath_t2):
    
    if os.path.exists(reProjectImgPath_t2):
        os.remove(reProjectImgPath_t2)

    datasetT1 = gdal.Open(imgPath_t1)
    datasetT2 = gdal.Open(imgPath_t2)

    sr_T1 = datasetT1.GetProjection()
    sr_T2 = datasetT2.GetProjection()

    osrobj_T1 = osr.SpatialReference()
    osrobj_T2 = osr.SpatialReference()

    osrobj_T1.ImportFromWkt(sr_T1)
    osrobj_T2.ImportFromWkt(sr_T2)


    isSame = osrobj_T2.IsSame(osrobj_T1)


    if isSame == 0:  
        print("the spatial reference between temporal images is different...")
        ct = osr.CoordinateTransformation(osrobj_T2, osrobj_T1)  

        
        datatype = datasetT2.ReadAsArray(0, 0, 1, 1).dtype.name  
        if "int8" in datatype:
            datatype = gdal.GDT_Byte
        elif "int16" in datatype:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        src_width = datasetT2.RasterXSize
        src_height = datasetT2.RasterYSize
        src_count = datasetT2.RasterCount

        src_trans = datasetT2.GetGeoTransform()
        OriginLX_src = src_trans[0]
        OriginTY_src = src_trans[3]
        pixl_w_src = src_trans[1]
        pixl_h_src = src_trans[5]

        OriginRX_src = OriginLX_src + pixl_w_src * src_width
        OriginBY_src = OriginTY_src + pixl_h_src * src_height

        driver = gdal.GetDriverByName("GTiff")
        driver.Register()
        dst_data = driver.Create(reProjectImgPath_t2, src_width, src_height, src_count,
                                 datatype)


        OriginLX_dst, OriginTY_dst, temp = ct.TransformPoint(OriginLX_src, OriginTY_src)
        OriginRX_dst, OriginBY_dst, temp = ct.TransformPoint(OriginRX_src, OriginBY_src)

        pixl_w_dst = (OriginRX_dst - OriginLX_dst) / src_width
        pixl_h_dst = (OriginBY_dst - OriginTY_dst) / src_height
        dst_trans = [OriginLX_dst, pixl_w_dst, 0, OriginTY_dst, 0, pixl_h_dst]


        dstSRS_wkt = osrobj_T1.ExportToWkt()

        dst_data.SetGeoTransform(dst_trans)
        dst_data.SetProjection(dstSRS_wkt)

        gdal.ReprojectImage(datasetT2, dst_data, sr_T2, dstSRS_wkt, gdal.GRA_Bilinear,
                            WarpMemoryLimit=8192)  

        return reProjectImgPath_t2

    else:
        reProjectImgPath_t2 = imgPath_t2
        print("the spatial reference between bi-temporal images is the same...")
        return reProjectImgPath_t2
    
    
def isBackGround(data):

    band1 = data[:, :, 0]  
    mindata = band1.min()
    maxdata = band1.max()
    if maxdata == mindata:
        return 1
    else:
        return 0
    
    
def compositeImg(dataT1, dataT2):

    row, col, bandnum = dataT1.shape
    row2, col2, bandnum2 = dataT2.shape

    newdata = np.zeros((row, col, bandnum * 2))
    newdata[:, :, 0:bandnum] = dataT1

    if (row != row2) or (col != col2):  
        for i in range(0, bandnum):
            img = dataT2[:, :, i]
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            img = cv2.resize(img, (col, row), interpolation=cv2.INTER_CUBIC)
            newdata[:, :, i + bandnum] = img[:, :, 0]
    else:
        newdata[:, :, bandnum:bandnum2 + bandnum] = dataT2

    return newdata


def deleteBackground(shpName, backGroundValue):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    pFeatureDataset = driver.Open(shpName, 1)
    pFeaturelayer = pFeatureDataset.GetLayer(0)
    strValue = backGroundValue

    strFilter = "Value = '" + str(strValue) + "'"
    pFeaturelayer.SetAttributeFilter(strFilter)
    pFeatureDef = pFeaturelayer.GetLayerDefn()
    pLayerName = pFeaturelayer.GetName()
    pFieldName = "Value"
    pFieldIndex = pFeatureDef.GetFieldIndex(pFieldName)

    for pFeature in pFeaturelayer:
        pFeatureFID = pFeature.GetFID()
        pFeaturelayer.DeleteFeature(int(pFeatureFID))

    strSQL = "REPACK " + str(pFeaturelayer.GetName())
    pFeatureDataset.ExecuteSQL(strSQL, None, "")
    pFeatureLayer = None
    pFeatureDataset = None
    

def RasterToPoly(rasterName, shpName):

    inraster = gdal.Open(rasterName)  
    inband = inraster.GetRasterBand(1)  
    prj = osr.SpatialReference()
    prj.ImportFromWkt(inraster.GetProjection())  

    outshp = shpName
    drv = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(outshp): 
        drv.DeleteDataSource(outshp)
    Polygon = drv.CreateDataSource(outshp)  
    Poly_layer = Polygon.CreateLayer(
        shpName[:-4], srs=prj, geom_type=ogr.wkbMultiPolygon) 

    newField = ogr.FieldDefn('Value', ogr.OFTReal)
    Poly_layer.CreateField(newField)

    gdal.FPolygonize(inband, None, Poly_layer, 0) 
    Polygon.SyncToDisk()
    Polygon = None

    deleteBackground(shpName, 0)  
    

def sigmoid(x):
    
    s = 1 / (1 + np.exp(-x))
    return s


def softmax(x):
    
    x_exp = np.exp(x)
    x_sum = np.sum(x_exp, axis=1, keepdims=True)

    s = x_exp / x_sum
    return s


def backGroundMask(predict, imgData, numNodata=100000, nodataValue=0):

    bandnum, row, col = imgData.shape
    T1_Data = imgData[0, :, :]  
    T2_Data = imgData[int(bandnum / 2), :, :]

    index_T1 = T1_Data == nodataValue  
    index_T2 = T2_Data == nodataValue

    numT1_Nodata = (T1_Data[index_T1]).size
    numT2_Nodata = (T2_Data[index_T2]).size

    if (numT1_Nodata > numNodata) or (numT2_Nodata > numNodata): 
        if numT1_Nodata != 0:
            predict[index_T1] = 0
        if numT2_Nodata != 0:
            predict[index_T2] = 0

    return predict


def backGroundMask_Time2(predict, imgData, numNodata=100000, nodataValueT1=0, nodataValueT2=0):

    bandnum, row, col = imgData.shape
    T1_Data = imgData[0, :, :]  
    T2_Data = imgData[int(bandnum / 2), :, :]

    index_T1 = T1_Data == nodataValueT1 
    index_T2 = T2_Data == nodataValueT2

    numT1_Nodata = (T1_Data[index_T1]).size
    numT2_Nodata = (T2_Data[index_T2]).size

    if (numT1_Nodata > numNodata) or (numT2_Nodata > numNodata):  
        if numT1_Nodata != 0:
            predict[index_T1] = 0
        if numT2_Nodata != 0:
            predict[index_T2] = 0

    return predict


def smallAreaRemove_HoleFill(oriImg, areaopen=200):

    arr = oriImg

    cleaned = mp.remove_small_objects(arr, min_size=areaopen) 
    cleaned = mp.remove_small_holes(cleaned, area_threshold=areaopen)  

    return cleaned


def SieveFilterTheRaster(inputfile, area=200, connectedness=4, mask='none', format='GTiff'):
    src_ds = gdal.Open(inputfile, gdal.GA_Update)
    srcband = src_ds.GetRasterBand(1)
    dstband = srcband
    if mask is 'default':
        maskband = srcband.GetMaskBand()
    elif mask is 'none':
        maskband = None
    else:
        mask_ds = gdal.Open(mask)
        maskband = mask_ds.GetRasterBand(1)

    result = gdal.SieveFilter(srcband, maskband, dstband, area, connectedness)
    return result


def getBlockNum(row, col, blocksize):

    rowNum, RowResi = divmod(float(row), blocksize)
    colNum, ColResi = divmod(float(col), blocksize)

    if RowResi > 0:
        rowNum = rowNum + 1
    if ColResi > 0:
        colNum = colNum + 1

    numBlock = rowNum * colNum

    return numBlock


def normBlockImg(data, nodataValue=0):

    data = np.array(data).astype(np.float)
    bandNum, _, _ = data.shape

    for i in range(0, bandNum):
        tempData = data[i, :, :]
        calData = tempData[tempData != nodataValue]

        data[i, :, :] = (data[i, :, :] - np.mean(calData)) / np.std(calData)

    return data


def normBlockImg_Time2(data, nodataValueT1=0, nodataValueT2=0):
    data = np.array(data).astype(np.float)
    bandNum, _, _ = data.shape

    numBandT1 = int(bandNum / 2)

    for i in range(0, numBandT1):
        tempData = data[i, :, :]
        calData = tempData[tempData != nodataValueT1]

        data[i, :, :] = (data[i, :, :] - np.mean(calData)) / np.std(calData)

    for i in range(numBandT1, bandNum):
        tempData = data[i, :, :]
        calData = tempData[tempData != nodataValueT2]

        data[i, :, :] = (data[i, :, :] - np.mean(calData)) / np.std(calData)

    return data



def model_predict(onnx_session, data, blocksize, pad_width, nodata_T1, nodata_T2, area, pro, isUseVote=0):
    
    inputChannel, row, col = data.shape

    global imgy
    if (row == blocksize + 2 * pad_width) & (col == blocksize + 2 * pad_width):

        oridata = data  
        
        if nodata_T1 == nodata_T2:
            data = normBlockImg(
                data, nodataValue=nodata_T1)  
        else:
            data = normBlockImg_Time2(data, nodataValueT1=nodata_T1,
                                        nodataValueT2=nodata_T2)  

        if isUseVote == 0:

            data = np.array(data[np.newaxis, :]).astype(
                np.float32)  

            inputs = {onnx_session.get_inputs()[0].name: data}
            outs = onnx_session.run(None, inputs)[0]

            _, c, _, _ = outs.shape

            if c == 1:
                outs = sigmoid(outs)
                result = outs[:, 0, :, :]
            else:
                outs = softmax(outs)
                result = outs[:, 1, :, :]  
            imgy = np.squeeze(result)
 
            
            if nodata_T1 == nodata_T2:
                imgy = backGroundMask(
                    imgy, oridata, nodataValue=nodata_T1)
            else:
                imgy = backGroundMask_Time2(imgy, oridata, nodataValueT1=nodata_T1,
                                                nodataValueT2=nodata_T2)

            imgy = smallAreaRemove_HoleFill(
                imgy > pro, areaopen=area)  
            
            
            if np.max(imgy) != 255:
                    imgy = imgy * 255
            else:
                imgy = imgy

    else:
        oridata = np.zeros(
            (inputChannel, blocksize+2*pad_width, blocksize+2*pad_width))
        oridata[:, :row, :col] = data

        if nodata_T1 == nodata_T2:
            data = normBlockImg(
                oridata, nodataValue=nodata_T1) 
        else:
            data = normBlockImg_Time2(oridata, nodataValueT1=nodata_T1,
                                        nodataValueT2=nodata_T2)  

        if isUseVote == 0:

            data = np.array(data[np.newaxis, :]).astype(
                np.float32)  # B C H W

            inputs = {onnx_session.get_inputs()[0].name: data}
            outs = onnx_session.run(None, inputs)[0]

            _, c, _, _ = outs.shape

            if c == 1:
                outs = sigmoid(outs)
                result = outs[:, 0, :, :]
            else:
                outs = softmax(outs)
                result = outs[:, 1, :, :]  

            imgy_temp = np.squeeze(result) 
            
            if nodata_T1 == nodata_T2:
                imgy_temp = backGroundMask(
                    imgy_temp, oridata, nodataValue=nodata_T1)
            else:
                imgy_temp = backGroundMask_Time2(imgy_temp, oridata, nodataValueT1=nodata_T1,
                                                nodataValueT2=nodata_T2)

            imgy_temp = smallAreaRemove_HoleFill(
                imgy_temp > pro, areaopen=area)  
             
          
            if np.max(imgy_temp) != 255:
                    imgy_temp = imgy_temp * 255
            else:
                imgy_temp = imgy_temp
 
            imgy = imgy_temp[:row, :col]


    return imgy


def getUnionRaster(inputChannel, onnx_model_Path, imgPath_t1, imgPath_t2, saveRasterPath,
                   blocksize, area, isUseVote=0, pro=0.5, pad_width=128):
    """
    main function
    """
    try:
        resnet_session = onnxruntime.InferenceSession(onnx_model_Path, providers=['CUDAExecutionProvider']) 
        print("the model is excute on GPU device...")
    except:
        resnet_session = onnxruntime.InferenceSession(onnx_model_Path, providers=['CPUExecutionProvider'])  
        print("the model is excute on GPU device...")
        

    device = onnxruntime.get_device()
    if device == 'GPU':
        print("inference on gpu device...")
    else:
        print("inference on cpu device...")

    datasetT1 = gdal.Open(imgPath_t1)
    datasetT2 = gdal.Open(imgPath_t2)

    # get nodatavalue
    nodata_T1 = datasetT1.GetRasterBand(1).GetNoDataValue()
    nodata_T2 = datasetT2.GetRasterBand(1).GetNoDataValue()

    
    if (nodata_T1 == None) or (nodata_T1 == 256):
        nodata_T1 = 0

    if (nodata_T2 == None) or (nodata_T2 == 256):
        nodata_T2 = 0

    # get the overlap region
    ul, lr = get_xy(imgPath_t1)
    ul_t2, lr_t2 = get_xy(imgPath_t2)
    
    union_ul, union_lr = getUion([ul, lr], [ul_t2, lr_t2])

    print("get overlap area success...")


    if datasetT1.RasterCount != datasetT2.RasterCount:
        print("the band list of two image is different.")
    else:
        print("patch predict...")

        bandNum = datasetT1.RasterCount
        colT1_ul, rowT1_ul = geo2imagexy(
            datasetT1, union_ul[0], union_ul[1]) 
        colT1_lr, rowT1_lr = geo2imagexy(
            datasetT1, union_lr[0], union_lr[1])  

        Xsize_T1 = int(colT1_lr - colT1_ul)
        Ysize_T1 = int(rowT1_lr - rowT1_ul)

        projinfo = datasetT1.GetProjection()  

        base = os.path.basename(saveRasterPath)
        ext = os.path.splitext(base)[1]
        format = "GTiff"
        driver = gdal.GetDriverByName(format)

        if ext == '.img':
            format = "HFA"  
            driver = gdal.GetDriverByName(format)


        _, xr, northRotation, _, northRotation2, yr = datasetT1.GetGeoTransform()
        geotransform = union_ul[0], xr, northRotation, union_ul[1], northRotation2, yr
        
        dst_ds = driver.Create(saveRasterPath, Xsize_T1, Ysize_T1, 1,
                                gdal.GDT_Byte, options=["TILED=YES", "COMPRESS=LZW"]) 
        dst_ds.SetGeoTransform(geotransform)
        dst_ds.SetProjection(projinfo)


        numBlock = getBlockNum(Ysize_T1, Xsize_T1, blocksize)
        num = 0
        pbar = tqdm(total=numBlock)
        for x in range(colT1_ul, colT1_lr, blocksize):
            if x + blocksize < colT1_lr:
                cols = blocksize
            else:
                cols = colT1_lr - x
            for y in range(rowT1_ul, rowT1_lr, blocksize):
                if y + blocksize < rowT1_lr:
                    rows = blocksize
                else:
                    rows = rowT1_lr - y
                try:
                    if (blocksize <= x <= colT1_lr - blocksize) and (
                            blocksize <= y <= rowT1_lr - blocksize):  

                        if (x + blocksize + pad_width > colT1_lr) or (
                                y + blocksize + pad_width > rowT1_lr): 

                            geoT1_X = imagexy2geo(datasetT1, y, x)[0]
                            geoT1_Y = imagexy2geo(datasetT1, y, x)[1]
                           
                            x_T2, y_T2 = geo2imagexy(
                                datasetT2, geoT1_X, geoT1_Y)

                            geoT2_X = imagexy2geo(
                                datasetT1, y + rows, x + cols)[0]
                            geoT2_Y = imagexy2geo(
                                datasetT1, y + rows, x + cols)[1]
                            cols_T2, rows_T2 = geo2imagexy(datasetT2, geoT2_X,
                                                            geoT2_Y)  

                            c_T2 = cols_T2 - x_T2
                            r_T2 = rows_T2 - y_T2

                            dataT1 = datasetT1.ReadAsArray(
                                x, y, cols, rows) 
                            dataT2 = datasetT2.ReadAsArray(
                                x_T2, y_T2, c_T2, r_T2) 

                        else:
                            geoT1_X = imagexy2geo(
                                datasetT1, y - pad_width, x - pad_width)[0]
                            geoT1_Y = imagexy2geo(
                                datasetT1, y - pad_width, x - pad_width)[1]
                        
                            x_T2, y_T2 = geo2imagexy(
                                datasetT2, geoT1_X, geoT1_Y)

                            geoT2_X = imagexy2geo(
                                datasetT1, y + rows + pad_width, x + cols + pad_width)[0]
                            geoT2_Y = imagexy2geo(
                                datasetT1, y + rows + pad_width, x + cols + pad_width)[1]
                            cols_T2, rows_T2 = geo2imagexy(datasetT2, geoT2_X,
                                                            geoT2_Y) 

                            c_T2 = cols_T2 - x_T2
                            r_T2 = rows_T2 - y_T2

                            dataT1 = datasetT1.ReadAsArray(x - pad_width, y - pad_width, blocksize + 2 * pad_width,
                                                            blocksize + 2 * pad_width) 
                            dataT2 = datasetT2.ReadAsArray(
                                x_T2, y_T2, c_T2, r_T2) 

                    else:

                        geoT1_X = imagexy2geo(datasetT1, y, x)[0]
                        geoT1_Y = imagexy2geo(datasetT1, y, x)[1]
                    
                        x_T2, y_T2 = geo2imagexy(
                            datasetT2, geoT1_X, geoT1_Y)

                        geoT2_X = imagexy2geo(
                            datasetT1, y + rows, x + cols)[0]
                        geoT2_Y = imagexy2geo(
                            datasetT1, y + rows, x + cols)[1]
                       
                        cols_T2, rows_T2 = geo2imagexy(
                            datasetT2, geoT2_X, geoT2_Y)

                        c_T2 = cols_T2 - x_T2
                        r_T2 = rows_T2 - y_T2

                        dataT1 = datasetT1.ReadAsArray(
                            x, y, cols, rows)  
                        dataT2 = datasetT2.ReadAsArray(
                            x_T2, y_T2, c_T2, r_T2)  

            
                    dataT1 = dataT1.transpose(1, 2, 0)  # row, col, band
                    dataT2 = dataT2.transpose(1, 2, 0)

                except Exception as e:
                    print(str(e))
                    continue

                try:
                    if isBackGround(dataT1) | isBackGround(dataT2):  
                        print("Total: " + str(int(numBlock)) + " blocks, the " +
                                str(num + 1) + " block only have background pixels")
                    else:
                        bandcomImg = compositeImg(dataT1, dataT2)  


                        bandcomImg = bandcomImg.transpose(2, 0, 1)

                        c, row, col = bandcomImg.shape

                        if (row == blocksize + 2 * pad_width) & (
                                col == blocksize + 2 * pad_width):

                            imgy = model_predict(resnet_session, bandcomImg, blocksize, pad_width, nodata_T1, nodata_T2, area, pro, isUseVote)

                            row, col = imgy.shape
                            saveImg = imgy[pad_width:row -
                                            pad_width, pad_width:col - pad_width]


                            dst_ds.GetRasterBand(
                                1).WriteArray(saveImg, x - colT1_ul, y - rowT1_ul)  


                        else:
                            newdata = np.zeros(
                                (inputChannel, blocksize, blocksize))  
                            newdata[:, :rows, :cols] = bandcomImg

                            imgy = model_predict(resnet_session, newdata, blocksize, pad_width, nodata_T1, nodata_T2, area, pro, isUseVote)

                            dst_ds.GetRasterBand(1).WriteArray(
                                imgy[:rows, :cols], x - colT1_ul, y - rowT1_ul)  


                    num = num + 1
                except Exception as e:
                    print(str(e))
                    continue
                
                pbar.update(1)

    datasetT1 = None
    datasetT2 = None


def resultOptimize(resultPath, saveSHPpath, areaopen=200):
    """
    holl fill 
    """
    img = SieveFilterTheRaster(
        resultPath, area=areaopen)  # small object remove
    if img == 0:
        print("small object remove...")
    else:
        print("some errors...")

    RasterToPoly(resultPath, saveSHPpath)  # raster to polygon  

    
def onnx_main(inputChannel, pro, onnx_modelPath, blocksize, T1_Path, T2_Path, saveRasterpath,
              isCheckProject, saveReProjectPath, isSaveVector, saveSHPpath,
              area,isUseVote, isHollFill, GPUid):
    """
    change detection main function
    """
    
    reProjectImgPath_t2 = saveReProjectPath
    if isCheckProject == 1:
        print("check Projection...")
        T2_Path = checkProject(
            T1_Path, T2_Path, reProjectImgPath_t2)
    else:
        print("check projection sucess...")
    
    print("change detection undergoing....")
    getUnionRaster(inputChannel, onnx_modelPath, T1_Path, T2_Path, saveRasterpath,
                blocksize, area, isUseVote, pro, pad_width=128)
    print("change detection raster dataset generate sucess....")
    
    if isSaveVector != 0:
        print("Raster to polygon...")
        resultOptimize(saveRasterpath, saveSHPpath, areaopen=200)
        print("change detection success...")
    elif (isSaveVector == 0) and (isHollFill != 0):
        print("Holl fill...")
        
        SieveFilterTheRaster(saveRasterpath, area=200)
        print("change detection success...")
    else:
        print("change detection success...")
        
    if T2_Path == reProjectImgPath_t2:  
        os.remove(reProjectImgPath_t2)
