# coding:utf-8
import os
import streamlit as st
# from Tool.torch_ONNX_changeDetection import onnx_main as AI_monitor
from AItool.AItool import onnx_main as AI_monitor
from pathlib import Path
import leafmap.foliumap as leafmap

from Tool.compressResult import compress_attaches
from pathlib import Path

import time 


st.set_page_config(layout="wide")  # wide layer


def app():
     
    savePath_File = "tempFile"
    if not os.path.exists(savePath_File):
        os.makedirs(savePath_File)  
        
    col1, col2, col3 = st.columns(3)  
        
    # Function choose
    st.sidebar.title("Change detection System with AI")
    object_type = st.sidebar.selectbox("please select what you are interested in",
        ["Forest"])
    
    uploaded_file_T1 = st.sidebar.file_uploader("please upload the former time-phase RS image", type=["tif", "tiff", "png", "jpeg"])
    uploaded_file_T2 = st.sidebar.file_uploader("please upload the latter time-phase RS image", type=["tif", "tiff", "png", "jpeg"])
    
    
    if uploaded_file_T1 is not None:
        m = leafmap.Map()
        
        T1_image_path = os.path.join(savePath_File, uploaded_file_T1.name)
        fp = Path(T1_image_path)
        fp.write_bytes(uploaded_file_T1.getvalue())  # save as image file
        
            
        with col1:
            m.add_local_tile(T1_image_path, layer_name = "T1_image_layer")

            m.to_streamlit(height=1000, minimap_control=True)
        
    if uploaded_file_T2 is not None:
        m2 = leafmap.Map()
        
        T2_image_path = os.path.join(savePath_File, uploaded_file_T2.name)
        fp = Path(T2_image_path)
        fp.write_bytes(uploaded_file_T2.getvalue())  
        
        with col2:
            m2.add_local_tile(T2_image_path, layer_name = "T2_image_layer")

            m2.to_streamlit(height=1000, minimap_control=True)
        

    
    # Browser-side: Parameter setting
    st.sidebar.markdown("## Please set the probability threshold to detect changes")
    confidence_threshold = st.sidebar.slider("probability", 0.0, 1.0, 0.5, 0.01)
    
    st.sidebar.markdown("## Please set the blocksize to detect changes")
    block_size = st.sidebar.slider("blocksize", 512, 4096, 2048, 512)

    
    # server-side: online deforestation detection
    if st.sidebar.button("online extraction"):
        
        m3 = leafmap.Map()

        print("begin...")
        
        imgName         = os.path.splitext(T1_image_path)[0]   # get image file name
        
        saveimgPath     = imgName+"_Deforestaion_Monitor_result.tif" 
        saveshpPath     = imgName+"_Deforestaion_Monitor_result.shp" 
        
        pro             = confidence_threshold
        isUseVote       = 0                                    # use vote or not
         
        if object_type == "Forest":  # forest monitor
            onnx_model_Path = "RS_change_detection_model/Forest_CD_model.onnx"
            
            T1 = time.time()
            AI_monitor(inputChannel=6, pro=pro, onnx_modelPath=onnx_model_Path, blocksize=block_size, T1_Path=T1_image_path,
                                  T2_Path=T2_image_path, saveRasterpath=saveimgPath, isCheckProject=1, saveReProjectPath="D://imgT2_reProject.tif",
                                  isSaveVector=1, saveSHPpath=saveshpPath, area=20, isUseVote=isUseVote, isHollFill=0, GPUid=0)        
            T2 = time.time()
            st.markdown("- Computing time: "+str(T2-T1)+"s")
        
        st.markdown("- finished...")
        
        with col3:
            m3.add_local_tile(saveimgPath, layer_name = "detection layer")

            m3.to_streamlit(height=1000, minimap_control=True)
        
        
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