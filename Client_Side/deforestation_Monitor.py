# coding:utf-8
import os
import streamlit as st

from pathlib import Path
import leafmap.foliumap as leafmap
# import leafmap.leafmap as leafmap
from osgeo import gdal
from Tool.compressResult import compress_attaches
from pathlib import Path
import requests
import json

import time 
import datetime


st.set_page_config(layout="wide")  # wide layer


def getXYcenter(rasterPath):
    """
    get center of input raster
    """
    dataset = gdal.Open(rasterPath)

    width = dataset.RasterXSize
    height = dataset.RasterYSize

    transform = dataset.GetGeoTransform()

    center_x = transform[0] + (width * transform[1] + height * transform[2]) / 2
    center_y = transform[3] + (width * transform[4] + height * transform[5]) / 2
    
    return center_x, center_y
    


def app():
    layerHeight = 500   # UI height of a layer
     
    currentFolder = os.path.abspath(os.curdir)
    savePathfile = "tempFile"
    
    savePath_File = os.path.join(currentFolder, savePathfile)
    
    if not os.path.exists(savePath_File):
        os.makedirs(savePath_File)  
        
    col1, col2, col3 = st.columns(3)  
        
    # Function choose
    st.sidebar.title("Change detection System with AI")
    object_type = st.sidebar.selectbox("please select what you are interested in",
        ["Forest"])
    
    # img type selection
    st.sidebar.title("Image type")
    img_type = st.sidebar.selectbox("please select an image type to detect deforestation",
        ["High_resolution", "Landsat", "Sentinel2A/2B"])
    
    uploaded_file_T1 = st.sidebar.file_uploader("please upload the former time-phase RS image", type=["tif", "tiff", "png", "jpeg", "img"])
    uploaded_file_T2 = st.sidebar.file_uploader("please upload the latter time-phase RS image", type=["tif", "tiff", "png", "jpeg", "img"])
    
    
    if uploaded_file_T1 is not None:
        
        
        T1_image_path = os.path.join(savePath_File, uploaded_file_T1.name)
        fp = Path(T1_image_path)
        fp.write_bytes(uploaded_file_T1.getvalue())  # save as image file
        
        center_x, center_y = getXYcenter(T1_image_path)
        
        m = leafmap.Map(center=(center_x, center_y), zoom = 8)
        
            
        with col1:
            m.add_local_tile(T1_image_path, layer_name = "T1_image_layer")
            
            

            m.to_streamlit(height=layerHeight, minimap_control=True)
        
    if uploaded_file_T2 is not None:
        
        T2_image_path = os.path.join(savePath_File, uploaded_file_T2.name)
        fp = Path(T2_image_path)
        fp.write_bytes(uploaded_file_T2.getvalue())  
        
        center_x, center_y = getXYcenter(T2_image_path)
        
        m2 = leafmap.Map(center=(center_x, center_y), zoom = 8)
        
        with col2:
            m2.add_local_tile(T2_image_path, layer_name = "T2_image_layer")

            m2.to_streamlit(height=layerHeight, minimap_control=True)
        

    
    # Browser-side: Parameter setting
    st.sidebar.markdown("## Please set the probability threshold to detect changes")
    confidence_threshold = st.sidebar.slider("probability", 0.0, 1.0, 0.5, 0.01)
    
    st.sidebar.markdown("## Please set the blocksize to detect changes")
    block_size = st.sidebar.slider("blocksize", 512, 4096, 2048, 512)
    
    
    # model selection
    st.sidebar.title("Model select")
    model_type = st.sidebar.selectbox("please select a model to detect deforestation",
        ["SiamHRnet-OCR", "Unet++", "SNUnet", "DeepLabV3+", "SegFormer", "SegNext","Unet"])

    
    # server-side: online deforestation detection
    if st.sidebar.button("online detection"):
        
        # m3 = leafmap.Map()

        print("begin...")
        
        imgName         = os.path.splitext(T1_image_path)[0]               
        
        saveimgPath     = imgName+"_Deforestaion_Monitor_result.tif" 
        saveshpPath     = imgName+"_Deforestaion_Monitor_result.shp" 
        
        pro             = confidence_threshold
        isUseVote       = 0                                                
         
        if (object_type == "Forest") and (img_type == "High_resolution"):  # forest monitor using high-resolution images
            
            if model_type == "SiamHRnet-OCR":
                onnx_model_Path = "RS_change_detection_model/SiamHRnet-OCR.onnx"
            elif model_type == "Unet" :
                onnx_model_Path = "RS_change_detection_model/Unet.onnx"
            elif model_type == "Unet++" :
                onnx_model_Path = "RS_change_detection_model/Unet++.onnx"
            elif model_type == "SNUnet" :
                onnx_model_Path = "RS_change_detection_model/SNUnet.onnx"
            elif model_type == "DeepLabV3+" :
                onnx_model_Path = "RS_change_detection_model/DeepLabV3+.onnx"
            elif model_type == "SegFormer" : 
                onnx_model_Path = "RS_change_detection_model/SegFormer.onnx"
            elif model_type == "SegNext" :
                onnx_model_Path = "RS_change_detection_model/SegNext.onnx"
            else:
                onnx_model_Path = "RS_change_detection_model/SiamHRnet-OCR.onnx"
        
        elif (object_type == "Forest") and (img_type == "Landsat"):        # forest monitor using Landsat images
            print("Deforestation detection on Landsat image...")
            onnx_model_Path = "RS_change_detection_model/SiamHRnet-OCR_Landsat.onnx"
            
        elif (object_type == "Forest") and (img_type == "Sentinel2A/2B"):  # forest monitor using Sentinel2A/B images
            print("Deforestation detection on Sentinel2A/B image...")
            onnx_model_Path = "RS_change_detection_model/SiamHRnet-OCR_Sentinel2AB.onnx"
            
        else:
            st.markdown("- please select an image type and deep learning model to run deforestation detection...")
                
            
        T1 = time.time()
        
        currentTime = datetime.datetime.now()
        taskID = int(currentTime.strftime("%Y%m%d%H%M%S"))
        
        url = "http://127.0.0.1:5000/openForestMonitor/task/"
        
        
        if (object_type == "Forest") and (img_type == "High_resolution"):
            postData = {'inputChannel': str(6),
                    'pro': str(pro),
                    'blockSize': str(block_size),
                    'onnx_modelPath': str(onnx_model_Path),
                    'T1_Path': str(T1_image_path),
                    'T2_Path': str(T2_image_path),
                    'saveRasterpath': str(saveimgPath),
                    'saveSHPpath': str(saveshpPath),
                    'isCheckProject': str(1),
                    'saveReProjectPath': "D://imgT2_reProject.tif",
                    'isSaveVector': str(1),
                    'area': str(200),
                    'isUseVote': str(0),
                    'isHollFill': str(0),
                    'GPUid': str(0),
                    'taskID': str(taskID),
                   }
            

            json_data = json.dumps(postData)
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, data=json_data, headers=headers)
            
        elif (object_type == "Forest") and (img_type == "Landsat"):
            postData = {'inputChannel': str(12),
                    'pro': str(pro),
                    'blockSize': str(block_size),
                    'onnx_modelPath': str(onnx_model_Path),
                    'T1_Path': str(T1_image_path),
                    'T2_Path': str(T2_image_path),
                    'saveRasterpath': str(saveimgPath),
                    'saveSHPpath': str(saveshpPath),
                    'isCheckProject': str(1),
                    'saveReProjectPath': "D://imgT2_reProject.tif",
                    'isSaveVector': str(1),
                    'area': str(200),
                    'isUseVote': str(0),
                    'isHollFill': str(0),
                    'GPUid': str(0),
                    'taskID': str(taskID),
                   }
            
            json_data = json.dumps(postData).encode('utf-8')
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, data=json_data, headers=headers)
            
        elif (object_type == "Forest") and (img_type == "Sentinel2A/2B"):
            postData = {'inputChannel': str(14),
                    'pro': str(pro),
                    'blockSize': str(block_size),
                    'onnx_modelPath': str(onnx_model_Path),
                    'T1_Path': str(T1_image_path),
                    'T2_Path': str(T2_image_path),
                    'saveRasterpath': str(saveimgPath),
                    'saveSHPpath': str(saveshpPath),
                    'isCheckProject': str(1),
                    'saveReProjectPath': "D://imgT2_reProject.tif",
                    'isSaveVector': str(1),
                    'area': str(200),
                    'isUseVote': str(0),
                    'isHollFill': str(0),
                    'GPUid': str(0),
                    'taskID': str(taskID),
                   }
            
            json_data = json.dumps(postData)
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, data=json_data, headers=headers)
            
        response = response.json()
        
        if response['code'] == 200:
            print("task running success...")
        elif response['code'] == 1001:
            print("catch errors on the server side")
            
               
        T2 = time.time()
        
        st.markdown("- Computing time: "+str(T2-T1)+"s")
        
        st.markdown("- finished...")
        
        with col3:
            center_x, center_y = getXYcenter(saveimgPath)
        
            m3 = leafmap.Map(center=(center_x, center_y), zoom = 8)
        
            m3.add_local_tile(saveimgPath, layer_name = "Deforestation map")  # 加载栅格
            # m3.add_shp(saveshpPath, layer_name = "Deforestation map")

            m3.to_streamlit(height=layerHeight, minimap_control=True)
        
        
        try:
            # server-side: image compressed
            save_prj_Path     = imgName+"_Deforestaion_Monitor_result.prj" 
            save_dbf_Path     = imgName+"_Deforestaion_Monitor_result.dbf" 
            save_shx_Path     = imgName+"_Deforestaion_Monitor_result.shx"
            out_name          = imgName+"_Deforestaion_Monitor_result.zip"
            
            files = [saveshpPath, save_prj_Path, save_dbf_Path, save_shx_Path, saveimgPath] 
            
            compress_attaches(files, out_name)
            
            zipName = Path(out_name).stem
            
            
            # browser-side: dowload result
            print("download result...")
            with open(out_name, "rb") as file:
                    btn = st.download_button(
                            label="download your result",
                            data=file,
                            file_name=zipName+'.zip',
                            mime="ZIP/zip"
                        )
                    
                    if btn:
                        st.balloons()
        except:
            
            saveImgName = Path(saveimgPath).stem
            
            # browser-side: dowload result
            print("download result...")
            with open(saveimgPath, "rb") as file:
                    btn = st.download_button(
                            label="download your result",
                            data=file,
                            file_name=saveImgName+'.tif',
                            mime="image/tif"
                        )
                    
                    if btn:
                        st.balloons()
            
                    
        print("success...")
    
        
app()
