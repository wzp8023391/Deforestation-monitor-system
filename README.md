## OpenForestMonitor: An Advanced Open-source Deforestation Monitoring System


### 1. Demo
A web-based deforestation system can be linked here: http://183.66.154.42:8501 (the maximum  upload image size is 4GB.)
Attention: if you are in China, you need to install a VPN tool to access this website! 

#### 1.1 Package Installation
- Environment: Python3.8
- In order to run the OpenForestMonitor system, you should install these third-party packages:
```python
pygis
geemap
streamlit
gdal
onnxruntime
opencv-python
numpy
tqdm
zipfile
multiprocessing
scikit-image
AItool
```
- if you have Nvidia GPUs, you can install onnxruntime-gpu to accelerate computing
- If you want to install the AItool package fails, you can download the source code from PyPi in .gz or .tar format(see https://test.pypi.org/project/AItool/).
  
#### 1.2 Deep learning model download
The deforestation model is over 150MB, you can download it from https://drive.google.com/drive/folders/1etsHlRJgT712Oq2HyQ321cFrd_ZkjacU?usp=share_link
or from BaiduDisk：https://pan.baidu.com/s/1hrYSyF81WdeVxo4_7SM86A?pwd=0k6k 
passkey：0k6k 

### 2. Performance
For a 91976×74237 pixels image, our server computer with AMD 3900x and 32 GB memory can be finished in half an hour.

### 3. run
you can run OpenForestMonitor on your server, just use one command line:
```python 
streamlit run deforestation_Monitor.py  --server.maxUploadSize 4000
```

### 4. Citation
@ article{wang2022OpenForestMonitor,
  title={OpenForestMonitor: An Advanced Open-source Deforestation Monitoring System},
  author={Zhipan Wang},
  journal={2023},
  year={2022}
}


### environment
This system was developed on windows 10, python3.8.3.
