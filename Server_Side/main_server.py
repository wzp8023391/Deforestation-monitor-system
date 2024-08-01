# coding:utf-8
# The server side of OpenForestMonitor system, Author:Mr zhipan wang, Email:1044625113@qq.com
import logging
# from Tool.AItool_fast import onnx_main
from AItool_fast import onnx_main


from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()  

app = Flask(__name__)
cors = CORS(app, supports_credentials=True)
app.debug = True


@app.route('/openForestMonitor/task/', methods=['post'])
def objectExtraction():
    """
    deforestation detection on server side
    """
    try:
        print("post success...")
        
        Parameter = request.data.decode('utf-8')
        Parameter_json = json.loads(Parameter)
        
        inputChannel = int(Parameter_json['inputChannel'])
        pro = float(Parameter_json['pro'])
        blockSize = int(Parameter_json['blockSize'])
        onnx_modelPath = str(Parameter_json['onnx_modelPath'])
        
        T1_Path = str(Parameter_json['T1_Path'])
        T2_Path = str(Parameter_json['T2_Path'])
        
        saveRasterpath = str(Parameter_json['saveRasterpath'])
        saveSHPpath = str(Parameter_json['saveSHPpath'])
        
        isCheckProject = int(Parameter_json['isCheckProject'])
        saveReProjectPath=str(Parameter_json['saveReProjectPath'])
        isSaveVector = int(Parameter_json['isSaveVector'])
        
        area = int(Parameter_json['area'])
        isUseVote = int(Parameter_json['isUseVote'])
        isHollFill = int(Parameter_json['isHollFill'])
        GPUid = int(Parameter_json['GPUid'])
        
        
        taskID = int(Parameter_json['taskID'])   
        
        logging.info("get inputChannel: " + str(inputChannel))
        logging.info("get pro: " + str(pro))
        logging.info("get blockSize: " + str(blockSize))
        logging.info("get onnx_modelPath: " + str(onnx_modelPath))
        logging.info("get T1_Path: " + str(T1_Path))
        logging.info("get T2_Path: " + str(T2_Path))
        
        logging.info("get saveRasterpath: " + str(saveRasterpath))
        logging.info("get saveSHPpath: " + str(saveSHPpath))
        logging.info("get isCheckProject: " + str(isCheckProject))
        logging.info("get saveReProjectPath: " + str(saveReProjectPath))
        logging.info("get isSaveVector: " + str(isSaveVector))
        logging.info("get area: " + str(area))
        logging.info("get isUseVote: " + str(isUseVote))
        logging.info("get isHollFill: " + str(isHollFill))
        logging.info("get GPUid: " + str(GPUid))
        logging.info("get taskID: " + str(taskID))
        
        onnx_main(inputChannel, pro, onnx_modelPath, blockSize, T1_Path, T2_Path, saveRasterpath,
              isCheckProject, saveReProjectPath, isSaveVector, saveSHPpath,
              area, isUseVote, isHollFill, GPUid)
            
        
        success_sf = jsonify({
                "code": 200,
                "msg": "request sucess"
            })
            
        logging.info("task running success..." )
        return success_sf
            
    
    except Exception as e:
        print(e)
        logging.error("errors: " + str(e))
        
        fail_sf = jsonify({
            "code": 1001,
            "msg": "errors"
        })
        
        return fail_sf
    

 
if __name__ == '__main__':
    
    from waitress import serve
    
    # logging 
    logging.basicConfig(filename='OpenForestMonitor.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Server run success, Author: Mr Wang, Email:1044625113@qq.com....")
    
    serve(app, host='127.0.0.1', port=5000)